"""
В этом модуле находятся фильтры для непосредственной работы с гильдиями
"""
from telegram.ext import BaseFilter
from castle_files.work_materials.globals import dispatcher

from castle_files.work_materials.filters.general_filters import filter_is_pm


class FilterEditGuild(BaseFilter):
    def filter(self, message):
        return message.text.startswith("/edit_guild_")


filter_edit_guild = FilterEditGuild()


class FilterDeleteGuild(BaseFilter):
    def filter(self, message):
        return message.text.startswith("/delete_guild_")


filter_delete_guild = FilterDeleteGuild()


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


class FilterViewGuild(BaseFilter):
    def filter(self, message):
        return message.text.startswith("Гильдия") and filter_is_pm(message)


filter_view_guild = FilterViewGuild()


class FilterRemovePlayer(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and message.text.startswith("/remove_player_")


filter_remove_player = FilterRemovePlayer()


class FilterChangeGuildDivision(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        return user_data is not None and user_data.get("status") == "edit_guild_division"


filter_change_guild_division = FilterChangeGuildDivision()
