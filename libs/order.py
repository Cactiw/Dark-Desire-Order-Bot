

class Order:

    def __init__(self, order_id, chat_id, text, pin, notification):
        self.order_id = order_id
        self.chat_id = chat_id
        self.text = text
        self.pin = pin
        self.notification = notification


class OrderBackup:

    def __init__(self, order_id, OK, text):
        self.order_id = order_id
        self.OK = OK
        self.text = text


class DeferredOrder:

    def __init__(self, deferred_id, order_id, time_set, target, defense_home, tactics, job):
        self.deferred_id = deferred_id
        self.order_id = order_id
        self.time_set = time_set
        self.target = target
        self.defense_home = defense_home
        self.tactics = tactics
        self.job = job
