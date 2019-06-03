"""
Здесь находятся всякие функции для непосредственной работы со стоком
"""
from castle_files.work_materials.item_consts import items
from castle_files.work_materials.resource_constants import resources, resources_reverted
from castle_files.libs.bot_async_messaging import MAX_MESSAGE_LENGTH

from castle_files.libs.guild import Guild
from castle_files.libs.player import Player

import re


def send_withdraw(bot, update):
    response = "/g_withdraw "
    res_count = 0
    player = Player.get_player(update.message.from_user.id)
    if player is None:
        return
    if player.guild is not None:
        guild = Guild.get_guild(guild_id=player.guild)
        if guild.settings is not None:
            if guild.settings.get("withdraw") is False:
                return
    for string in update.message.text.splitlines():
        parse = re.search("(\\d+) x ([^\n$]+)", string)
        if parse is None:
            continue
        count = int(parse.group(1))
        name = parse.group(2)
        code = resources.get(name)
        if code is None:
            for num, elem in list(items.items()):
                if name == elem[1]:
                    code = "k" + num
                elif elem[0] in name:
                    code = "r" + num
                else:
                    continue
        if code is None:
            continue
        response += "{} {} ".format(code, count)
        res_count += 1
        if res_count >= 8:
            bot.send_message(chat_id=update.message.chat_id, text=response)
            response = "/g_withdraw "
            res_count = 0
    if res_count > 0:
        bot.send_message(chat_id=update.message.chat_id, text=response)


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


def set_withdraw_res(bot, update, user_data, args):
    mes = update.message
    found = []
    not_found = False
    response = "Список для выдачи ресурсов обновлён. Текущий список:\n"
    response_end = "\nНе найдены ресурсы с кодом:\n"
    for res_code in args:
        res_name = resources_reverted.get(res_code)
        if res_name is None:
            not_found = True
            response_end += "<b>{}</b>\n".format(res_code)
        else:
            if res_code in found:
                continue
            found.append(res_code)
            response += "<b>{}</b>\n".format(res_name)
    user_data.update({"withdraw_res": found})
    if not_found:
        response += response_end
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


def withdraw_resources(bot, update, user_data):
    mes = update.message
    res_codes = user_data.get("withdraw_res")
    if res_codes is None or not res_codes:
        bot.send_message(chat_id=mes.chat_id,
                         text="Необходимо задать список ресурсов для выдачи командой /set_withdraw_res")
        return
    response = "/g_withdraw "
    res_already_counted = 0
    for line in mes.text.splitlines()[1:]:
        code = line.split(" ")[0]
        if code not in res_codes:
            continue
        res_count = re.search("x (\\d+)", line)
        if res_count is None:
            continue
        res_count = int(res_count.group(1))
        response += "{} {} ".format(code, res_count)
        res_already_counted += 1
        if res_already_counted >= 8:
            bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
            response = "/g_withdraw "
            res_already_counted = 0
    if res_already_counted > 0:
        bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


def deposit(bot, update):
    mes = update.message
    # 📦Склад
    response = "<b>Ресурсы на складе:</b>\n<em>Нажмите на ресурс, чтобы внести в гильдию</em>\n\n"
    for string in mes.text.splitlines()[1:]:
        parse = re.search("(/sg_\\d+)? (.*) \\((\\d+)\\)", string)
        if parse is None:
            continue
        res_name = parse.group(2)
        count = int(parse.group(3))
        code = resources.get(res_name)
        if code is None:
            continue
        response += "<a href=\"https://t.me/share/url?url=/g_deposit {} {}\">{} x {}</a>\n".format(code, count,
                                                                                                   res_name, count)
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
