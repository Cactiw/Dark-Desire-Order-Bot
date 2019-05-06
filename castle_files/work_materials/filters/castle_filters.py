"""
В этом модуле находятся фильтры для сообщений, относящихся к виртуальному замку
"""
from telegram.ext import BaseFilter
from castle_files.work_materials.filters.general_filters import filter_is_pm
from castle_files.work_materials.globals import dispatcher, king_id, SUPER_ADMIN_ID


class FilterBack(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and message.text.startswith("↩️ Назад")


filter_back = FilterBack()


class FilterNotConstructed(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and message.text.startswith("🏚 Не построено")


filter_not_constructed = FilterNotConstructed()


# Далее идут фильтры для локаций замка
class FilterCentralSquare(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and message.text.startswith("⛲️ Центральная площадь")


filter_central_square = FilterCentralSquare()


class FilterCastleGates(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and message.text.startswith("⛩ Врата замка")


filter_castle_gates = FilterCastleGates()


class FilterGuideSigns(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text.startswith("↔️ Подойти к указателям") and \
            user_data.get("status") == 'central_square'


filter_guide_signs = FilterGuideSigns()


class FilterBarracks(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text.startswith("🎪 Казарма") and \
            user_data.get("status") == 'central_square'


filter_barracks = FilterBarracks()


class FilterThroneRoom(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text.startswith("🏛 Тронный зал") and \
            user_data.get("status") == 'central_square'


filter_throne_room = FilterThroneRoom()


class FilterWatchPortraits(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text.startswith("Смотреть на портреты") and \
            user_data.get("status") == 'throne_room'


filter_watch_portraits = FilterWatchPortraits()


class FilterKingCabinet(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text.startswith("Кабинет Короля") and \
            user_data.get("status") == 'throne_room' and message.from_user.id in [king_id, SUPER_ADMIN_ID]


filter_king_cabinet = FilterKingCabinet()


class FilterRequestChangeCastleMessage(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text.startswith("Изменить сообщение") and \
            user_data.get("status") == 'king_cabinet' and message.from_user.id in [king_id, SUPER_ADMIN_ID]


filter_request_change_castle_message = FilterRequestChangeCastleMessage()


class FilterChangeCastleMessage(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and user_data.get("status") == 'changing_castle_message' and \
            message.from_user.id in [king_id, SUPER_ADMIN_ID]


filter_change_castle_message = FilterChangeCastleMessage()


class FilterAddGeneral(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text.startswith("Добавить генерала") and \
            user_data.get("status") == 'king_cabinet' and message.from_user.id in [king_id, SUPER_ADMIN_ID]


filter_add_general = FilterAddGeneral()


class FilterAddingGeneral(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and user_data.get("status") == 'adding_general' and \
            message.from_user.id in [king_id, SUPER_ADMIN_ID]


filter_adding_general = FilterAddingGeneral()


class FilterRemoveGeneral(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text.startswith("/remove_general_") and \
            user_data.get("status") == 'king_cabinet' and message.from_user.id in [king_id, SUPER_ADMIN_ID]


filter_remove_general = FilterRemoveGeneral()
