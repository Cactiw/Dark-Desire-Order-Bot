"""
Здесь находятся всякие функции для непосредственной работы со стоком
"""
from castle_files.work_materials.item_consts import items
from castle_files.work_materials.resource_constants import resources, resources_reverted
from castle_files.work_materials.equipment_constants import equipment_names, get_equipment_by_name, \
    get_equipment_by_code
from castle_files.work_materials.alch_constants import alch_recipes
from castle_files.libs.bot_async_messaging import MAX_MESSAGE_LENGTH

from castle_files.libs.guild import Guild
from castle_files.libs.player import Player

import re


def get_item_code_by_name(name):
    for num, elem in list(items.items()):
        if name == elem[1]:
            code = "k" + num
            return code
        elif elem[0] in name and "recipe" in name.lower():
            code = "r" + num
            return code
        else:
            continue
    item = get_equipment_by_name(name)
    if item is not None:
        return item.type + item.code
    item = alch_recipes.get(name.lower())
    if item is not None:
        return item.get("code")
    item = resources.get(name)
    return item


def get_item_name_by_code(code):
    item = get_equipment_by_code(code)
    if item is not None:
        return item.name
    item = resources_reverted.get(code)
    if item is not None:
        return item
    if code[0] in ["k", "r"]:
        item = items.get(code[1:])
        if code[0] == 'k':
            return item[1]
        if code[0] == 'r':
            return item[0] + " recipe"
    if code[0] == "p":
        for name, potion in list(alch_recipes.items()):
            if potion.get("code") == code:
                return name
    return code


def stock_sort_comparator(item_code):
    # --> item_code: str || int
    if isinstance(item_code, int) or item_code.isdigit():
        return [0, int(item_code)]
    if item_code[0] in ["k", "r"]:
        return [1, int(item_code[1:])]
    if item_code[0] == "p":
        return [2, int(item_code[1:])]
    return [3, item_code]


def format_withdraw_link(response: str) -> str:
    return "<a href=\"https://t.me/share/url?url={}\">".format(response) + response + "</a>"


def format_all_withdraws(response: str, response_full: str, not_enough: str) -> str:
    response = format_withdraw_link(response)
    if not_enough != "":
        response += "\n\nВозможно, не хватает ресурсов:\n" + not_enough
        response += "\nПопытаться достать всё:\n"
        response += format_withdraw_link(response_full)
    else:
        response = format_withdraw_link(response_full)
    return response


def send_withdraw(bot, update):
    mes = update.message
    response, response_full = "/g_withdraw ", "/g_withdraw "
    give = {}
    res_count = 0
    player = Player.get_player(update.message.from_user.id)
    if player is None:
        return
    guild_stock = None
    if player.guild is not None:
        guild = Guild.get_guild(guild_id=player.guild)
        if guild.settings is not None:
            if guild.settings.get("withdraw") is False:
                if guild.chat_id == mes.chat_id:
                    return
        guild_stock = guild.api_info.get("stock")
    if "дай" in mes.text.lower():
        # Выдача ресурсов по Дай x y
        potions_dict = {
            "фр": ["p01", "p02", "p03"], "фд": ["p04", "p05", "p06"], "грид": ["p07", "p08", "p09"],
            "натуру": ["p10", "p11", "p12"], "ману": ["p13", "p14", "p15"], "твайлайт": ["p16", "p17", "p18"],
            "морф": ["p19", "p20", "p21"]}
        parse = mes.text.lower().split()[1:]
        mode = "name"
        names = []
        for string in parse:
            if mode == "quantity":
                mode = "name"
                try:
                    quantity = int(string)
                    if quantity > 0:
                        if not names:
                            continue
                        for name in names:
                            give.update({name: quantity})
                        continue
                except ValueError:
                    pass
            if mode == "name":
                mode = "quantity"
                potions = potions_dict.get(string)
                if potions is None:
                    if string not in list(resources) and string not in list(equipment_names) and string not in \
                            list(resources_reverted) and re.match("[rk]\\d\\d?", string) is None:
                        mode = "name"
                        continue
                    names = [string]  # Список из имён, к которым далее следует количество для выдачи
                    give.update({string: 1})
                else:
                    names = []
                    for p in potions:
                        give.update({p: 1})
                        names.append(p)
    else:
        for string in update.message.text.splitlines():
            parse = re.search("(\\d+) x ([^\n$]+)", string)
            if parse is None:
                continue
            count = int(parse.group(1))
            name = parse.group(2)
            code = resources.get(name)
            if code is None:
                for num, elem in list(items.items()):
                    if name.lower() == elem[1].lower():
                        code = "k" + num
                    elif elem[0].lower() in name.lower():
                        code = "r" + num
                    else:
                        continue
            if code is None:
                continue
            give.update({code: count})
    not_enough = ""
    for code, count in list(give.items()):
        if guild_stock is not None:
            # Есть данные о стоке, проверка наличия ресурсов
            in_stock = guild_stock.get(code) or 0
            if in_stock > 0:
                response += "{} {} ".format(code, min(count, in_stock))
            if in_stock < count:
                not_enough += "{} x {}\n".format(get_item_name_by_code(code), count - in_stock)
        response_full += "{} {} ".format(code, count)
        res_count += 1
        if res_count >= 8:
            response = format_all_withdraws(response, response_full, not_enough)
            bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML')
            response, response_full, not_enough = "/g_withdraw ", "/g_withdraw ", ""
            res_count = 0
    if res_count > 0:
        response = format_all_withdraws(response, response_full, not_enough)
        bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML')


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
            response = "<a href=\"https://t.me/share/url?url={}\">".format(response) + response + "</a>"
            bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
            response = "/g_withdraw "
            res_already_counted = 0
    if res_already_counted > 0:
        response = "<a href=\"https://t.me/share/url?url={}\">".format(response) + response + "</a>"
        bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


# Скинут /alch, выводит банки, которые можно скрафтить
def alch_possible_craft(bot, update):
    mes = update.message
    alch = {}
    for string in mes.text.splitlines()[1:]:
        parse = re.search("/aa_(\\d+) .* x (\\d+)", string)
        if parse is None:
            continue
        code = parse.group(1)
        count = int(parse.group(2))
        res = resources_reverted.get(code)
        alch.update({res.lower(): count})
    response = "Зелья и травы, которые можно скрафтить:\n"
    for name, potion in list(alch_recipes.items()):
        code = potion.get("code")
        recipe = potion.get("recipe")
        craft_count = 999999999
        for item, count in list(recipe.items()):
            has = alch.get(item) or 0
            can_craft = has // int(count)
            if can_craft < craft_count:
                craft_count = can_craft
        if craft_count > 0:
            response += "<a href=\"https://t.me/share/url?url={}\">{} ({})</a>" \
                       "\n".format("/brew_{} {}".format(code, craft_count), name, craft_count)
    response += "\n<em>Нажмите на название, чтобы переслать в бота.</em>"
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


def deposit(bot, update):
    mes = update.message
    response = "<b>Ресурсы на складе:</b>\n<em>Нажмите на ресурс, чтобы внести в гильдию</em>\n\n"
    for string in mes.text.splitlines():
        # parse = re.search("/aa_(\\d+)", string)
        parse = re.search("/lot_(\\S+) (.*) \\((\\d+)\\)", string)
        if parse is not None:
            # Кинут аукцион
            code = parse.group(1)
            res_name = parse.group(2)
            count = int(parse.group(3))
        else:
            parse = re.search("(.*) \\((\\d+)\\) /(use|view)_(.+)", string)
            if parse is not None:
                # Кинут misc
                code = parse.group(4)
                if code[-1] == ' ':
                    # Обрезаем последний пробел, найс чв вообще прогали, тупо пробел в конце строки
                    code = code[:-1]
                res_name = parse.group(1)
                count = int(parse.group(2))
            else:
                # Кинут сток
                parse = re.search("(/sg_\\d+ )?(.*) \\((\\d+)\\)", string)
                if parse is None:
                    continue
                res_name = parse.group(2)
                count = int(parse.group(3))
                code = resources.get(res_name)
        if code is None:
            for num, elem in list(items.items()):
                if res_name == elem[1]:
                    code = "k" + num
                elif elem[0] in res_name:
                    code = "r" + num
                else:
                    continue
        if code is None:
            continue
        response += "<a href=\"https://t.me/share/url?url=/g_deposit {} {}\">{} x {}</a>\n".format(code, count,
                                                                                                   res_name, count)
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
