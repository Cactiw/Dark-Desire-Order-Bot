"""
В этом модуле находятся фильтры для вахты деферов
"""
from telegram.ext import BaseFilter
from castle_files.work_materials.filters.general_filters import filter_is_pm
from castle_files.work_materials.globals import dispatcher, SENTINELS_DUTY_CHAT_ID, CASTLE_BOT_ID


class FilterBeginDuty(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["Заступить на вахту", "Go on duty"] and \
            user_data.get("status") == 'castle_gates'


filter_begin_duty = FilterBeginDuty()


class FilterEndDuty(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["Покинуть вахту", "Leave duty"] and \
            user_data.get("status") == 'castle_gates' and user_data.get('on_duty')


filter_end_duty = FilterEndDuty()


class FilterRequestDutyFeedback(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["Talk to 💂‍♂Guardians", "Обратиться к 💂‍♂Стражам"] and \
            user_data.get("status") == 'castle_gates' and not user_data.get('on_duty')


filter_request_duty_feedback = FilterRequestDutyFeedback()


class FilterSendDutyFeedback(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and user_data.get("status") == 'duty_feedback'


filter_send_duty_feedback = FilterSendDutyFeedback()


class FilterReplyToDutyFeedback(BaseFilter):
    def filter(self, message):
        return message.chat_id == SENTINELS_DUTY_CHAT_ID and message.reply_to_message is not None and \
               message.reply_to_message.from_user.id == CASTLE_BOT_ID and \
               (message.reply_to_message.forward_from is not None or (
                       'Запрос к стражнику' in message.reply_to_message.text and '#r' in message.reply_to_message.text))


filter_reply_to_duty_feedback = FilterReplyToDutyFeedback()


class FilterBaneInDutyChat(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        return message.chat_id == SENTINELS_DUTY_CHAT_ID and (user_data is None or not user_data.get("on_duty"))


filter_ban_in_duty_chat = FilterBaneInDutyChat()
