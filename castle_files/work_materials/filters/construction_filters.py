"""
В этом модуле находятся фильтры для сообщений, относящихся к стройке
"""
from telegram.ext import BaseFilter
from castle_files.work_materials.filters.general_filters import filter_is_pm
from castle_files.work_materials.globals import dispatcher


class FilterSawmill(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text.startswith("🌲Лесопилка") and \
            user_data.get("status") == 'castle_gates'


filter_sawmill = FilterSawmill()


class FilterQuarry(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text.startswith("⛰Каменоломня") and \
            user_data.get("status") == 'castle_gates'


filter_quarry = FilterQuarry()


class FilterTreasury(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text.startswith("💰Сокровищница") and \
            user_data.get("status") == 'throne_room'


filter_treasury = FilterTreasury()
