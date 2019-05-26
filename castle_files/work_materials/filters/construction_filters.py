"""
В этом модуле находятся фильтры для сообщений, относящихся к стройке
"""
from telegram.ext import BaseFilter
from castle_files.work_materials.filters.general_filters import filter_is_pm
from castle_files.work_materials.globals import dispatcher, king_id, SUPER_ADMIN_ID


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


class FilterKingCabinetConstruction(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text.startswith("Начать стройку") and \
            user_data.get("status") == 'king_cabinet' and message.from_user.id in [king_id, SUPER_ADMIN_ID]


filter_king_cabinet_construction = FilterKingCabinetConstruction()


class FilterBeginConstruction(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text.startswith("/begin_construction_") and \
            user_data.get("status") == 'king_cabinet' and message.from_user.id in [king_id, SUPER_ADMIN_ID]


filter_begin_construction = FilterBeginConstruction()
