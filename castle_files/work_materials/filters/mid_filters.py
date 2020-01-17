"""
Здесь находятся фильтры для функций в файле castle_files/bin/mid.py
"""

from telegram.ext import BaseFilter
from castle_files.work_materials.globals import MID_CHAT_ID


class FilterMailing(BaseFilter):
    def filter(self, message):
        return message.chat_id == MID_CHAT_ID and (message.text.startswith("/mailing")
                                                   or message.text.startswith("/debrief"))


filter_mailing = FilterMailing()


class FilterMailingPin(BaseFilter):
    def filter(self, message):
        return message.chat_id == MID_CHAT_ID and message.text.startswith("/mailing_pin")


filter_mailing_pin = FilterMailingPin()
