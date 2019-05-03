"""
Здесь находятся фильтры для всяких callback - ивентов, например, аудиенция у короля, обращение в мид
"""
from telegram.ext import BaseFilter
from castle_files.work_materials.filters.general_filters import filter_is_pm
from castle_files.work_materials.globals import dispatcher, king_id


class FilterRequestAudience(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm and message.text.startswith("Попросить аудиенции у Короля") and \
            user_data.get("status") == 'throne_room'


filter_request_audience = FilterRequestAudience()


class FilterAcceptAudience(BaseFilter):
    def filter(self, message):
        return filter_is_pm and message.text.startswith("/accept_king_audience_") and message.from_user.id == king_id


filter_accept_audience = FilterAcceptAudience()


class FilterDeclineAudience(BaseFilter):
    def filter(self, message):
        return filter_is_pm and message.text.startswith("/decline_king_audience_") and message.from_user.id == king_id


filter_decline_audience = FilterDeclineAudience()
