from telegram.ext import BaseFilter

from castle_files.work_materials.filters.general_filters import filter_is_chat_wars_forward, filter_is_pm

from castle_files.bin.trade_unions import union_chats, TradeUnion


class FilterTradeUnion(BaseFilter):
    def filter(self, message):
        if message.text:
            if message.forward_from is None:
                return False
            return message.text.startswith("🏠Trade Union:") and filter_is_chat_wars_forward(message) and \
                filter_is_pm(message)
        return False


filter_trade_union = FilterTradeUnion()


class FilterUnionList(BaseFilter):
    def filter(self, message):
        if message.text:
            if message.forward_from is None:
                return False
            return "/tu_list_" in message.text and filter_is_chat_wars_forward(message) and \
                filter_is_pm(message)
        return False


filter_union_list = FilterUnionList()


class FilterNeedToBanInUnionChat(BaseFilter):
    def filter(self, message):
        if message.text:
            print(list(union_chats.values()), message.chat_id)
            if message.chat_id not in list(union_chats.values()):
                return False
            union = TradeUnion.get_union(chat_id=message.chat_id)
            if union is None:
                return False
            return message.from_user.id not in union.players


filter_need_to_ban_in_union_chat = FilterNeedToBanInUnionChat()
