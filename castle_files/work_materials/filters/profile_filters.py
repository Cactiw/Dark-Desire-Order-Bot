from telegram.ext import BaseFilter

from castle_files.work_materials.filters.general_filters import filter_is_chat_wars_forward, filter_is_pm

import re


class FilterIsHero(BaseFilter):
    def filter(self, message):
        return filter_is_chat_wars_forward(message) and re.match("[🍆🍁☘🌹🐢🦇🖤]+", message.text) is not None and \
               re.search("🎒Рюкзак:", message.text) is not None


filter_is_hero = FilterIsHero()


class FilterViewHero(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and message.text.startswith("Профиль")


filter_view_hero = FilterViewHero()
