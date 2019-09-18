

class Order:

    def __init__(self, order_id, chat_id, text, pin, notification, reply_markup=None, kwargs={}):
        self.order_id = order_id
        self.chat_id = chat_id
        self.text = text
        self.pin = pin
        self.notification = notification
        self.reply_markup = reply_markup
        self.kwargs = kwargs


class OrderBackup:

    def __init__(self, order_id, OK, text):
        self.order_id = order_id
        self.OK = OK
        self.text = text
