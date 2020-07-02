"""
Здесь находятся всякие функции для непосредственной работы со стоком
"""
from castle_files.work_materials.item_consts import items
from castle_files.work_materials.resource_constants import resources, resources_reverted, get_resource_code_by_name, \
    get_resource_name_by_code
from castle_files.work_materials.equipment_constants import equipment_names, get_equipment_by_name, \
    get_equipment_by_code, search_equipment_by_name
from castle_files.work_materials.alch_constants import alch_recipes
from castle_files.work_materials.recipes import craft as craft_dict
from castle_files.libs.bot_async_messaging import MAX_MESSAGE_LENGTH

from castle_files.libs.guild import Guild
from castle_files.libs.player import Player
from castle_files.libs.equipment import Equipment

from castle_files.bin.stock_service import get_item_name_by_code, get_item_code_by_name, get_equipment_by_code, \
    get_equipment_by_name
from castle_files.bin.service_functions import increase_or_add_value_to_dict, decrease_or_pop_value_from_dict, \
    pop_from_user_data_if_presented, merge_int_dictionaries, build_inline_buttons_menu
from castle_files.bin.buttons import get_craft_buttons
from castle_files.bin.equipment import TIERS, InlineKeyboardMarkup
from castle_files.bin.api import try_update_all_stocks

from distutils.util import strtobool

import logging
import traceback
import re

WITHDRAW_MESSAGE_LIMIT = 9


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


def send_withdraw(bot, update, *args):
    manual = False
    if args and args[0] == "custom_request":
        manual = True
        give = args[1]
        chat_id = update
        player = Player.get_player(chat_id)
    else:
        chat_id = update.message.chat_id
        player = Player.get_player(update.message.from_user.id)
        give = {}
    mes = update.message if not isinstance(update, int) else None
    response, response_full = "/g_withdraw ", "/g_withdraw "
    res_count = 0
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
    if manual:
        pass
    elif "дай" in mes.text.lower():
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
        text = update.message.text.partition("In your stock:")
        text = text[2] or text[0]
        for string in text.splitlines():
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
            bot.send_message(chat_id=chat_id, text=response, parse_mode='HTML')
            response, response_full, not_enough = "/g_withdraw ", "/g_withdraw ", ""
            res_count = 0
    if res_count > 0:
        response = format_all_withdraws(response, response_full, not_enough)
        bot.send_message(chat_id=chat_id, text=response, parse_mode='HTML')


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
        if res_already_counted >= WITHDRAW_MESSAGE_LIMIT:
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
    if mes.text == "/deposit":
        if mes.reply_to_message is None:
            return
        mes = mes.reply_to_message
    response = "<b>Ресурсы на складе:</b>\n<em>Нажмите на ресурс, чтобы внести в гильдию</em>\n\n"
    num = 0
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
        num += 1
        if num % 5 == 0:
            response += "\n"
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


def get_craft_by_code(code: str) -> dict:
    eq = get_equipment_by_code(code)
    if eq is None:
        return None
    return craft_dict.get(eq.name.lower())


def get_craft_name_by_code(code: str) -> str:
    eq = get_equipment_by_code(code)
    if eq is None:
        return get_item_name_by_code(code).lower()
    return eq.name.lower()


LEVEL_OFFSET = "    "
LEVEL_SEPARATOR = "├"
LAST_IN_LEVEL_SEPARATOR = "└"


def check_depth(depth, depth_limit) -> bool:
    return depth_limit is not None and depth > depth_limit


def get_craft_by_name(name: str) -> dict:
    return craft_dict.get(name)


def format_resource_string(name, code, player_count, guild_count, total_count, need_count,
                           need_separator: bool = True, close_separator: bool = False, depth: int = None) -> str:
    emoji = "📜" if code[0] == "r" else ("🔩" if code[0] == "k" else "📦")
    return "{} {}{} {} x {} | {}{}".format(
        (LAST_IN_LEVEL_SEPARATOR if close_separator else LEVEL_SEPARATOR) if need_separator else "",
        emoji if depth < 3 else "",
        "<code>{}</code>".format(code) if code is not None else "",
        name, need_count, ("" if player_count >= need_count else "{}📤 ".format(need_count - player_count))
        if total_count >= need_count else "{} ".format(total_count), "✅" if total_count >= need_count else "❌")


def count_craft(craft_item: dict, craft_name: str, need_count: int, stock: dict, guild_stock: dict, withdraw: dict,
                buy: dict, to_craft: dict, current_offset: str, depth: int = 0, depth_limit: int = None,
                force_deep: bool = False, explicit: bool = True, last_one: bool = False):
    depth += 1
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
        enough = True
        if player_count < need_count:
            withdraw_count = min(guild_count, need_count - player_count)
            increase_or_add_value_to_dict(withdraw, craft_code, withdraw_count)
            pop_from_user_data_if_presented(stock, craft_code)
            decrease_or_pop_value_from_dict(guild_stock, craft_code, withdraw_count)

            buy_count = need_count - total_count
            if buy_count > 0:
                enough = False
                increase_or_add_value_to_dict(buy, craft_code, buy_count)
        else:
            decrease_or_pop_value_from_dict(stock, craft_code, need_count)
        if (enough and not explicit) or check_depth(depth, depth_limit):
            return ""
        return "{}{}".format(
            current_offset, format_resource_string(craft_name, craft_code, player_count, guild_count, total_count,
                                                   need_count, depth=depth,
                                                   need_separator=current_offset != "", close_separator=last_one))
    res = ""
    if not force_deep or depth == depth_limit:
        res += "{}{}\n".format(current_offset,
                               format_resource_string(craft_name, craft_code, player_count, guild_count, total_count,
                                                      need_count, depth=depth,
                                                      need_separator=current_offset != "", close_separator=last_one))

        lvl_name = "level_{}".format(depth)
        cur_lvl = to_craft.get(lvl_name)
        if cur_lvl is None:
            cur_lvl = {}
            to_craft.update({lvl_name: cur_lvl})
        increase_or_add_value_to_dict(cur_lvl, craft_code, need_count - total_count)

    if not force_deep and craft_code is not None:
        pop_from_user_data_if_presented(stock, craft_code)
        increase_or_add_value_to_dict(withdraw, craft_code, guild_count)
        pop_from_user_data_if_presented(guild_stock, craft_code)

    resources_to_craft = list(craft_item.get("recipe").items())
    for i, (resource_name, count) in enumerate(resources_to_craft):
        current_withdraw = {}
        new_res = count_craft(
            get_craft_by_name(resource_name), resource_name, count * need_count, stock, guild_stock, current_withdraw,
            buy,
            to_craft, current_offset + (LEVEL_OFFSET if not force_deep else ""),
            depth=depth, depth_limit=depth_limit, explicit=explicit, last_one=i == len(resources_to_craft) - 1)
        merge_int_dictionaries(withdraw, current_withdraw)

        res += ("<a href=\"/g_withdraw {}\">{}</a>\n".format(
               " ".join(["{} {}".format(code, count) for code, count in current_withdraw.items()]), new_res
        ) if current_withdraw is not None else "{}\n".format(new_res)) if new_res != "" else ""
        if res[-2:] == "\n\n":
            res = res[:-1]
    return res[:-1] if not check_depth(depth, depth_limit) else ""


def format_buy_resources(buy: dict) -> str:
    from castle_files.bin.api import cwapi
    res = ""
    prices = cwapi.api_info.get("prices") or {}
    total_price = 0
    for code, count in list(buy.items()):
        price = prices.get(code, "❔")
        full_price = price * count if isinstance(price, int) else 0
        total_price += full_price
        res += "{} {} x {} ≈ {}\n".format(
            code, get_item_name_by_code(code), count,
            "{}💰 ({}💰x{})".format(full_price, price, count) if isinstance(price, int) else price)
    res += "\nВсего: {}💰\n".format(total_price)
    return res


def get_craft_text(craft_eq, name, code: str, count: int, player_stock, guild_stock, withdraw, buy, to_craft,
                   explicit: bool, depth_limit: int) -> str:
    craft_text = count_craft(craft_eq, name, count, player_stock, guild_stock, withdraw, buy, to_craft, "",
                             force_deep=True, explicit=explicit, depth_limit=depth_limit)
    collect_craft(to_craft)
    return "⚒Крафт <b>{}</b> x {}:\n{}\n\n{}\nДля отображения лавок нажмите ⚒Крафт!\n\n" \
          "<em>📦📤 - нужно достать из гильдии\n" \
          "Совет: обновляйте свой сток и сток гильдии перед началом крафта:\n</em>" \
          "/update_stock\n/update_guild".format(
                name, count, craft_text,
                "Не хватает базовых ресурсов (необходимо докупить):\n{}".format(format_buy_resources(buy)) if buy else
                "<b>Все ресурсы присутствуют! Можно крафтить!</b>\n"
                "(Не забудьте достать из гильдии при помощи кнопки ниже)")


def collect_craft(to_craft: dict):
    craft = to_craft.copy()
    to_craft.clear()
    max_lvl = 0
    i = 2
    while True:
        lvl_name = "level_{}".format(i)
        cur_lvl = craft.get(lvl_name)
        if cur_lvl is None:
            i -= 1
            break
        i += 1
    j = 0
    used_codes = []
    while True:
        lvl_name = "level_{}".format(i)
        cur_lvl = craft.get(lvl_name)
        if cur_lvl is None:
            break
        for code, count in list(cur_lvl.items()):
            total_count = count
            if code in used_codes:
                continue
            for z in range(i - 1, 2, -1):
                lvl_name = "level_{}".format(z)
                cur_lvl = craft.get(lvl_name)
                total_count += cur_lvl.get(code, 0)
            to_craft.update({j: [code, total_count]})
            j += 1
            used_codes.append(code)
        i -= 1


def get_shops_text(eq, name: str = None) -> str:
    res = ""

    if eq is None:
        LIMIT = 5
        if name is None:
            return ""
        from castle_files.bin.api import cwapi
        mana_cost = None
        res_list = []
        i = 0
        for shop in cwapi.api_info.get("shops"):
            offer = None
            for cur_offer in shop["offers"]:
                if cur_offer["item"].lower() == name.lower():
                    offer = cur_offer
            if offer is None:
                continue
            mana_cost = offer.get("mana")
            if shop.get("mana") < mana_cost:
                continue
            cur_res = "{}💰 {}💧 <a href=\"t.me/share/url?url=/ws_{}\">{}{}</a>".format(
                offer.get("price"), shop["mana"], shop["link"], shop["ownerCastle"], shop["name"])
            res_list.append([offer.get("price"), shop.get("mana"), cur_res])

            i += 1
            if i >= LIMIT:
                res_list.append([1000000000, 1000000000,
                                 "...\n<a href=\"t.me/share/url?url=/ws {}\">Все лавки</a>".format(name)])
                break
        res_list.sort(key=lambda x: (x[0], -x[1]))
        return "Доступные лавки (Нужно {}💧)\n".format(mana_cost) + "\n".join(map(lambda x: x[2], res_list))

    mana_cost = None
    shops = eq.get_quality_shops()
    shops.sort(key=lambda sh: (sh.qualityCraftLevel, -sh.get_offer(eq.name).get("price")),
               reverse=True)
    max_lvl = 0
    for shop in shops:
        if not shop.is_open() or shop.qualityCraftLevel < max_lvl:
            continue
        if shop.qualityCraftLevel > max_lvl:
            max_lvl = shop.qualityCraftLevel
        offer = shop.get_offer(eq.name)
        mana_cost = offer.get("mana")
        res += shop.format_offer(eq, offer)
    return "Доступные лавки (Нужно {}💧)\n".format(mana_cost) + res + "\nВсе лавки: /ws_{}".format(eq.format_code())


def get_craft_text_withdraw_and_buy_by_code(code: str, count, player_id, explicit: bool = True,
                                            depth_limit: int = None) -> tuple:
    name = get_craft_name_by_code(code)
    craft_eq = get_craft_by_name(name)
    player = Player.get_player(player_id)
    guild = Guild.get_guild(player.guild)
    guild_stock = guild.get_stock({}).copy() if guild is not None else {}
    player_stock = player.stock.copy() if player is not None else {}
    withdraw, buy, to_craft = {}, {}, {}
    res = get_craft_text(craft_eq, name, code, count, player_stock, guild_stock, withdraw, buy, to_craft,
                         explicit=explicit, depth_limit=depth_limit)  # Has side-effects!
    return res, withdraw, buy, to_craft


def craft(bot, update):
    first, space, search = update.message.text.partition(" ")
    if search != "" and first == "/craft":
        # Ищем экипировку для крафта
        return search_craft(bot, update)
    elif update.message.text == "/craft":
        # Пустая команда /craft - показываем возможный крафт
        return craft_possible(bot, update)
    try:
        parse = re.search("craft_([^_ ]+)([_ ](\\d+))?", update.message.text)
        code = parse.group(1)
    except Exception:
        bot.send_message(chat_id=update.message.chat_id, text="Неверный синтаксис")
        return
    try:
        name = get_craft_name_by_code(code)
    except Exception:
        bot.send_message(chat_id=update.message.chat_id, text="Предмет не найден.")
        return
    try_update_all_stocks(update.message.from_user.id)
    count = int(parse.group(3)) if parse.group(3) is not None else 1
    res, withdraw, buy, to_craft = get_craft_text_withdraw_and_buy_by_code(
        code, count, update.message.from_user.id, depth_limit=2)
    buttons = get_craft_buttons(code, count)
    bot.send_message(chat_id=update.message.chat_id, text=res, parse_mode='HTML', reply_markup=buttons)


def craft_action(bot, update):
    mes = update.callback_query.message
    data = update.callback_query.data
    parse = re.search("craft_(withdraw|buy|fewer|more|go|all|recipeonly)_([^_]+)_([^_]+)", data)
    if parse is None:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                                text="Произошла ошибка. Попробуйте начать сначала.", show_alert=True)
        return
    message_need_to_be_updated = False
    action, code, count = parse.groups()
    count = int(count)
    explicit = True
    recipe_only = False
    if action in frozenset({"fewer", "more", "all", "recipeonly"}):
        message_need_to_be_updated = True
        state = re.search("craft_[^_]+_[^_]+_[^_]+_([^_]+)_([^_]+)", data)
        if state is None:
            logging.warning("State is None in craft")
            explicit = action == "more"
            recipe_only = True
        else:
            explicit, recipe_only = state.groups()
            explicit, recipe_only = strtobool(explicit), strtobool(recipe_only)
        if action in frozenset({"fewer", "more"}):
            explicit = action == "more"
        elif action in frozenset({"all", "recipeonly"}):
            recipe_only = action == "recipeonly"

    res, withdraw, buy, to_craft = get_craft_text_withdraw_and_buy_by_code(
        code, count, update.callback_query.from_user.id, explicit=explicit, depth_limit=2 if recipe_only else None)
    if action == "withdraw":
        send_withdraw(bot, mes.chat_id, "custom_request", withdraw)
    elif action == "buy":
        for code, count in list(buy.items()):
            bot.send_message(chat_id=mes.chat_id, text="/wtb_{}_{}".format(code, count))
    elif action == "go":
        name = get_craft_name_by_code(code)
        res = "Действия для крафта:\n💰Купить недостающие ресурсы (достать с биржи)\n" \
              "📦Достать из гильдии всё необходимое\n\n"
        i = 0
        while True:
            l = to_craft.get(i)
            if l is None:
                break
            item_code, item_count = l
            res += "⚒Изготовить <code>{}</code> {} x {}: <a href=\"t.me/share/url?url=/craft_{} {}\">" \
                   "/craft_{} {}</a>\n".format(
                        item_code, get_resource_name_by_code(item_code), item_count, item_code, item_count,
                        item_code, item_count)
            i += 1
        res += "\n<a href=\"t.me/share/url?url=/craft_{}{}\">Изготовить {}!</a>\n".format(
            code, " {}".format(count) if count > 1 else "", name)
        res += "\n{}".format(get_shops_text(eq=get_equipment_by_code(code), name=name))
        bot.send_message(chat_id=mes.chat_id, text=res, parse_mode='HTML')

    if message_need_to_be_updated:
        buttons = get_craft_buttons(code, count, explicit=explicit, recipe_only=recipe_only)
        try:
            bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=res,
                                reply_markup=buttons, parse_mode='HTML')
        except Exception:
            logging.error(traceback.format_exc())
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Готово!")


def search_craft(bot, update):
    search = update.message.text.partition(" ")[2]
    if len(search) < 4:
        bot.send_message(chat_id=update.message.chat_id, text="Слишком короткий поисковый запрос (менее 4 символов)")
        return
    response = "Найденная экипировка:\n"
    suitable_equipment = search_equipment_by_name(search)
    if not suitable_equipment:
        bot.send_message(chat_id=update.message.chat_id, text="Экипировка не найдена.")
        return
    for eq in suitable_equipment:
        response += "{} /craft_{}\n".format(eq.name, eq.format_code())
    bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML')


def get_possible_buttons(selected_tier: int):
    return build_inline_buttons_menu(
        TIERS, "craft_possible_tier_", 2, None if selected_tier is None else lambda data, num: num == selected_tier,
        skip_first=2)


POSSIBLE_LIMIT = 20


def get_possible_text(stock, tier: int = None) -> str:
    can_craft, possible_craft = [], []
    for short_code, item in list(items.items()):
        eq = get_equipment_by_name(item[0])
        if eq is None:
            continue
        parts_count = stock.get("k" + short_code, 0)
        recipes_count = stock.get("r" + short_code, 0)
        need_parts = max(0, item[2] - parts_count) + 1 - min(1, recipes_count)
        craft_count = min(recipes_count, parts_count // item[2])
        if eq is None:
            logging.warning("Equipment is None for {}".format(item[0]))
            continue
        if tier is not None and eq.tier != tier:
            continue
        if need_parts == 0:
            can_craft.append([need_parts, eq, craft_count])
        else:
            possible_craft.append([need_parts, eq, recipes_count, parts_count, item[2]])
    can_craft.sort(key=lambda x: (-x[1].tier, x[1].name))
    possible_craft.sort(key=lambda x: (x[0], (-x[1].tier, x[1].name)))
    res = "Экипировка, которую можно скрафтить:\n"
    for item in can_craft:
        res += "{}{} x {}: /craft_{}\n".format(item[1].get_tier_emoji(), item[1].name, item[2], item[1].format_code())
    res += "\nНемного не хватает:\n"
    for item in possible_craft[:POSSIBLE_LIMIT]:
        res += "{}{} - {}📄 {}/{}🔩\n".format(item[1].get_tier_emoji(), item[1].name, item[2], item[3], item[4])
    return res


def craft_possible(bot, update):
    player = Player.get_player(update.message.from_user.id)
    guild = Guild.get_guild(player.guild)
    guild_stock = guild.get_stock() if guild is not None else {}
    stock = merge_int_dictionaries((player.stock or {}).copy(), guild_stock.copy())
    res = get_possible_text(stock)
    buttons = InlineKeyboardMarkup(get_possible_buttons(None))
    bot.send_message(chat_id=update.message.chat_id, text=res, parse_mode='HTML', reply_markup=buttons)


def set_craft_possible_tier(bot, update, user_data):
    mes = update.callback_query.message
    data = update.callback_query.data
    player = Player.get_player(update.callback_query.from_user.id)
    guild = Guild.get_guild(player.guild)
    guild_stock = guild.get_stock() if guild is not None else {}
    stock = merge_int_dictionaries(player.stock.copy(), guild_stock.copy())
    parse = re.search("craft_possible_tier_(\\d+)", data)
    if parse is None:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=True,
                                text="Произошла ошибка. Попробуйте начать сначала.")
        return
    tier = user_data.get("craft_possible_tier")
    new_tier = int(parse.group(1))
    if tier == new_tier:
        new_tier = None
        pop_from_user_data_if_presented(user_data, "craft_possible_tier")
    else:
        user_data.update({"craft_possible_tier": new_tier})
    res = get_possible_text(stock, tier=new_tier)
    buttons = InlineKeyboardMarkup(get_possible_buttons(new_tier))
    try:
        bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=res,
                            reply_markup=buttons, parse_mode='HTML')
    except Exception:
        logging.error(traceback.format_exc())
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Готово!")
