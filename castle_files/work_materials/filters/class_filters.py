"""
Здесь находятся фильтры для классовых функций
"""

from telegram.ext import BaseFilter
from castle_files.work_materials.filters.general_filters import filter_is_pm, filter_is_chat_wars_forward


class FilterArcherTrap(BaseFilter):
    def filter(self, message):
        return filter_is_chat_wars_forward(message) and filter_is_pm(message) and \
               'попал в твою ловушку.' in message.text.lower()


filter_archer_trap = FilterArcherTrap()
