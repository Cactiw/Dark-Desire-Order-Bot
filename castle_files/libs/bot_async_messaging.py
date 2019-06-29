from telegram import Bot
from telegram.utils.request import Request
from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)
import multiprocessing
import queue
import threading
import time
import logging
import traceback

MESSAGE_PER_SECOND_LIMIT = 29
MESSAGE_PER_CHAT_LIMIT = 3
MESSAGE_PER_CHAT_MINUTE_LIMIT = 19

UNAUTHORIZED_ERROR_CODE = 2
BADREQUEST_ERROR_CODE = 3

MAX_MESSAGE_LENGTH = 4096


class AsyncBot(Bot):

    def __init__(self, token, workers=4, request_kwargs=None):
        counter_rlock = threading.RLock()
        self.counter_lock = threading.Condition(counter_rlock)
        self.message_queue = multiprocessing.Queue()
        self.waiting_chats_message_queue = multiprocessing.Queue()
        self.processing = True
        self.num_workers = workers
        self.messages_per_second = 0
        self.messages_per_chat = {}
        self.messages_per_chat_per_minute = {}
        self.spam_chats_count = {}
        self.workers = []
        self.resending_workers = []
        if request_kwargs is None:
            request_kwargs = {}
        con_pool_size = workers + 4
        if 'con_pool_size' not in request_kwargs:
            request_kwargs['con_pool_size'] = con_pool_size
        self._request = Request(**request_kwargs)
        super(AsyncBot, self).__init__(token=token, request=self._request)

    def send_message(self, *args, **kwargs):
        message = MessageInQueue(*args, **kwargs)
        self.message_queue.put(message)
        return 0

    def sync_send_message(self, *args, **kwargs):
        return super(AsyncBot, self).send_message(*args, **kwargs)

    def actually_send_message(self, *args, **kwargs):
        chat_id = kwargs.get('chat_id')
        lock = self.counter_lock
        lock.acquire()
        try:
            while True:
                lock.acquire()
                if chat_id in self.spam_chats_count and not kwargs.get("resending"):
                    spam_was = self.spam_chats_count.get(chat_id)
                    if time.time() - spam_was > 30 * 60:
                        self.spam_chats_count.pop(chat_id)
                    else:
                        self.spam_chats_count.update({chat_id: time.time()})
                        self.waiting_chats_message_queue.put(MessageInQueue(*args, **kwargs))
                        lock.release()
                        return None
                messages_per_current_chat = self.messages_per_chat.get(chat_id)
                messages_per_current_chat_per_minute = self.messages_per_chat_per_minute.get(chat_id)
                if messages_per_current_chat is None:
                    messages_per_current_chat = 0
                if messages_per_current_chat_per_minute is None:
                    messages_per_current_chat_per_minute = 0
                if self.messages_per_second < MESSAGE_PER_SECOND_LIMIT and messages_per_current_chat < \
                        MESSAGE_PER_CHAT_LIMIT and messages_per_current_chat_per_minute < MESSAGE_PER_CHAT_MINUTE_LIMIT:
                    self.messages_per_second += 1
                    self.messages_per_chat.update({chat_id: messages_per_current_chat + 1})
                    self.messages_per_chat_per_minute.update({chat_id: messages_per_current_chat_per_minute + 1})
                    lock.release()
                    break
                else:
                    if self.messages_per_second < MESSAGE_PER_SECOND_LIMIT and not kwargs.get("resending"):
                        # Сообщения в эту секунду ещё можно отправлять
                        if messages_per_current_chat_per_minute >= MESSAGE_PER_CHAT_MINUTE_LIMIT:
                            self.spam_chats_count.update({chat_id: time.time()})
                        # Кладём в другую очередь
                        self.waiting_chats_message_queue.put(MessageInQueue(*args, **kwargs))
                        lock.release()
                        return None
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
            release = threading.Timer(interval=60, function=self.__releasing_minute_resourse, args=[chat_id])
            release.setDaemon(True)
            release.start()
            return UNAUTHORIZED_ERROR_CODE
        except BadRequest:
            logging.error(traceback.format_exc())
            release = threading.Timer(interval=1, function=self.__releasing_resourse, args=[chat_id])
            release.start()
            release = threading.Timer(interval=60, function=self.__releasing_minute_resourse, args=[chat_id])
            release.setDaemon(True)
            release.start()
            return BADREQUEST_ERROR_CODE
        except (TimedOut, NetworkError):
            release = threading.Timer(interval=1, function=self.__releasing_resourse, args=[chat_id])
            release.start()
            release = threading.Timer(interval=60, function=self.__releasing_minute_resourse, args=[chat_id])
            release.setDaemon(True)
            release.start()
            logging.error(traceback.format_exc())
            return None

            # Временно отключена повторная попытка отправить
            retry = kwargs.get('retry')
            if retry is None:
                retry = 0
            if retry == 3:
                self.send_message(*args, **kwargs)
                return
            retry += 1
            kwargs.update({"retry": retry})
            time.sleep(0.1)
            message = super(AsyncBot, self).send_message(*args, **kwargs)
        release = threading.Timer(interval=1, function=self.__releasing_resourse, args=[chat_id])
        release.start()
        release = threading.Timer(interval=60, function=self.__releasing_minute_resourse, args=[chat_id])
        release.setDaemon(True)
        release.start()
        return message

    def start(self):
        for i in range(0, self.num_workers):
            worker = threading.Thread(target=self.__work, args=())
            worker.start()
            self.workers.append(worker)
            resending_worker = threading.Thread(target=self.__resend_work, args=())
            resending_worker.start()
            self.resending_workers.append(worker)

    def stop(self):
        self.processing = False
        for i in range(0, self.num_workers):
            self.message_queue.put(None)
            self.waiting_chats_message_queue.put(None)
        for i in self.workers:
            i.join()
        for i in self.resending_workers:
            i.join()
        time.sleep(1)
        try:
            while True:
                self.message_queue.get_nowait()
        except queue.Empty:
            pass
        try:
            while True:
                self.waiting_chats_message_queue.get_nowait()
        except queue.Empty:
            pass
        self.message_queue.close()
        self.waiting_chats_message_queue.close()

    def __del__(self):
        self.processing = False
        for i in range(0, self.num_workers):
            #self.message_queue.put(None)
            pass
        self.message_queue.close()
        try:
            super(AsyncBot, self).__del__()
        except AttributeError:
            pass


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
            self.messages_per_chat.update({chat_id: mes_per_chat})
            self.counter_lock.notify_all()

    def __releasing_minute_resourse(self, chat_id):
        with self.counter_lock:
            mes_per_chat = self.messages_per_chat_per_minute.get(chat_id)
            if mes_per_chat is None:
                self.counter_lock.notify_all()
                return
            if mes_per_chat == 1:
                self.messages_per_chat_per_minute.pop(chat_id)
                self.counter_lock.notify_all()
                return
            mes_per_chat -= 1
            self.messages_per_chat_per_minute.update({chat_id: mes_per_chat})
            self.counter_lock.notify_all()

    def __work(self):
        message_in_queue = self.message_queue.get()
        while self.processing and message_in_queue is not None:
            args = message_in_queue.args
            kwargs = message_in_queue.kwargs
            self.actually_send_message(*args, **kwargs)
            message_in_queue = self.message_queue.get()
            if message_in_queue is None:
                return 0
        return 0

    def __resend_work(self):
        message_in_queue = self.waiting_chats_message_queue.get()
        while self.processing and message_in_queue is not None:
            args = message_in_queue.args
            kwargs = message_in_queue.kwargs
            kwargs.update({"resending": True})
            mes = self.actually_send_message(*args, **kwargs)
            if mes is None:
                time.sleep(0.1)
            message_in_queue = self.waiting_chats_message_queue.get()
            if message_in_queue is None:
                return 0
        return 0


class MessageInQueue:

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
