"""
Здесь назодятся фильтры для работы со стоком
"""
from telegram.ext import BaseFilter
from castle_files.work_materials.filters.general_filters import filter_is_pm, filter_is_chat_wars_forward, update_filter

from castle_files.work_materials.resource_constants import resources_reverted, resources

import re
import logging
import traceback


# Сообщение - форвард /g_stock_rec из чв3 и в личке
class FilterGuildStockRecipes(BaseFilter):
    def filter(self, message):
        return message.forward_from and filter_is_chat_wars_forward(message) and\
               filter_is_pm(message) and message.text.find("Guild Warehouse:") == 0 and "recipe" in message.text


filter_guild_stock_recipes = FilterGuildStockRecipes()


# Сообщение - форвард /g_stock_parts из чв3 и в личке
class FilterGuildStockParts(BaseFilter):
    def filter(self, message):
        return message.forward_from and filter_is_chat_wars_forward(message) and \
               filter_is_pm(message) and message.text.find("Guild Warehouse:") == 0 and "part" in message.text


filter_guild_stock_parts = FilterGuildStockParts()


# Сообщение - форвард нехватки ресов из чв3
class FilterStockWithdraw(BaseFilter):
    def filter(self, message):
        return (filter_is_chat_wars_forward(message) or True) and (
                message.text.startswith("Not enough materials") or message.text.startswith("Не хватает материалов") or
                message.text.startswith("Materials needed") or message.text.startswith("Нет нужных материалов") or
                message.text.startswith("Недостаточно ресурсов"))


filter_stock_withdraw = FilterStockWithdraw()


# Сообщение - форвард /g_stock_res из чв3 и в личке
class FilterGuildStockResources(BaseFilter):
    def filter(self, message):
        return message.forward_from and filter_is_chat_wars_forward(message) and \
               filter_is_pm(message) and message.text.find("Guild Warehouse:") == 0 and \
               resources_reverted.get(message.text.splitlines()[1].split(" ")[0]) is not None


filter_guild_stock_resources = FilterGuildStockResources()


# Сообщение - форвард /stock из чв3 и в личке
class FilterPlayerStockResources(BaseFilter):
    @update_filter
    def filter(self, message):
        return filter_is_chat_wars_forward(message) and message.text.startswith("📦Склад")


filter_player_stock_resources = FilterPlayerStockResources()


# Сообщение - форвард доступных вещей для продажи с аука из чв3 и в личке
class FilterPlayerAuction(BaseFilter):
    @update_filter
    def filter(self, message):
        return filter_is_chat_wars_forward(message) and \
               "🛎Welcome to auction!" in message.text and "You have for sale:" in message.text


filter_player_auction = FilterPlayerAuction()


# Сообщение - форвард /misc из чв3 и в личке
class FilterPlayerMisc(BaseFilter):
    @update_filter
    def filter(self, message):
        return filter_is_chat_wars_forward(message) and \
               re.search("(.*) \\((\\d+)\\) /(use)|(view)_(.+)]", message.text) is not None


filter_player_misc = FilterPlayerMisc()


# Сообщение - форвард алхимии из чв3 и в личке
class FilterPlayerAlch(BaseFilter):
    @update_filter
    def filter(self, message):
        try:
            return filter_is_chat_wars_forward(message) and \
                   message.text.splitlines()[0].partition(" (")[0] in list(resources)
        except Exception:
            return False


filter_player_alch = FilterPlayerAlch()


# Сообщение - форвард /alch из чв3 и в личке
class FilterPlayerAlchCraft(BaseFilter):
    @update_filter
    def filter(self, message):
        try:
            return filter_is_chat_wars_forward(message) and \
                   message.text.startswith("📦Склад:") and message.text.splitlines()[1].startswith("/aa_")
        except Exception:
            return False


filter_player_alch_craft = FilterPlayerAlchCraft()

filter_player_alch.update_filter = True
filter_player_alch_craft.update_filter = True
filter_player_misc.update_filter = True
filter_player_auction.update_filter = True
filter_player_stock_resources.update_filter = True


# Сообщение - ответ на форвард любого стока в групповом чате
class FilterReplyDeposit(BaseFilter):
    def filter(self, message):
        if message.text != "/deposit":
            return False
        message = message.reply_to_message
        if message is None:
            return False
        try:
            return filter_is_chat_wars_forward(message) and \
                   (filter_player_alch(message) or filter_player_alch_craft(message) or filter_player_misc(message)
                    or filter_player_auction(message) or filter_player_stock_resources(message))
        except Exception:
            logging.error(traceback.format_exc())
            return False


filter_reply_deposit = FilterReplyDeposit()


# Дай x y
class FilterGiveResource(BaseFilter):
    def filter(self, message):
        return message.text.lower().startswith("дай ")


filter_give_resource = FilterGiveResource()


# Крафт
class FilterCraft(BaseFilter):
    def filter(self, message):
        return message.text.lower().startswith("/craft")


filter_craft = FilterCraft()
