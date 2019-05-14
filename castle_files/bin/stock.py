"""
Здесь находятся всякие функции для непосредственной работы со стоком
"""
from castle_files.work_materials.item_consts import items
from castle_files.libs.bot_async_messaging import MAX_MESSAGE_LENGTH

import re


# Получает и сохраняет в user_data список шмоток, на которые есть рецепты для дальнейшего использования
def guild_recipes(bot, update, user_data):
    mes = update.message
    user_recipes = {}
    for string in mes.text.splitlines()[1:]:
        item_code = re.match("r\\S+", string).group()[1:]
        item_count = int(re.search("x (\\d+)", string).group(1))
        user_recipes.update({item_code: item_count})
    user_data.update({"recipes": user_recipes})
    bot.send_message(chat_id=mes.chat_id, text="Отлично! Теперь пришли мне форвард /g_stock_parts из @ChatWarsBot")


def guild_parts(bot, update, user_data):
    mes = update.message
    response = "Шмотки, которые можно скрафтить:\n"
    recipes = user_data.get("recipes")
    if recipes is None:
        # Необходим список рецептов
        bot.send_message(chat_id=mes.chat_id, text="Пришли мне форвард /g_stock_rec из @ChatWarsBot")
        return
    for string in mes.text.splitlines()[1:]:
        item_code = re.match("k\\S+", string).group()[1:]
        item_count = int(re.search("x (\\d+)", string).group(1))
        recipes_count = recipes.get(item_code)
        if recipes_count is None:
            continue
        item = items.get(item_code)
        if item is None:
            continue
        need_frags = item[2]
        try:
            item_count = min(recipes_count, item_count // need_frags)
        except Exception:
            item_count = 0
        new_response = ""
        if item_count > 0:
            new_response = "<b>{}</b> x <b>{}</b>\n".format(item[0], item_count)
        if len(response + new_response) >= MAX_MESSAGE_LENGTH:
            bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
            response = ""
        response += new_response
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
