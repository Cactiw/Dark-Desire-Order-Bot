"""
Здесь находятся классы и методы для работы с группами сообщений - сообщения, которые должны быть отправлены
строго в определённом порядке, но асинхронно
"""
from threading import Lock, RLock
from multiprocessing import Queue
from queue import Empty


lock = Lock()
message_groups = {}
message_groups_locks = {}
groups_need_to_be_sent = Queue()


class MessageInQueue:

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class MessageGroup:

    def __init__(self, created_id):

        with lock:
            group_id_list = list(message_groups)
            if not group_id_list:
                self.id = 0
            else:
                self.id = group_id_list[-1] + 1
            message_groups.update({self.id: self})
        self.messages = []
        self.created_id = created_id
        self_lock = RLock()
        message_groups_locks.update({self.id: self_lock})
        self.busy = False

    def add_message(self, message):
        self_lock = message_groups_locks.get(self.id)
        with self_lock:
            self.messages.append(message)

    def get_message(self):
        if not self.messages:
            return 1
        message = self.messages[0]
        self.messages.pop(0)
        return message

    def send_group(self):
        self.messages.append(None)
        groups_need_to_be_sent.put(self)
        message_groups.pop(self.id)

    def is_empty(self):
        return not self.messages
