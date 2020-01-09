"""
В этом модуле находятся фильтры для функций в  ../bin/rewards.py
"""
from telegram.ext import BaseFilter

from castle_files.work_materials.filters.general_filters import filter_is_pm

from castle_files.work_materials.globals import dispatcher

from castle_files.bin.rewards import muted_players

import time


class FilterSmuggler(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        return filter_is_pm(message) and message.text in ["🧳Контрабандист", "🧳Smuggler"] and \
            user_data.get("status") == 'tea_party'


filter_smuggler = FilterSmuggler()


class FilterGetReward(BaseFilter):
    def filter(self, message):
        user_data = dispatcher.user_data.get(message.from_user.id)
        if user_data is None:
            return False
        print(user_data)
        return filter_is_pm(message) and (user_data.get("status") == 'requested_reward' or
                                          user_data.get("status") == "requested_additional_reward")


filter_get_reward = FilterGetReward()


class FilterRewardDeleteMessage(BaseFilter):
    def filter(self, message):
        muted_time = muted_players.get(message.from_user.id)
        if muted_time is not None:
            if time.time() > muted_time:
                muted_players.pop(message.from_user.id)
            else:
                return True
        return False


filter_reward_delete_message = FilterRewardDeleteMessage()
