"""
В этом модуле находятся фильтры к альянсам
"""
from telegram.ext import BaseFilter

from castle_files.work_materials.filters.general_filters import filter_is_chat_wars_forward, filter_is_pm


class FilterAllianceLocation(BaseFilter):
    def filter(self, message):
        return message.text.startswith("You found hidden location") and filter_is_chat_wars_forward(message)


filter_alliance_location = FilterAllianceLocation()
