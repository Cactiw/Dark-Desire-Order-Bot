

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
