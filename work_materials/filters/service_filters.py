from telegram.ext import BaseFilter
from work_materials.globals import admin_ids, allowed_chats


class FilterIsAdmin(BaseFilter):
    def filter(self, message):
        return message.from_user.id in admin_ids

filter_is_admin = FilterIsAdmin()

class FilterInAllowedChat(BaseFilter):
    def filter(self, message):
        return message.chat_id in allowed_chats

filter_chat_allowed = FilterInAllowedChat()
