from telegram.ext import BaseFilter

from castle_files.work_materials.filters.general_filters import filter_is_chat_wars_forward

import re


class FilterIsHero(BaseFilter):
    def filter(self, message):
        print(filter_is_chat_wars_forward(message), re.match("[🍆🍁☘🌹🐢🦇🖤]+", message.text), re.search("🎒Рюкзак:", message.text))
        return filter_is_chat_wars_forward(message) and re.match("[🍆🍁☘🌹🐢🦇🖤]+", message.text) is not None and \
               re.search("🎒Рюкзак:", message.text) is not None


filter_is_hero = FilterIsHero()
