from telegram import Bot
from telegram.utils.request import Request
from telegram.error import (Unauthorized, BadRequest,
                            TimedOut, NetworkError)
from aiogram import Bot as ABot
import multiprocessing
import threading
import time
import logging
import traceback
import random
import asyncio
import json

from order_files.libs.order import Order, OrderBackup

MESSAGE_PER_SECOND_LIMIT = 25
MESSAGE_PER_CHAT_LIMIT = 3

UNAUTHORIZED_ERROR_CODE = 2
BADREQUEST_ERROR_CODE = 3

advanced_callback = multiprocessing.Queue()


order_backup_queue = multiprocessing.Queue()

logging.basicConfig(level=logging.INFO)


class AsyncBot(Bot):

    def __init__(self, token, order_token, workers=8, request_kwargs=None):
        self.__rlock = threading.RLock()
        self.counter_lock = threading.Condition(self.__rlock)
        # self.order_queue = multiprocessing.Queue()
        self.order_queue = asyncio.Queue()
        self.processing = True
        self.num_workers = workers
        self.messages_per_second = 0
        self.workers = []
        self.__order_token = order_token
        self.request_kwargs = request_kwargs
        if request_kwargs is None:
            request_kwargs = {}
        con_pool_size = 8
        if 'con_pool_size' not in request_kwargs:
            request_kwargs['con_pool_size'] = con_pool_size
        self._request = Request(**request_kwargs)
        self.con_pool_size = workers * 2
        request_kwargs['con_pool_size'] = con_pool_size
        self._order_request = Request(**request_kwargs)
        super(AsyncBot, self).__init__(token=token, request=self._request)
        # self.start()


    """def send_message(self, *args, **kwargs):
        message = MessageInQueue(*args, **kwargs)
        self.message_queue.put(message)
        return 0"""

    def sync_send_message(self, *args, **kwargs):
        return super(AsyncBot, self).send_message(*args, **kwargs)

    def send_message(self, *args, **kwargs):
        # return self.actually_send_message(*args, **kwargs)
        return self.sync_send_message(*args, **kwargs)

    async def actually_send_message(self, *args, **kwargs):
        chat_id = kwargs.get('chat_id')
        lock = self.counter_lock
        wait_start = time.time()
        try:
            lock.acquire()
            while True:
                if self.messages_per_second < MESSAGE_PER_SECOND_LIMIT:
                    self.messages_per_second += 1
                    lock.release()
                    # time.sleep(random.random()*0.01)
                    break
                # logging.info("sleeping")
                lock.wait()
                # logging.info("woke up")
        finally:
            pass
        wait_end = time.time()
        advanced_callback.put({"chat_id": kwargs.get("chat_id"), "wait_start": wait_start, "wait_end": wait_end})
        message = None
        release = threading.Timer(interval=1, function=self.__releasing_resourse, args=[chat_id])
        release.start()
        try:
            print("sending")
            message = await self.order_bot.send_message(*args, **kwargs)
        except Unauthorized:
            return UNAUTHORIZED_ERROR_CODE
        except BadRequest:
            logging.error(traceback.format_exc())
            return BADREQUEST_ERROR_CODE
        except TimedOut:
            time.sleep(0.1)
            message = self.order_bot.send_message(*args, **kwargs)
        except NetworkError:
            time.sleep(0.1)
            message = self.order_bot.send_message(*args, **kwargs)
        except Exception:
            logging.error(traceback.format_exc())
        return message

    def send_order(self, order_id, chat_id, response, pin_enabled, notification, reply_markup=None):
        order = Order(order_id=order_id, text=response, chat_id=chat_id, pin=pin_enabled, notification=notification,
                      reply_markup=reply_markup)
        # asyncio.create_task(self.__send_order(order))
        self.order_queue.put_nowait(order)

    def start_workers(self):
        """
        works = []
        for i in range(0, self.num_workers):
            works.append(self.__work(i))
        """
        request_kwargs = self.request_kwargs
        order_token = self.__order_token
        con_pool_size = self.con_pool_size
        proxy_url = request_kwargs.get("proxy_url") if request_kwargs is not None else None
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_debug(True)
        self.loop = loop
        self.order_bot = ABot(order_token, connections_limit=con_pool_size, proxy=proxy_url, loop=loop)

        asyncio.run_coroutine_threadsafe(self.async_work(), loop=loop)
        loop.run_until_complete(self.async_work())
        # asyncio.gather(*works)

    async def async_work(self):
        print("started work")
        order_in_queue = await self.order_queue.get()
        while self.processing and order_in_queue:
            # await self.__send_order(order_in_queue)
            asyncio.create_task(self.__send_order(order_in_queue))
            print("created task")
            order_in_queue = await self.order_queue.get()
        return 0

    def start(self):
        threading.Thread(target=self.start_workers).start()

        """
        worker = threading.Thread(target=self.__work, args=(i,))
        worker.start()
        self.workers.append(worker)
        """
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
        # self.order_queue.close()
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
            self.counter_lock.notify(1)

    async def __send_order(self, order_in_queue):
        print("work started")
        response = ""
        pin = order_in_queue.pin
        notification = order_in_queue.notification
        chat_id = order_in_queue.chat_id
        text = order_in_queue.text
        reply_markup = order_in_queue.reply_markup.to_dict()
        print(reply_markup)
        reply_markup = json.dumps(reply_markup)
        # logging.info("worker {}, starting to send".format(num))
        begin = time.time()
        message = await self.actually_send_message(chat_id=chat_id, text=text, parse_mode='HTML',
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
                    await self.order_bot.pin_chat_message(chat_id=chat_id, message_id=message.message_id,
                                                          disable_notification=not notification)
                except Unauthorized:
                    response += "Недостаточно прав для закрепления сообщения в чате {0}\n".format(chat_id)
                    pass
                except BadRequest:
                    response += "Недостаточно прав для закрепления сообщения в чате {0}\n".format(chat_id)
                    pass
                except Exception:
                    logging.error(traceback.format_exc())
        pin_end = time.time()
        advanced_callback.put({"chat_id": chat_id, "begin": begin, "sent": sent, "pin_end": pin_end})
        OK = response == ""
        order_backup = OrderBackup(order_id=order_in_queue.order_id, OK=OK, text=response)
        order_backup_queue.put(order_backup)
        return 0


    async def __work(self, num):
        print("work started")
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
            message = await self.actually_send_message(chat_id=chat_id, text=text, parse_mode='HTML',
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
                        await self.order_bot.pin_chat_message(chat_id=chat_id, message_id=message.message_id,
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
