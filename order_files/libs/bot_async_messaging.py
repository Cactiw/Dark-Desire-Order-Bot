from aiogram import Bot, Dispatcher
from aiogram.utils.exceptions import NotEnoughRightsToPinMessage, BadRequest, Unauthorized, TelegramAPIError, \
    NetworkError, TimeoutWarning, ChatNotFound, ChatIdIsEmpty
import multiprocessing
import threading
import time
import logging
import traceback
import queue
import json

import asyncio

from order_files.libs.order import Order, OrderBackup

MESSAGE_PER_SECOND_LIMIT = 25
MESSAGE_PER_CHAT_LIMIT = 3

UNAUTHORIZED_ERROR_CODE = 2
BADREQUEST_ERROR_CODE = 3

advanced_callback = multiprocessing.Queue()


order_backup_queue = multiprocessing.Queue()


class AsyncBot(Bot):

    def __init__(self, token, workers=8, proxy=None):
        # self.__rlock = asyncio.Lock()
        self.counter_lock = None
        self.order_queue = multiprocessing.Queue()
        self.processing = True
        self.num_workers = workers
        self.messages_per_second = 0
        self.workers = []

        self.token = token
        self.proxy = proxy

        self.loop = None

        self.con_pool_size = workers + 4
        # self.dp = Dispatcher(self)
        # self.start()


    def sync_send_message(self, *args, **kwargs):
        return super(AsyncBot, self).send_message(*args, **kwargs)

    async def send_message(self, *args, **kwargs):
        return await self.actually_send_message(*args, **kwargs)

    async def actually_send_message(self, *args, **kwargs):
        chat_id = kwargs.get('chat_id')
        message = None
        try:
            print("actually sending")
            message = await super(AsyncBot, self).send_message(*args, **kwargs)
            print("sent")
        except Unauthorized:
            return UNAUTHORIZED_ERROR_CODE
        except (BadRequest, ChatNotFound, ChatIdIsEmpty):
            # logging.error(traceback.format_exc())
            return BADREQUEST_ERROR_CODE
        except TimeoutError:
            time.sleep(0.1)
            message = await super(AsyncBot, self).send_message(*args, **kwargs)
        except NetworkError:
            time.sleep(0.1)
            message = await super(AsyncBot, self).send_message(*args, **kwargs)
        except Exception:
            return BADREQUEST_ERROR_CODE
        return message

    def send_order(self, order_id, chats, response, reply_markup=None):
        order = Order(order_id=order_id, text=response, chats=chats, reply_markup=reply_markup)
        self.order_queue.put(order)

    def start(self):
        threading.Thread(target=self.__work_start).start()

    def __work_start(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.set_debug(True)
        self.counter_lock = asyncio.Condition()
        super(AsyncBot, self).__init__(token=self.token, connections_limit=self.con_pool_size, proxy=self.proxy,
                                       loop=self.loop)
        asyncio.run_coroutine_threadsafe(self.__work_loop(), loop=self.loop)
        self.loop.run_forever()
        self.loop.close()
        print("Loop closed")

    async def __work_loop(self):
        print("WORKING")
        """
        pin_enabled=chat[1], notification=not chat[2],
        """
        while self.processing:
            order = self.order_queue.get()
            if order is None:
                break
            text = order.text
            reply_markup = order.reply_markup
            order_id = order.order_id
            if reply_markup is not None:
                reply_markup = json.dumps(reply_markup.to_dict())
            tasks = []
            for chat in order.chats:
                chat_id = chat[0]
                pin_enabled = chat[1]
                notification = not chat[2]
                tasks.append(self.__send_order(chat_id, text, pin_enabled, notification, reply_markup, order_id))
            await asyncio.gather(*tasks)
        self.loop.stop()

    async def __send_order(self, chat_id, text, pin, notification, reply_markup, order_id):
        response = ""
        wait_start = time.time()
        async with self.counter_lock:
            while True:
                if self.messages_per_second < MESSAGE_PER_SECOND_LIMIT:
                    self.messages_per_second += 1
                    break
                else:
                    await self.counter_lock.wait()

        wait_end = time.time()
        advanced_callback.put({"chat_id": chat_id, "wait_start": wait_start, "wait_end": wait_end})
        self.loop.create_task(self.__releasing_resourse())
        # reply_markup = json.dumps(reply_markup) if reply_markup is not None else None
        begin = time.time()
        message = await self.actually_send_message(chat_id=chat_id, text=text, parse_mode='HTML',
                                                   reply_markup=reply_markup)
        sent = time.time()
        if message == UNAUTHORIZED_ERROR_CODE:
            response += "Недостаточно прав для отправки сообщения в чат {0}\n".format(chat_id)
            pass
        elif message == BADREQUEST_ERROR_CODE:
            response += "Невозможно отправить сообщение в чат {0}, проверьте корректность chat id\n".format(chat_id)
            pass
        else:
            if pin:
                try:
                    await super(AsyncBot, self).pin_chat_message(chat_id=chat_id, message_id=message.message_id,
                                                                 disable_notification=not notification)
                except (Unauthorized, NotEnoughRightsToPinMessage):
                    response += "Недостаточно прав для закрепления сообщения в чате {0}\n".format(chat_id)
                    pass
                except BadRequest:
                    response += "Недостаточно прав для закрепления сообщения в чате {0}\n".format(chat_id)
                    pass
                except Exception:
                    response += "Недостаточно прав для закрепления сообщения в чате {0}\n".format(chat_id)
                    logging.error(traceback.format_exc())
        pin_end = time.time()
        advanced_callback.put({"chat_id": chat_id, "begin": begin, "sent": sent, "pin_end": pin_end})
        OK = response == ""
        order_backup = OrderBackup(order_id=order_id, OK=OK, text=response)
        order_backup_queue.put(order_backup)
        return 0

    def stop(self):
        self.processing = False
        self.loop.stop()
        for i in range(0, self.num_workers):
            self.order_queue.put(None)
        for i in self.workers:
            i.join()
        time.sleep(0.1)
        self.loop.close()

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

    async def __releasing_resourse(self):
        await asyncio.sleep(1)
        async with self.counter_lock:
            self.messages_per_second -= 1
            self.counter_lock.notify(1)


class MessageInQueue:

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
