from telegram.ext import BaseFilter
from castle_files.work_materials.globals import castles, CHAT_WARS_ID


class FilterGuildList(BaseFilter):
    def filter(self, message):
        try:
            first_line = message.text.splitlines()[1]
        except Exception:
            return False
        return message.text[0] in castles and message.forward_from and message.forward_from.id == CHAT_WARS_ID and \
            first_line.find("#1") == 0 and "[" in first_line


filter_guild_list = FilterGuildList()
