"""
В этом модуле находятся фильтры к альянсам
"""
from telegram.ext import BaseFilter

from castle_files.work_materials.globals import dispatcher

from castle_files.work_materials.filters.general_filters import filter_is_chat_wars_forward, filter_is_pm

import re


class FilterAllianceLocation(BaseFilter):
    def filter(self, message):
        return re.match("You found hidden (location|headquarter)", message.text) is not None \
               and filter_is_chat_wars_forward(message)


filter_alliance_location = FilterAllianceLocation()


class FilterAllianceInfo(BaseFilter):
    def filter(self, message):
        return all(i in message.text for i in frozenset(["Guilds:", "Owner:", "State:", "Balance:"])) and \
               message.text.startswith("🤝") and filter_is_chat_wars_forward(message) and filter_is_pm(message)


filter_alliance_info = FilterAllianceInfo()


class FilterAllianceRoster(BaseFilter):
    def filter(self, message):
        return message.text.startswith("📋Roster:") and filter_is_chat_wars_forward(message) and filter_is_pm(message)


filter_alliance_roster = FilterAllianceRoster()


class FilterViewAlliance(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return (message.text.startswith("🤝Альянс") or message.text.startswith("🤝Alliance")) and \
            user_data.get("status") == "barracks" and filter_is_pm(message)


filter_view_alliance = FilterViewAlliance()


class FilterAlliancePin(BaseFilter):
    def filter(self, message):
        return re.search('/ga_((atk|def)_\\w+|def)', message.text) is not None


filter_alliance_pin = FilterAlliancePin()

