from telegram.ext import BaseFilter
from order_files.work_materials.globals import allowed_chats, admin_ids
from castle_files.bin.service_functions import check_access
from castle_files.work_materials.globals import MID_CHAT_ID
from castle_files.bin.mid import fill_mid_players


class FilterIsAdmin(BaseFilter):
    def filter(self, message):
        fill_mid_players(other_process=True)
        return check_access(message.from_user.id)


filter_is_admin = FilterIsAdmin()


class FilterInAllowedChat(BaseFilter):
    def filter(self, message):
        return message.chat_id == MID_CHAT_ID


filter_chat_allowed = FilterInAllowedChat()


class FilterSuperAdmin(BaseFilter):
    def filter(self, message):
        if message.from_user is None:
            return False
        return message.from_user.id == admin_ids[0]


filter_super_admin = FilterSuperAdmin()
