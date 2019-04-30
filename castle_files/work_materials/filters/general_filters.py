"""
В этом модуле содержатся общие фильтры для замкового бота
"""

from telegram.ext import BaseFilter
from castle_files.work_materials.globals import CHAT_WARS_ID
from castle_files.bin.service_functions import check_access


class FilterIsChatWarsForward(BaseFilter):
    def filter(self, message):
        return message.forward_from is not None and message.forward_from.id == CHAT_WARS_ID


filter_is_chat_wars_forward = FilterIsChatWarsForward()


class FilterIsPM(BaseFilter):
    def filter(self, message):
        return message.chat_id == message.from_user.id


filter_is_pm = FilterIsPM()


class FilterHasAccess(BaseFilter):
    def filter(self, message):
        return check_access(message.from_user.id)


filter_has_access = FilterHasAccess()
