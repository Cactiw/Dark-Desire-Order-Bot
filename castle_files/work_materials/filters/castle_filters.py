"""
В этом модуле находятся фильтры для сообщений, относящихся к виртуальному замку
"""
from telegram.ext import BaseFilter
from castle_files.work_materials.filters.general_filters import filter_is_pm
from castle_files.work_materials.globals import dispatcher, king_id, SUPER_ADMIN_ID, DEFAULT_CASTLE_STATUS
from castle_files.bin.service_functions import check_access


class FilterBack(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and (message.text in ["↩️ Back", "↩️ Назад"] or
                                          message.text in ["↩️ Отмена", "↩️Cancel"])


filter_back = FilterBack()


class FilterNotConstructed(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and message.text in ["🏚 Не построено", "🏚 Not yet built"]


filter_not_constructed = FilterNotConstructed()


# Далее идут фильтры для локаций замка
class FilterCentralSquare(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and message.text in ["⛲️ Центральная площадь", "⛲️Central Square"]


filter_central_square = FilterCentralSquare()


class FilterCastleGates(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and message.text in ["⛩ Врата замка", "⛩ Castle gates"]


filter_castle_gates = FilterCastleGates()


class FilterGuideSigns(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["↔️ Подойти к указателям", "↔️ View signs",
                                                          "↔️ See the signs"] and \
            user_data.get("status") == 'central_square'


filter_guide_signs = FilterGuideSigns()


class FilterBarracks(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["🎪 Казарма", "🎪 Barracks"] and \
            user_data.get("status") == 'central_square'


filter_barracks = FilterBarracks()


class FilterThroneRoom(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["🏛 Тронный зал", "🏛Throne Room"] and \
            user_data.get("status") == 'central_square'


filter_throne_room = FilterThroneRoom()


class FilterWatchPortraits(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["🎇Посмотреть на портреты", "🎇View portraits"] and \
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


class FilterHeadquarters(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text.startswith("Штаб") and \
            user_data.get("status") == 'throne_room' and check_access(message.from_user.id)


filter_headquarters = FilterHeadquarters()


class FilterRequestChangeDebrief(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["📜Выкатить дебриф"] and \
            user_data.get("status") == 'headquarters' and check_access(message.from_user.id)


filter_request_change_debrief = FilterRequestChangeDebrief()


class FilterChangeDebrief(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and user_data.get("status") == 'editing_debrief' and \
            check_access(message.from_user.id)


filter_change_debrief = FilterChangeDebrief()


class FilterRequestGuildMessageNotify(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["📣Рассылка по гильдиям", "📣Guild Newsletter"] and \
            user_data.get("status") == 'headquarters' and check_access(message.from_user.id)


filter_request_guild_message_notify = FilterRequestGuildMessageNotify()


class FilterSendGuildMessageNotify(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and user_data.get("status") == 'sending_guild_message' and \
            check_access(message.from_user.id)


filter_send_guild_message_notify = FilterSendGuildMessageNotify()


class FilterRequestChangeCastleMessage(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["Изменить сообщение", "Edit message"] and \
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
        return filter_is_pm(message) and message.text in ["Добавить генерала", "Add general"] and \
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


class FilterHallOfFame(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["🏤Мандапа Славы", "🏤Hall of Fame"] and \
            user_data.get("status") == 'central_square'


filter_hall_of_fame = FilterHallOfFame()


class FilterTops(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["📈Топы", "📈Tops"] and \
            user_data.get("status") in ['hall_of_fame', DEFAULT_CASTLE_STATUS, "rp_off"]


filter_tops = FilterTops()


class FilterTopStat(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["⚔️Атака", "🛡Защита", "🔥Опыт", "🌲Дерево", "⛰Камень",
                                                          "🏚Стройка", "⚔️Attack", "🛡Defence", "🔥Experience", "🌲Wood",
                                                          "⛰Stone", "🏚Construction"] and user_data.get("status") == 'tops'


filter_top_stat = FilterTopStat()


class FilterStatusShop(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["Магазин статусов", "Status shop"]


filter_status_shop = FilterStatusShop()


class FilterRoulette(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["Рулетка", "Roulette"] and \
            user_data.get("status") == 'tea_party'


filter_roulette = FilterRoulette()


class FilterRequestRouletteBet(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["Сделать ставку", "Place a bet"] and \
            user_data.get("status") == 'roulette'


filter_request_roulette_bet = FilterRequestRouletteBet()


class FilterPlaceRouletteBet(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and user_data.get("status") == 'awaiting_roulette_bet'


filter_place_roulette_bet = FilterPlaceRouletteBet()
