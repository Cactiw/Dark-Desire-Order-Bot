"""
Здесь находятся фильтры для всяких callback - ивентов, например, аудиенция у короля, обращение в мид
"""
from telegram.ext import BaseFilter
from castle_files.work_materials.filters.general_filters import filter_is_pm
from castle_files.work_materials.globals import dispatcher, king_id, MID_CHAT_ID, CASTLE_BOT_ID, SENTINELS_DUTY_CHAT_ID


class FilterRequestAudience(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text.startswith("Попросить аудиенции у 👑Короля") and \
            user_data.get("status") == 'throne_room'


filter_request_audience = FilterRequestAudience()


class FilterAcceptAudience(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and message.text.startswith("/accept_king_audience_") and message.from_user.id == king_id


filter_accept_audience = FilterAcceptAudience()


class FilterDeclineAudience(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and message.text.startswith("/decline_king_audience_") and message.from_user.id == king_id


filter_decline_audience = FilterDeclineAudience()


class FilterRequestMidFeedback(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text.startswith("Обратиться к командному составу") and \
            user_data.get("status") == 'throne_room'


filter_request_mid_feedback = FilterRequestMidFeedback()


class FilterSendMidFeedback(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and user_data.get("status") == 'mid_feedback'


filter_send_mid_feedback = FilterSendMidFeedback()


class FilterReplyToMidFeedback(BaseFilter):
    def filter(self, message):
        return message.chat_id == MID_CHAT_ID and message.reply_to_message is not None and \
               message.reply_to_message.from_user.id == CASTLE_BOT_ID and \
               message.reply_to_message.forward_from is not None


filter_reply_to_mid_feedback = FilterReplyToMidFeedback()


class FilterRestrictFeedback(BaseFilter):
    def filter(self, message):
        return message.chat_id in [MID_CHAT_ID, SENTINELS_DUTY_CHAT_ID] and \
               message.text.startswith("/restrict_feedback_")


filter_restrict_feedback = FilterRestrictFeedback()


class FilterUnRestrictFeedback(BaseFilter):
    def filter(self, message):
        return message.chat_id in [MID_CHAT_ID, SENTINELS_DUTY_CHAT_ID] and \
               message.text.startswith("/unrestrict_feedback_")


filter_unrestrict_feedback = FilterUnRestrictFeedback()
