"""
Здесь находятся всякие функции для непосредственной работы со стоком
"""
from castle_files.work_materials.item_consts import items
from castle_files.work_materials.resource_constants import resources, resources_reverted, get_resource_code_by_name, \
    get_resource_name_by_code
from castle_files.work_materials.equipment_constants import equipment_names, get_equipment_by_name, \
    get_equipment_by_code
from castle_files.work_materials.alch_constants import alch_recipes
from castle_files.work_materials.recipes import craft as craft_dict
from castle_files.libs.bot_async_messaging import MAX_MESSAGE_LENGTH

from castle_files.libs.guild import Guild
from castle_files.libs.player import Player

from castle_files.bin.stock_service import get_item_name_by_code, get_item_code_by_name, get_equipment_by_code, \
    get_equipment_by_name
from castle_files.bin.service_functions import increase_or_add_value_to_dict, decrease_or_pop_value_from_dict, \
    pop_from_user_data_if_presented

import re


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
            if "Нет нужных материалов" in mes.text:
                parse = re.search("([^\n$]+) x (\\d+)", string)
                if parse is None:
                    continue
                count = int(parse.group(2))
                name = parse.group(1)
                code = resources.get(name)
            else:
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


def get_craft_by_code(code: str) -> dict:
    eq = get_equipment_by_code(code)
    if eq is None:
        return None
    return craft_dict.get(eq.name.lower())


def get_craft_name_by_code(code: str) -> str:
    eq = get_equipment_by_code(code)
    if eq is None:
        return None
    return eq.name.lower()


LEVEL_OFFSET = "    "
LEVEL_SEPARATOR = "|"


def get_craft_by_name(name: str) -> dict:
    return craft_dict.get(name)


def format_resource_string(name, code, player_count, guild_count, total_count, need_count,
                           need_separator: bool = True) -> str:
    return "{} {} {} x {} | {} ({})📦 {}".format(
        LEVEL_SEPARATOR if need_separator else "", "<code>{}</code>".format(code) if code is not None else "",
        name, need_count,
        min(total_count, need_count), min(player_count, need_count), "✅" if total_count >= need_count else "❌")


def count_craft(craft_item: dict, craft_name: str, need_count: int, stock: dict, guild_stock: dict, withdraw: dict,
                buy: dict, current_offset: str, force_deep: bool = False):
    if craft_item is None:
        craft_type = "simple"
        search_name = craft_name[0].capitalize() + craft_name[1:]
        craft_code = get_resource_code_by_name(search_name)
        if craft_code is None:
            craft_code = get_item_code_by_name(search_name)
    else:
        craft_type = craft_item.get("type")
        craft_code = str(craft_item.get("code"))
    player_count, guild_count = stock.get(craft_code, 0), guild_stock.get(craft_code, 0)
    total_count = player_count + guild_count
    if craft_type == "simple" or (not force_deep and total_count >= need_count):
        # Добавляем ресурс в список на выдачу, и вычитаем из стока, чтобы не посчитать далее дважды
        if player_count < need_count:
            withdraw_count = min(guild_count, need_count - player_count)
            increase_or_add_value_to_dict(withdraw, craft_code, withdraw_count)
            pop_from_user_data_if_presented(stock, craft_code)
            decrease_or_pop_value_from_dict(guild_stock, craft_code, withdraw_count)

            buy_count = need_count - total_count
            if buy_count > 0:
                increase_or_add_value_to_dict(buy, craft_code, buy_count)
        else:
            decrease_or_pop_value_from_dict(stock, craft_code, need_count)
        return "{}{}".format(
            current_offset, format_resource_string(craft_name, craft_code, player_count, guild_count, total_count,
                                                   need_count,
                                                   need_separator=current_offset != ""))
    res = ""
    if not force_deep:
        res += "{}{}\n".format(current_offset,
                               format_resource_string(craft_name, craft_code, player_count, guild_count, total_count,
                                                      need_count,
                                                      need_separator=current_offset != ""))
    for resource_name, count in list(craft_item.get("recipe").items()):
        if not force_deep and craft_code is not None:
            pop_from_user_data_if_presented(stock, craft_code)
            increase_or_add_value_to_dict(withdraw, craft_code, guild_count)
            pop_from_user_data_if_presented(guild_stock, craft_code)

        res += "{}\n".format(count_craft(
            get_craft_by_name(resource_name), resource_name, count * need_count, stock, guild_stock, withdraw, buy,
            current_offset + (LEVEL_OFFSET if not force_deep else "")))
    return res[:-1]


def format_buy_resources(buy: dict) -> str:
    from castle_files.bin.api import cwapi
    res = ""
    prices = cwapi.api_info.get("prices") or {}
    total_price = 0
    for code, count in list(buy.items()):
        price = prices.get(code, "❔")
        full_price = price * count if isinstance(price, int) else 0
        total_price += full_price
        res += "{} {} x {} {}\n".format(
            code, get_item_name_by_code(code), count,
            "{}💰 ({}💰x{})".format(full_price, price, count) if isinstance(price, int) else price)
    res += "\nВсего: {}💰\n".format(total_price)
    return res


def craft(bot, update):
    args = update.message.text.split()[1:]
    if args:
        code = args[0]  # TODO чёт сделать
        pass
    else:
        try:
            code = re.search("craft_(\\w+)", update.message.text).group(1)
        except Exception:
            bot.send_message(chat_id=update.message.chat_id, text="Неверный синтаксис")
            return
    name = get_craft_name_by_code(code)
    craft_eq = get_craft_by_name(name)
    player = Player.get_player(update.message.from_user.id)
    guild = Guild.get_guild(player.guild)
    guild_stock = guild.get_stock({}).copy()
    withdraw, buy = {}, {}
    res = "⚒Крафт <b>{}</b>:\n{}\n\n{}\n\n" \
          "<em>📦 - весь сток, (👤) - уже у Вас (разница в гильдии)\n" \
          "Совет: обновляйте свой сток и сток гильдии перед началом крафта:\n</em>" \
          "/update_stock\n/update_guild".format(
                name, count_craft(craft_eq, name, 1, player.stock.copy(), guild_stock, withdraw, buy, "",
                                  force_deep=True),
                "Не хватает базовых ресурсов (необходимо докупить):\n{}".format(format_buy_resources(buy)) if buy else
                "<b>Все ресурсы присутствуют! Можно крафтить!</b>\n"
                "(Не забудьте достать из гильдии при помощи кнопки ниже)")
    print(withdraw)
    print(buy)
    bot.send_message(chat_id=update.message.chat_id, text=res, parse_mode='HTML')



