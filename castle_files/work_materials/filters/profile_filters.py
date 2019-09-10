from telegram.ext import BaseFilter

from castle_files.work_materials.filters.general_filters import filter_is_chat_wars_forward, filter_is_pm
from castle_files.work_materials.globals import allowed_list, class_chats, castle_chats

from castle_files.libs.player import Player

from castle_files.bin.profile import castle_chat_check

import re


class FilterNotRegistered(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and Player.get_player(message.from_user.id) is None


filter_not_registered = FilterNotRegistered()


class FilterForbidden(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and message.from_user.id not in allowed_list


filter_forbidden = FilterForbidden()


class FilterIsHero(BaseFilter):
    def filter(self, message):
        return filter_is_chat_wars_forward(message) and re.match("[🍆🍁☘🌹🐢🦇🖤]+", message.text) is not None and \
               re.search("🎒Рюкзак:", message.text) is not None


filter_is_hero = FilterIsHero()


class FilterIsProfile(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and filter_is_chat_wars_forward(message) \
               and "Битва" in message.text and "семи замков через" in message.text and \
               "Состояние:" in message.text and "Подробнее: /hero" in message.text


filter_is_profile = FilterIsProfile()


class FilterViewHero(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and (message.text in [
            "👀 Посмотреть в зеркало", "👀 Профиль", "👀 Profile", "👀 Look in the mirror"])


filter_view_hero = FilterViewHero()


class FilterViewProfile(BaseFilter):
    def filter(self, message):
        return filter_is_pm(message) and message.text.startswith("/view_profile_")


filter_view_profile = FilterViewProfile()


class FilterSetClass(BaseFilter):
    def filter(self, message):
        if message.text:
            if message.forward_from is None:
                return False
            return 'skills levels' in message.text and filter_is_chat_wars_forward(message) and filter_is_pm(message)
        return False


filter_set_class = FilterSetClass()


class FilterInClassChat(BaseFilter):
    def filter(self, message):
        return message.chat_id in list(class_chats.values())


filter_in_class_chat = FilterInClassChat()


class FilterKickFromCastleChat(BaseFilter):
    def filter(self, message):
        return message.chat_id in castle_chats and castle_chat_check(message)


filter_kick_from_castle_chat = FilterKickFromCastleChat()
