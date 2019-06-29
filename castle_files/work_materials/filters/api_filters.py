"""
В этом модуле находятся фильтры для обработки команд, поступающих в бота и непосредственно связанных с АПИ ЧВ
"""
from telegram.ext import BaseFilter

from castle_files.work_materials.globals import API_APP_NAME
from castle_files.work_materials.filters.general_filters import filter_is_pm, filter_is_chat_wars_forward

import re


class FilterGrantAuthCode(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and filter_is_chat_wars_forward(message) and \
               re.match("Code \\d+ to authorize {}. This app will have the access to:".format(API_APP_NAME),
                        message.text)


filter_grant_auth_code = FilterGrantAuthCode()
