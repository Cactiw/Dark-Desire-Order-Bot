"""
В этом модуле находятся фильтры для непосредственной работы с гильдиями
"""
from telegram.ext import BaseFilter
from castle_files.work_materials.globals import dispatcher


class FilterEditGuild(BaseFilter):
    def filter(self, message):
        return message.text.startswith("/edit_guild_")


filter_edit_guild = FilterEditGuild()


class FilterChangeGuildCommander(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        return user_data is not None and user_data.get("status") == "edit_guild_commander"


filter_change_guild_commander = FilterChangeGuildCommander()


class FilterChangeGuildChat(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        return user_data is not None and user_data.get("status") == "edit_guild_chat"


filter_change_guild_chat = FilterChangeGuildChat()
