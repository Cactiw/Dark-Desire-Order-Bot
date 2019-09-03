"""
Здесь находится класс Bot с его методами для приказника (и только! - избегать копирования),
предназначен для наиболее быстрой и стабильной отправки пинов во множество чатов.
"""
from telegram import Bot
from telegram.utils.request import Request
from telegram.error import (Unauthorized, BadRequest,
                            TimedOut, NetworkError)
import multiprocessing
import threading
import time
import logging
import traceback
import datetime

from order_files.libs.order import Order, OrderBackup
from castle_files.bin.service_functions import get_time_remaining_to_battle

MESSAGE_PER_SECOND_LIMIT = 25
MESSAGE_PER_CHAT_LIMIT = 3

UNAUTHORIZED_ERROR_CODE = 2
BADREQUEST_ERROR_CODE = 3

advanced_callback = multiprocessing.Queue()


order_backup_queue = multiprocessing.Queue()


class AsyncBot(Bot):

    def __init__(self, token, workers=8, request_kwargs=None):
        self.__rlock = threading.RLock()
        self.counter_lock = threading.Condition(self.__rlock)
        self.order_queue = multiprocessing.Queue()
        self.processing = True
        self.num_workers = workers
        print(workers)
        self.messages_per_second = 0
        self.second_reset_queue = multiprocessing.Queue()
        self.workers = []
        if request_kwargs is None:
            request_kwargs = {}
        con_pool_size = workers + 4
        if 'con_pool_size' not in request_kwargs or True:
            request_kwargs.update({'con_pool_size': con_pool_size})
        self._request = Request(**request_kwargs)
        super(AsyncBot, self).__init__(token=token, request=self._request)
        # self.start()


    """def send_message(self, *args, **kwargs):
        message = MessageInQueue(*args, **kwargs)
        self.message_queue.put(message)
        return 0"""

    def sync_send_message(self, *args, **kwargs):
        return super(AsyncBot, self).send_message(*args, **kwargs)

    def send_message(self, *args, **kwargs):
        return self.actually_send_message(*args, **kwargs)

    def actually_send_message(self, *args, **kwargs):
        chat_id = kwargs.get('chat_id')
        lock = self.counter_lock
        wait_start = time.time()
        try:
            with lock:
                while True:
                    if self.messages_per_second < MESSAGE_PER_SECOND_LIMIT:
                        self.messages_per_second += 1
                        # lock.release()
                        break
                    # logging.info("sleeping")
                    lock.wait()
                    # logging.info("woke up")
        finally:
            pass
        wait_end = time.time()
        advanced_callback.put({"chat_id": kwargs.get("chat_id"), "wait_start": wait_start, "wait_end": wait_end})
        message = None
        body = {"chat_id": chat_id, "time": time.time()}
        self.second_reset_queue.put(body)
        remaining_time = get_time_remaining_to_battle()
        if remaining_time <= datetime.timedelta(seconds=30) and not kwargs.get("timeout_retry"):
            kwargs.update({"timeout": 1, "timeout_retry": True})
        try:
            message = super(AsyncBot, self).send_message(*args, **kwargs)
        except TimedOut:
            logging.error("Order timeout")
            # time.sleep(0.1)
            message = self.actually_send_message(*args, **kwargs)
        except Unauthorized:
            return UNAUTHORIZED_ERROR_CODE
        except BadRequest:
            logging.error(traceback.format_exc())
            return BADREQUEST_ERROR_CODE
        except NetworkError:
            time.sleep(0.1)
            message = super(AsyncBot, self).send_message(*args, **kwargs)
        return message

    def send_order(self, order_id, chat_id, response, pin_enabled, notification, reply_markup=None):
        order = Order(order_id=order_id, text=response, chat_id=chat_id, pin=pin_enabled, notification=notification,
                      reply_markup=reply_markup)
        self.order_queue.put(order)

    def start(self):
        threading.Thread(target=self.__release_monitor, args=[]).start()
        for i in range(0, self.num_workers):
            worker = threading.Thread(target=self.__work, args=(i,))
            worker.start()
            self.workers.append(worker)

    def stop(self):
        self.processing = False
        self.second_reset_queue.put(None)
        for i in range(0, self.num_workers):
            self.order_queue.put(None)
        for i in self.workers:
            i.join()

    def __del__(self):
        self.processing = False
        for i in range(0, self.num_workers):
            pass
            #self.order_queue.put(None)
        self.order_queue.close()
        try:
            super(AsyncBot, self).__del__()
        except AttributeError:
            pass


    """def __message_counter(self):
        while self.processing:
            with self.counter_lock:
                self.messages_per_second = 0
                self.messages_per_chat.clear()
                self.counter_lock.notify_all()
            time.sleep(1)"""

    def __releasing_resourse(self, chat_id):
        with self.counter_lock:
            self.messages_per_second -= 1
            self.counter_lock.notify_all()

    def __release_monitor(self):
        data = self.second_reset_queue.get()
        while self.processing and data is not None:
            chat_id = data.get("chat_id")
            if chat_id is None:
                chat_id = 0
            set_time = data.get("time")
            if chat_id is None or time is None:
                data = self.second_reset_queue.get()
                continue
            remaining_time = 1 - (time.time() - set_time)
            if remaining_time > 0:
                time.sleep(remaining_time)
            self.__releasing_resourse(chat_id)
            try:
                data = self.second_reset_queue.get()
            except Exception:
                return

    def __work(self, num):
        order_in_queue = self.order_queue.get()
        while self.processing and order_in_queue:
            response = ""
            pin = order_in_queue.pin
            notification = order_in_queue.notification
            chat_id = order_in_queue.chat_id
            text = order_in_queue.text
            reply_markup = order_in_queue.reply_markup
            # logging.info("worker {}, starting to send".format(num))
            begin = time.time()
            message = self.actually_send_message(chat_id=chat_id, text=text, parse_mode='HTML',
                                                 reply_markup=reply_markup)
            sent = time.time()
            # logging.info("worker {}, message sent".format(num))
            if message == UNAUTHORIZED_ERROR_CODE:
                response += "Недостаточно прав для отправки сообщения в чат {0}\n".format(chat_id)
                pass
            elif message == BADREQUEST_ERROR_CODE:
                response += "Невозможно отправить сообщение в чат {0}, проверьте корректность chat id\n".format(chat_id)
                pass
            else:
                if pin:
                    try:
                        super(AsyncBot, self).pinChatMessage(chat_id=chat_id, message_id=message.message_id,
                                                             disable_notification=not notification)
                    except Unauthorized:
                        response += "Недостаточно прав для закрепления сообщения в чате {0}\n".format(chat_id)
                        pass
                    except BadRequest:
                        response += "Недостаточно прав для закрепления сообщения в чате {0}\n".format(chat_id)
                        pass
            pin_end = time.time()
            advanced_callback.put({"chat_id": chat_id, "begin": begin, "sent": sent, "pin_end": pin_end})
            OK = response == ""
            order_backup = OrderBackup(order_id=order_in_queue.order_id, OK = OK, text = response)
            order_backup_queue.put(order_backup)
            order_in_queue = self.order_queue.get()
            if order_in_queue is None:
                return 0
        return 0


class MessageInQueue:

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
