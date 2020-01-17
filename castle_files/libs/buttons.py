"""
 Здесь находятся реализации классов кнопок и всего, что с ними связано.
"""
from telegram import InlineKeyboardButton, KeyboardButton as KeyButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


class KeyboardButton(KeyButton):
    def __index__(self, text, eng_text=None, request_contact=None, request_location=None, **kwargs):
        self.eng_text = eng_text
        super(self, KeyboardButton).__init__(text, request_contact, request_location, **kwargs)


