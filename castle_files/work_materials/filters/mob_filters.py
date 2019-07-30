from telegram.ext import BaseFilter

from castle_files.work_materials.filters.general_filters import filter_is_pm, filter_is_chat_wars_forward


class FilterMobMessage(BaseFilter):
    def filter(self, message):
        return (filter_is_chat_wars_forward(message) or True) and filter_is_pm(message) and \
               '/fight' in message.text.lower()


filter_mob_message = FilterMobMessage()
