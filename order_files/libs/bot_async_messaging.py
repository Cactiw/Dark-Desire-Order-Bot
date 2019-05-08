from telegram import Bot
from telegram.utils.request import Request
from telegram.error import (Unauthorized, BadRequest,
                            TimedOut, NetworkError)
import multiprocessing
import threading
import time
import logging
import traceback

from order_files.libs.order import Order, OrderBackup

MESSAGE_PER_SECOND_LIMIT = 28
MESSAGE_PER_CHAT_LIMIT = 3

UNAUTHORIZED_ERROR_CODE = 2
BADREQUEST_ERROR_CODE = 3


order_backup_queue = multiprocessing.Queue()


class AsyncBot(Bot):

    def __init__(self, token, workers = 4, request_kwargs = None):
        counter_rlock = threading.RLock()
        self.counter_lock = threading.Condition(counter_rlock)
        #self.message_queue = multiprocessing.Queue()
        self.order_queue = multiprocessing.Queue()
        self.processing = True
        self.num_workers = workers
        self.messages_per_second = 0
        self.messages_per_chat = {}
        self.workers = []
        if request_kwargs is None:
            request_kwargs = {}
        con_pool_size = workers + 4
        if 'con_pool_size' not in request_kwargs:
            request_kwargs['con_pool_size'] = con_pool_size
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
        lock.acquire()
        try:
            while True:
                lock.acquire()
                messages_per_current_chat = self.messages_per_chat.get(chat_id)
                if messages_per_current_chat is None:
                    messages_per_current_chat = 0
                if self.messages_per_second < MESSAGE_PER_SECOND_LIMIT and messages_per_current_chat < MESSAGE_PER_CHAT_LIMIT:
                    self.messages_per_second += 1
                    self.messages_per_chat.update({chat_id : messages_per_current_chat + 1})
                    lock.release()
                    break
                lock.release()
                lock.wait()
        finally:
            try:
                lock.release()
            except RuntimeError:
                pass
        message = None
        try:
            message = super(AsyncBot, self).send_message(*args, **kwargs)
        except Unauthorized:
            release = threading.Timer(interval=1, function=self.__releasing_resourse, args=[chat_id])
            release.start()
            return UNAUTHORIZED_ERROR_CODE
        except BadRequest:
            logging.error(traceback.format_exc())
            release = threading.Timer(interval=1, function=self.__releasing_resourse, args=[chat_id])
            release.start()
            return BADREQUEST_ERROR_CODE
        except TimedOut:
            time.sleep(0.1)
            message = super(AsyncBot, self).send_message(*args, **kwargs)
        except NetworkError:
            time.sleep(0.1)
            message = super(AsyncBot, self).send_message(*args, **kwargs)
        release = threading.Timer(interval=1, function=self.__releasing_resourse, args=[chat_id])
        release.start()
        return message

    def send_order(self, order_id, chat_id, response, pin_enabled, notification):
        order = Order(order_id=order_id, text=response, chat_id=chat_id, pin=pin_enabled, notification=notification)
        self.order_queue.put(order)

    def start(self):
        for i in range(0, self.num_workers):
            worker = threading.Thread(target = self.__work, args = ())
            worker.start()
            self.workers.append(worker)

    def stop(self):
        self.processing = False
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
            mes_per_chat = self.messages_per_chat.get(chat_id)
            if mes_per_chat is None:
                self.counter_lock.notify_all()
                return
            if mes_per_chat == 1:
                self.messages_per_chat.pop(chat_id)
                self.counter_lock.notify_all()
                return
            mes_per_chat -= 1
            self.messages_per_chat.update({chat_id : mes_per_chat})
            self.counter_lock.notify_all()

    def __work(self):
        order_in_queue = self.order_queue.get()
        while self.processing and order_in_queue:
            response = ""
            pin = order_in_queue.pin
            notification = order_in_queue.notification
            chat_id = order_in_queue.chat_id
            text = order_in_queue.text
            message = self.actually_send_message(chat_id=chat_id, text = text, parse_mode='HTML')
            if message == UNAUTHORIZED_ERROR_CODE:
                response += "Недостаточно прав для отправки сообщения в чат {0}\n".format(chat_id)
                pass
            elif message == BADREQUEST_ERROR_CODE:
                response += "Невозможно отправить сообщение в чат {0}, проверьте корректность chat id\n".format(chat_id)
                pass
            else:
                if pin:
                    try:
                        super(AsyncBot, self).pinChatMessage(chat_id=chat_id, message_id=message.message_id, disable_notification=not notification)
                    except Unauthorized:
                        response += "Недостаточно прав для закрепления сообщения в чате {0}\n".format(chat_id)
                        pass
                    except BadRequest:
                        response += "Недостаточно прав для закрепления сообщения в чате {0}\n".format(chat_id)
                        pass
            OK = response == ""
            order_backup = OrderBackup(order_id=order_in_queue.order_id, OK = OK, text = response)
            order_backup_queue.put(order_backup)
            order_in_queue = self.order_queue.get()
            if order_in_queue is None:
                return 0
        return 0


class MessageInQueue():

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs