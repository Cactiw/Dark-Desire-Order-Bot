"""
В этом модуле содержатся общие фильтры для замкового бота
"""

from telegram.ext import BaseFilter
from castle_files.work_materials.globals import CHAT_WARS_ID, MERC_ID, dispatcher, SUPER_ADMIN_ID
from castle_files.bin.service_functions import check_access

from telegram import Update
from functools import wraps


def update_filter(func):
    @wraps(func)
    def wrapper(self, message):
        if isinstance(message, Update):
            message = message.message
        return func(self, message)
    return wrapper


class FilterIsChatWarsForward(BaseFilter):
    def filter(self, message):
        if isinstance(message, Update):
            message = message.message
        return message.forward_from is not None and message.forward_from.id == CHAT_WARS_ID


filter_is_chat_wars_forward = FilterIsChatWarsForward()
filter_is_chat_wars_forward.update_filter = True


class FilterIsPM(BaseFilter):
    def filter(self, message):
        if isinstance(message, Update):
            message = message.message
        if message.from_user is None:
            return False
        return message.chat_id == message.from_user.id


filter_is_pm = FilterIsPM()
filter_is_pm.update_filter = True


class FilterHasAccess(BaseFilter):
    def filter(self, message):
        if isinstance(message, Update):
            message = message.message
            if message is None:
                return False
        return check_access(message.from_user.id)


filter_has_access = FilterHasAccess()
filter_has_access.update_filter = True


class FilterSuperAdmin(BaseFilter):
    def filter(self, message):
        if isinstance(message, Update):
            message = message.message
            if message is None:
                return False
        return message.from_user.id == SUPER_ADMIN_ID


filter_superadmin = FilterSuperAdmin()
filter_superadmin.update_filter = True


class FilterIsMerc(BaseFilter):
    def filter(self, message):
        if isinstance(message, Update):
            message = message.message
        return message.from_user.id == MERC_ID


filter_is_merc = FilterIsMerc()
filter_is_merc.update_filter = True


class FilterPlayerStatus(BaseFilter):
    def __init__(self, status):
        self.status = status

    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return user_data.get("status") == self.status
