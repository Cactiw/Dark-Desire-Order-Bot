"""
Здесь назодятся фильтры для работы со стоком
"""
from telegram.ext import BaseFilter
from castle_files.work_materials.filters.general_filters import filter_is_pm, filter_is_chat_wars_forward

from castle_files.work_materials.resource_constants import resources_reverted


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
        return filter_is_chat_wars_forward(message) and (
                message.text.startswith("Not enough materials") or message.text.startswith("Не хватает материалов") or
                message.text.startswith("Materials needed"))


filter_stock_withdraw = FilterStockWithdraw()


# Сообщение - форвард /g_stock_res из чв3 и в личке
class FilterGuildStockResources(BaseFilter):
    def filter(self, message):
        return message.forward_from and filter_is_chat_wars_forward(message) and \
               filter_is_pm(message) and message.text.find("Guild Warehouse:") == 0 and \
               resources_reverted.get(message.text.splitlines()[1].split(" ")[0]) is not None


filter_guild_stock_resources = FilterGuildStockResources()
