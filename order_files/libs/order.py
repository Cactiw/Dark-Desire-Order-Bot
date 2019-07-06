

class Order:

    def __init__(self, order_id, chats, text, reply_markup=None):
        self.order_id = order_id
        self.chats = chats
        self.text = text
        self.reply_markup = reply_markup


class OrderBackup:

    def __init__(self, order_id, OK, text):
        self.order_id = order_id
        self.OK = OK
        self.text = text
