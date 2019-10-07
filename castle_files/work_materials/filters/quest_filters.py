"""
В этом модуле находятся фильтры для сообщений, относящихся к стройке
"""
from telegram.ext import BaseFilter
from castle_files.work_materials.filters.general_filters import filter_is_pm, filter_is_chat_wars_forward
from castle_files.work_materials.globals import dispatcher, king_id, SUPER_ADMIN_ID

import re


class FilterSawmill(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["🌲Лесопилка", "🌲Sawmill"] and \
            user_data.get("status") == 'castle_gates'


filter_sawmill = FilterSawmill()


class FilterQuarry(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["⛰Каменоломня", "⛰Quarry"] and \
            user_data.get("status") == 'castle_gates'


filter_quarry = FilterQuarry()


class FilterTreasury(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["💰Сокровищница", "💰Treasury"] and \
            user_data.get("status") == 'throne_room'


filter_treasury = FilterTreasury()


class FilterConstruct(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        # Внимательность при копировании, отрицание
        return filter_is_pm(message) and not (message.text in ["↩️ Назад", "↩️ Back"]) and \
            user_data.get("status") == 'construction_plate'


filter_construct = FilterConstruct()


class FilterConstructionPlate(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["🏚 Стройплощадка", "🏚 Construction Plate"] and \
            user_data.get("status") == 'central_square'


filter_construction_plate = FilterConstructionPlate()


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


class FilterTeaParty(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["🍵Чайная лига", "🍵Tea party"] and \
            user_data.get("status") == 'central_square'


filter_tea_party = FilterTeaParty()


class FilterTeaPartyQuest(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["Разведка", "Рыть котлован", "Exploration", "Dig a pit"] and \
            user_data.get("status") == 'tea_party'


filter_tea_party_quest = FilterTeaPartyQuest()


class FilterTwoGoQuest(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and \
               message.text in ["/protyanut", "/shvatit", "/sgrupirovatsya", "/podsadit", "/spinakspine", "/podelitsya",
                                "/oglyanutsya", "/ostanovispodumoi", "/chempahnet", "/smellsliketeenspirit",
                                "/ktotam", "/datpyat", ] and \
            user_data.get("status") == 'two_quest'


filter_two_go_quest = FilterTwoGoQuest()


class FilterCWQuestResult(BaseFilter):
    def filter(self, message):
        return filter_is_chat_wars_forward(message) and re.search("Получено: \\d+ опыта", message.text) is not None


filter_cw_quest_result = FilterCWQuestResult()
