from telegram.ext import BaseFilter
from order_files.work_materials.globals import admin_ids, allowed_chats


class FilterIsAdmin(BaseFilter):
    def filter(self, message):
        return message.from_user.id in admin_ids

filter_is_admin = FilterIsAdmin()


class FilterInAllowedChat(BaseFilter):
    def filter(self, message):
        return message.chat_id in allowed_chats

filter_chat_allowed = FilterInAllowedChat()


class FilterSuperAdmin(BaseFilter):
    def filter(self, message):
        return message.from_user.id == admin_ids[0]

filter_super_admin = FilterSuperAdmin()
