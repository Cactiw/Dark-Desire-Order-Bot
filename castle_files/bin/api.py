"""
В данном модуле находятся все необходимые callback-функции для работы с api CW3 (которые вызываются непосредственно
командами в бота, остальные же функции находятся прямо в библиотеке)
"""

from castle_files.libs.api import CW3API
from castle_files.libs.player import Player
from castle_files.libs.guild import Guild
from castle_files.bin.stock_service import get_equipment_by_code, get_equipment_by_name
from castle_files.libs.bot_async_messaging import MAX_MESSAGE_LENGTH

from castle_files.bin.stock import get_item_name_by_code
from castle_files.bin.reports import count_battle_time, count_battle_id
from castle_files.bin.service_functions import get_time_remaining_to_battle

from castle_files.work_materials.globals import conn, SUPER_ADMIN_ID, castles, MID_CHAT_ID, dispatcher

from config import cwuser, cwpass

import time
import logging
import traceback
import threading
import copy
import datetime

import re

MAX_PLAYERS_AUTO_UPDATE_PER_SECOND = 2
GUILD_UPDATE_INTERVAL_SECONDS = 20


cwapi = CW3API(cwuser, cwpass)


def start_api():
    """
    Функция запуска апи
    """
    cwapi.start()


def auth(bot, update):
    """
    Функция авторизации API CW3 (команда /auth)
    """
    cwapi.request_auth_token(update.message.from_user.id)
    bot.send_message(chat_id=update.message.chat_id, text="Пришлите форвард сообщения, полученного от @ChatWarsBot.\n"
                                                          "Если ничего не пришло, то попробуйте ещё раз позже.")


def grant_auth_token(bot, update):
    """
    Функция обработки пересланного сообщения от чв с кодом авторизации АПИ
    """
    mes = update.message
    code = re.match("Code (\\d+) to authorize", mes.text)
    if code is None:
        bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка.")
        return
    code = int(code.group(1))
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    request_id, token = player.api_info.get("requestId"), player.api_info.get("token")
    if request_id is not None and token is not None:
        cwapi.grant_additional_operation(mes.from_user.id, request_id, code, player=player)
    else:
        cwapi.grant_token(mes.from_user.id, code)


def update(bot, update):
    """
    Запрос обновления профиля (команда /update)
    """
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    try:
        cwapi.update_player(mes.from_user.id, player=player)
        cwapi.update_stock(mes.from_user.id, player=player)
        try:
            gear_access = "gear" in player.api_info.get("access")
        except (TypeError, IndexError):
            gear_access = False
        if gear_access is False:
            cwapi.auth_additional_operation(mes.from_user.id, "GetGearInfo", player=player)
            bot.send_message(chat_id=mes.chat_id,
                             text="Для возможности обновления информации о снаряжении, пожалуйста, "
                                  "Пришлите форвард сообщения, полученного от @ChatWarsBot.")
        else:
            cwapi.update_gear(mes.from_user.id, player=player)
    except RuntimeError:
        bot.send_message(chat_id=mes.chat_id, text="Ошика. Проверьте наличие доступа у бота. "
                                                   "Возможно, стоит сделать /auth ещё раз.")
        return
    bot.send_message(chat_id=mes.chat_id, text="Запрошено обновление профиля. В скором времени данные будут обновлены.")


def update_stock(bot, update):
    """
    Запрос обновления стока (команда /update_stock)
    """
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    token = player.api_info.get("token") if player.api_info is not None else None
    if token is None:
        auth(bot, update)
        return
    cwapi.update_stock(player.id, player=player)
    bot.send_message(chat_id=mes.chat_id, text="Запрошено обновление стока. В скором времени данные будут обновлены.")


def update_guild(bot, update):
    """
    Запрос обновления гильдии (команда /update_guild)
    """
    mes = update.message
    try:
        cwapi.update_guild_info(mes.from_user.id)
    except RuntimeError:
        bot.send_message(chat_id=mes.chat_id, text="Ошика. Проверьте наличие доступа у бота. "
                                                   "Возможно, стоит сделать /auth ещё раз.")
        return
    bot.send_message(chat_id=mes.chat_id, text="Запрошено обновление гильдии. В скором времени данные будут обновлены.")


def get_player_with_api_access_from_guild(guild: Guild):
    """
    Функция, возвращающая человека гильдии, который давал доступ к апи (для обновления гильдии)
    :param guild: Guild
    :return: Int (player.id) or None
    """
    # for player_id in guild.members:
    #     player = Player.get_player(player_id)
    #     token = player.api_info.get("token")
    #     if token is not None:
    #         return player
    players_with_api_ids = guild.api_info.get('api_players') or []
    player_id = players_with_api_ids[0] if players_with_api_ids else None
    return player_id


def check_guilds_api_access(bot=None, job=None):
    """
    Проверка наличия доступа к АПИ у зарегистрированных гильдий.
    Вызывается отложенно, выполняется в фоне.
    :param bot: Bot
    :param job: Job
    :return: None
    """
    if job is None:
        reset = False
    else:
        try:
            reset = job.context.get("reset") or False
        except Exception:
            reset = False
    cursor = conn.cursor()
    if reset:
        logging.info("Clearing data about players with guilds API access")
        request = "update guilds set api_info = (api_info::jsonb - 'api_players')"
        cursor.execute(request)
    logging.info("Checking API access for guilds")
    request = "select guild_id from guilds where (api_info -> 'api_players') is null or " \
              "(api_info -> 'api_players')::text = '[]'::text"
    cursor.execute(request)
    rows = cursor.fetchall()
    if not rows:
        logging.info("All guilds have data about players with API access")
        return
    for row in rows:
        guild = Guild.get_guild(guild_id=row[0])
        search_for_players_with_api_access(guild)
    logging.info("Information about players with API access requested")


def search_for_players_with_api_access(guild: Guild):
    """
    Запрашивает обновление всех игроков гильдии.
    Если получен конкретный ответ, запоминает, что у игрока гильдии есть доступ к обновлению информации о ней.
    :param guild: Guild
    :return: None
    """
    logging.info("Requesting information about {} players with API access".format(guild.tag))
    # dispatcher.bot.send_message(chat_id=SUPER_ADMIN_ID, text="Обновляю данные о доступе к АПИ у {}".format(guild.tag))
    guild.api_info.update({"api_players": []})
    for player_id in guild.members:
        player = Player.get_player(player_id)
        token = player.api_info.get("token")
        if token is not None:
            cwapi.update_guild_info(player.id, player)
    guild.update_to_database(need_order_recashe=False)


def players_update_monitor():
    """
    Выполняется на всём протяжении функционирования бота. Раз в секунду запрашивает обновление
    MAX_PLAYERS_AUTO_UPDATE_PER_SECOND профилей игроков, ранее всего обновлявших свои профили.
    Раз в GUILD_UPDATE_INTERVAL_SECONDS секунд вызывает обновление гильдии, которая не обновлялась дольше всего.
    :return: None
    """
    cursor = conn.cursor()
    time.sleep(7)

    check_guilds_api_access()
    logging.info("Started updating profiles")
    i = 0
    while True:
        try:
            i += 1
            if not cwapi.active:
                return 0
            time_to_battle = get_time_remaining_to_battle()
            if time_to_battle < datetime.timedelta(minutes=30) or \
                    time_to_battle > datetime.timedelta(minutes=30, hours=7):
                time.sleep(1)
                continue
            if i % GUILD_UPDATE_INTERVAL_SECONDS == 0:
                # Обновление гильдии
                request = "select guild_id from guilds order by last_updated nulls first"
                cursor.execute(request)
                rows = cursor.fetchall()
                guild, player_id = None, None
                for row in rows:
                    guild_id = row[0]
                    guild = Guild.get_guild(guild_id=guild_id)
                    player_id = get_player_with_api_access_from_guild(guild)
                    if player_id is not None:
                        break
                if guild is None or player_id is None:
                    logging.error("No guild to update")
                    continue
                cwapi.update_guild_info(player_id)
                guild.api_info.update()
                logging.debug("Updating {} through CW3 API".format(guild.tag))

            request = "select id from players where api_info -> 'token' is not null order by last_updated limit %s"
            cursor.execute(request, (MAX_PLAYERS_AUTO_UPDATE_PER_SECOND,))
            row = cursor.fetchone()
            while row is not None:
                if row is None:
                    logging.error("Request is None in players_update_monitor")
                    return 0
                player = Player.get_player(row[0])
                cwapi.update_player(player.id, player=player)
                logging.debug("Updating {} through CW3 API".format(player.nickname))
                if not cwapi.active:
                    return 0
                access = player.api_info.get("access")
                if access is not None and "gear" in access:
                    cwapi.update_gear(player.id, player=player)
                row = cursor.fetchone()
            time.sleep(1)
        except Exception:
            logging.error(traceback.format_exc())


def repair_comparator(shop: dict, castle: str):
    """
    Компаратор для лавок с починкой и ремонтом.
    Лавки с замком игрока (castle) располагаются в самом конце (в самом низу сообщения).
    Общая сортировка происходит по цене починки
    :param shop: Словавь с описанием лавки, полученный от API
    :param castle: Замок игрока (строка, состоящая из одного символа)
    :return:
    """
    shop_castle = shop.get("ownerCastle")
    gold = shop.get("maintenanceCost")
    if shop_castle == castle:
        return -1000 + gold
    return gold


def ws_comparator(shop, castle):
    """
    Аналогично компаратору для починки, но сортировка происходит по количеству маны
    :param shop: Словавь с описанием лавки, полученный от API
    :param castle: Замок игрока (строка, состоящая из одного символа)
    :return:
    """
    shop_castle = shop.get("ownerCastle")
    mana = shop.get("mana")
    if shop_castle == castle:
        return -100000 + mana
    return mana


def repair(bot, update):
    """
    Показывает список лавок с открытым обслуживанием (команда /repair)
    """
    mes = update.message
    shops = cwapi.api_info.get("shops")
    if shops is None or not shops:
        bot.send_message(chat_id=mes.chat_id, text="Нет данных о магазинах. Ожидайте обновления.")
        return
    player = Player.get_player(mes.from_user.id)
    player_castle = player.castle if player is not None else '🖤'
    sh = []
    for shop in shops:
        if shop.get("maintenanceEnabled"):
            sh.append(shop)
    sh.sort(key=lambda x: repair_comparator(x, player_castle), reverse=True)

    response = "Доступные магазины для обслуживания:\n"
    castle_stage = sh[0].get("ownerCastle") if sh else '🖤'
    for shop in sh:
        castle, link, gold, mana, discount, name = shop.get("ownerCastle"), shop.get("link"), shop.get("maintenanceCost"), \
                                             shop.get("mana"), shop.get("castleDiscount"), shop.get("name")
        if castle_stage != castle == player_castle:
            castle_stage = player_castle
            response += "\n"
        response += "{} <a href=\"https://t.me/share/url?url={}\">{}</a> 💰{} 💧{} {}" \
                    "\n".format(castle, "/ws_" + link, "/ws_" + link, gold, mana,
                                "🏰: -{}%".format(discount) if discount is not None else "")
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


def ws(bot, update):
    """
    Выполянет поиск на наличие товара в лавках (команда /ws ...)
    """
    mes = update.message
    find_item = mes.text.partition(" ")[2].lower()
    if len(find_item) <= 3:
        bot.send_message(chat_id=mes.chat_id, text="Минимальная длина запроса — 4 символа")
        return
    shops = cwapi.api_info.get("shops")
    if shops is None or not shops:
        bot.send_message(chat_id=mes.chat_id, text="Нет данных о магазинах. Ожидайте обновления.")
        return
    player = Player.get_player(mes.from_user.id)
    player_castle = player.castle if player is not None else '🖤'
    sh = []
    for shop in shops:
        offers = []
        for offer in shop.get("offers"):
            name = offer.get("item")
            if find_item in name.lower():
                offers.append(offer)
        if offers:
            cur_shop = copy.deepcopy(shop)
            cur_shop.update({"offers": offers})
            sh.append(cur_shop)
    if not sh:
        bot.send_message(chat_id=mes.chat_id, text="Магазинов с этим предметом в продаже не найдено")
        return
    sh.sort(key=lambda x: ws_comparator(x, player_castle), reverse=True)
    pl_castle_flag = False
    response = "<b>Доступные магазины:</b>\n"
    for shop in sh:
        castle = shop.get("ownerCastle")
        if castle == player_castle:
            if not pl_castle_flag:
                pl_castle_flag = True
                response += "---------------------------------\n"
        response += "<a href=\"https://t.me/share/url?url=/ws_{}\">{}{} 💧{}</a>\n" \
                    "".format(shop.get("link"), castle, shop.get("ownerName"), shop.get("mana"))
        if 'full' in mes.text:
            response += "/ws_{}\n".format(shop.get("link"))
        for offer in shop.get("offers"):
            response += "<em>{}, 💧{} 💰{}</em>\n".format(offer.get("item"), offer.get("mana"), offer.get("price"))
        response += "\n"
    bot.send_message(chat_id=mes.from_user.id, text=response, parse_mode='HTML')


def ws_with_code(bot, update):
    code = re.match("/ws_(\\w+)", update.message.text)
    if code is None:
        bot.send_message(chat_id=update.message.chat_id, text="Неверный синтаксис")
        return
    code = code.group(1)
    eq = get_equipment_by_code(code)
    if eq is None:
        bot.send_message(chat_id=update.message.chat_id, text="Экипировка не найдена.")
        return
    shops = eq.get_quality_shops()
    shops.sort(key=lambda sh: (sh.is_open(), sh.qualityCraftLevel, -sh.get_offer(eq.name).get("price")),
               reverse=True)

    res = ""
    closed = False
    mana = None
    for shop in shops:
        if not shop.is_open() and closed is False:
            closed = True
            res += "\nСейчас закрыты:\n"
        offer = shop.get_offer(eq.name)
        mana = offer.get("price")
        res += shop.format_offer(eq, offer)

    result = "Лавки не найдены" if res == "" else "Открытые лавки с {} (нужно {}💧)\n".format(eq.name, mana) + res

    bot.send_message(chat_id=update.message.chat_id, text=result,
                     parse_mode='HTML')



def stock(bot, update):
    """
    Выводит сток игрока (команда /stock)
    """
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    is_guild = False
    guild = None
    if 'guild' in mes.text or mes.text.startswith("/g_stock"):
        is_guild = True
        if player.guild is None:
            bot.send_message(chat_id=mes.from_user.id,
                             text="Вы не состоите в гильдии. Попросите командира добавить вас")
            return
        guild = Guild.get_guild(guild_id=player.guild)
        if guild is None:
            bot.send_message(chat_id=mes.from_user.id,
                             text="Вы не состоите в гильдии. Попросите командира добавить вас")
            return
        curr_stock = guild.api_info.get("stock")
        if curr_stock is None:
            bot.send_message(chat_id=mes.from_user.id,
                             text="Отсутствует информация о стоке. Для обновления нажмите /update_guild. "
                             "Требуется доступ к API.")
            return
    else:
        if not player.stock:
            bot.send_message(chat_id=mes.chat_id,
                             text="Отсутствует информация о стоке. Для обновления нажмите /update_stock. "
                                  "Требуется доступ к API.")
            return
        curr_stock = player.stock
    """
    res:   Ресурсы
    alch:  Травы
    misc:  Корм, Зелья, свитки
    other: Остальное
    """
    if 'res' in mes.text:
        stage = [0]
    elif 'alch' in mes.text:
        stage = [1]
    elif 'misc' in mes.text:
        stage = [2]
    elif 'equip' in mes.text:
        stage = [3]
    elif 'other' in mes.text:
        stage = [5]
    else:
        stage = []
    response = "<b>📦Склад:\nРесурсы:</b>\n"
    stages = {0: {"name": "Ресурсы:", "to_achieve": lambda code: True},
              1: {"name": "Травы", "to_achieve": lambda code: not code.isdigit() or int(code) >= 39},
              2: {"name": "Корм:", "to_achieve": lambda code: not code.isdigit() or int(code) >= 618},
              3: {"name": "Экипировка и крафт:", "to_achieve": lambda code: not code.isdigit()},
              4: {"name": "Зелья:", "to_achieve": lambda code: not code.isdigit() and code[0] not in ["k", "r", "w"]},
              5: {"name": "Другое:", "to_achieve": lambda code: not code.isdigit() and code[0] != "p"},
              6: {"name": "КОНЕЦ", "to_achieve": lambda code: False}
              }
    stage_num = 0
    next_stage = stages.get(stage_num + 1)
    total_gold = 0
    prices = cwapi.api_info.get("prices") or {}
    for code, count in list(curr_stock.items()):
        stage_changed = False
        new_response = ""
        while next_stage.get("to_achieve")(code):
            stage_changed = True
            stage_num += 1
            next_stage = stages.get(stage_num + 1)
        if stage and stage_num not in stage:
            continue
        if stage_changed:
            new_response += "\n<b>{}</b>\n".format(stages.get(stage_num).get("name"))
        price = prices.get(code) or "❔"
        if len(code) > 4:
            name = code
        else:
            name = get_item_name_by_code(code)
        new_response += "<a href=\"https://t.me/share/url?url=/{}\">{} x {}</a> ≈ {}" \
                        "\n".format("{} {} {}".format("g_withdraw" if is_guild else "g_deposit", code, count),
                                    "{} | {}".format(code, name) if code != name else
                                    name, count, "<b>{}</b>💰({}💰x{})".format(
                                    price * count, price, count) if isinstance(price, int) else price)
        total_gold += price * count if isinstance(price, int) else 0
        if len(response + new_response) > MAX_MESSAGE_LENGTH:
            bot.group_send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
            response = ""
        response += new_response
    response += "\n\n<b>Всего: {}💰</b>\n".format(total_gold)
    if is_guild and guild is not None:
        stock_size, stock_limit = guild.api_info.get("stock_size"), guild.api_info.get("stock_limit")
        if stock_size is not None and stock_limit is not None:
            response += "📦Сток гильдии: <b>{}</b> / <b>{}</b>\n".format(stock_size, stock_limit)
        response += "Последнее обновление: <em>{}</em>".format(guild.last_updated.strftime(
                "%d/%m/%y %H:%M") if guild.last_updated is not None else "Неизвестно")
    elif not is_guild:
        response += "Последнее обновление: <em>{}</em>\n".format(player.api_info.get("stock_update") or "Неизвестно")
    bot.group_send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
    bot.send_message_group(mes.chat_id)


def autospend_gold(bot, update):
    """
    Функция для автослива голды... Не дописана, не работает
    """
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    access = player.api_info.get("access") or []
    if "wtb" not in access:
        cwapi.auth_additional_operation(mes.from_user.id, "TradeTerminal", player=player)
        bot.send_message(chat_id=mes.chat_id,
                         text="Для возможности покупать ресурсы на бирже, пожалуйста, "
                              "пришлите форвард сообщения, полученного от @ChatWarsBot.")
        return
    return

    parse = re.search(" (.*) (\\d+)")


def grassroots_update_players(bot, job):
    """
    Запрос на обновление профилей всех игроков (на текущий момент обновляется только сток(grassroots_update_stock),
    профили и так обновляются постоянно)
    """
    cursor = conn.cursor()
    request = "select id, api_info from players where api_info ->> 'token' is not null"
    cursor.execute(request)
    row = cursor.fetchone()
    count = 0
    while row is not None:
        # cwapi.update_player(row[0])
        cwapi.update_stock(row[0])
        access = row[1].get("access") or []
        gear_access = "gear" in access
        if gear_access or False:
            cwapi.update_gear(row[0])
        count += 1
        row = cursor.fetchone()
    bot.send_message(chat_id=SUPER_ADMIN_ID, text="Запрошено обновление профилей <b>{}</b> игроков".format(count),
                     parse_mode='HTML')


def grassroots_update_stock(bot, job):
    """
    Запрос на обновление стока всех игроков, и гильдий
    """
    print("starting updating")
    change_send = job.context.get("change_send") or False
    cursor = conn.cursor()
    request = "select id, api_info from players where api_info ->> 'token' is not null"
    cursor.execute(request)
    row = cursor.fetchone()
    count = 0
    count_all = 0
    while row is not None:
        player = Player.get_player(row[0], notify_on_error=False, new_cursor=cursor)
        count_all += 1
        player.api_info.update({"change_stock_send": change_send})
        player.update()
        count += 1 if change_send else 0
        cwapi.update_stock(player.id, player=player)
        row = cursor.fetchone()
    bot.send_message(chat_id=SUPER_ADMIN_ID,
                     text="Запрошено обновление {} стоков, установлено {} флагов для отправки"
                          "".format(count_all, count))

    # Обновление стока гильдий
    request = "select guild_id from guilds where (api_info -> 'api_players') is not null and " \
              "json_array_length(api_info -> 'api_players') > 0"
    cursor.execute(request)
    rows = cursor.fetchall()
    count, count_all = 0, 0
    for row in rows:
        guild = Guild.get_guild(guild_id=row[0])
        player_id = guild.api_info.get("api_players")[0]
        cwapi.update_guild_info(player_id)
        logging.info("Requested {} update".format(guild.tag))
        count_all += 1
        if change_send:
            guild.api_info.update({"change_stock_send": True})
            guild.update_to_database(need_order_recashe=False)
            count += 1
    bot.send_message(chat_id=SUPER_ADMIN_ID,
                     text="Запрошено обновление {} гильдий, установлено {} флагов для отправки"
                          "".format(count_all, count))


def update_stock_for_fails(bot, job):
    """
    Если по какой-то причине ответ от API получен не был для определённых игроков, то выполняется повторный запрос
    """
    cursor = conn.cursor()
    request = "select id, api_info from players where api_info ->> 'token' is not null and (api_info ->> " \
              "'change_stock_send')::boolean is true"
    cursor.execute(request)
    row = cursor.fetchone()
    while row is not None:
        player = Player.get_player(row[0], notify_on_error=False, new_cursor=cursor)
        cwapi.update_stock(player.id, player=player)
        row = cursor.fetchone()

    request = "select guild_id from guilds where (api_info -> 'change_stock_send')::text::boolean is true"
    cursor.execute(request)
    rows = cursor.fetchall()
    count_all = 0
    for row in rows:
        guild = Guild.get_guild(guild_id=row[0])
        api_players = guild.api_info.get("api_players")
        # if len(api_players) > 0:  # Сомнительно, часто гильдии не обновляются из-за багов АПИ
        #     api_players.pop(0)
        if not api_players:
            # guild.api_info.clear()
            bot.send_message(chat_id=SUPER_ADMIN_ID, parse_mode='HTML',
                             text="Гильдию <b>{}</b> невозможно обновить - нет игроков с доступом к АПИ."
                                  "".format(guild.tag))
            continue
        player_id = api_players[0]
        cwapi.update_guild_info(player_id)
        logging.info("Requested {} update".format(guild.tag))
        count_all += 1
    if count_all > 0:
        bot.send_message(chat_id=SUPER_ADMIN_ID, parse_mode='HTML',
                         text="Повторно запрошено обновление <b>{}</b> гильдий, игроки с доступом к АПИ подвинуты"
                              "".format(count_all))
    if len(rows) > 0:
        bot.send_message(chat_id=SUPER_ADMIN_ID, text="Начата проверка доступа к АПИ у гильдий")
        check_guilds_api_access(bot, None)


def send_potion_stats(bot, job):
    """
    Отправка статистики покупки банок по замкам в чат МИДа
    """
    clear = job.context[0]
    potions = cwapi.api_info.get("potions_info")
    if potions is None:
        bot.send_message(chat_id=SUPER_ADMIN_ID, text="Ошибка. Информация по банкам отсутствует.")
        return
    battle_id = count_battle_id(None) + 1
    response = "Закупки замков по банкам к битве № <code>{}</code> ({}):\n\n<em>total | vial / potion / bottle</em>" \
               "\n\n".format(battle_id, count_battle_time(battle_id).strftime("%d/%m/%y %H:%M:%S"))
    for category, pot in list(potions.items()):
        total_potions = {}
        response += "<b>{}:</b>\n".format(category)
        types = ["vial", "potion", "bottle"]
        for type in types:
            potion = pot.get(type)
            if potion is None:
                potion = {k: 0 for k in castles}
            for castle in castles:
                count = potion.get(castle) or 0
                pt = total_potions.get(castle)
                if pt is None:
                    pt = [0, ""]
                    total_potions.update({castle: pt})
                # count, res = pt
                pt[1] += "<code>{:>2}</code> / ".format(count)
                pt[0] += count
        total_potions = {k: v for k, v in sorted(list(total_potions.items()), key=lambda x: x[1][0], reverse=True)}
        for castle, pot in list(total_potions.items()):
            if pot[0] == 0:
                continue
            response += "{}: <code>{:>2}</code> | {}\n".format(castle, pot[0], pot[1][:-1])
    bot.send_message(chat_id=MID_CHAT_ID, text=response, parse_mode='HTML')
    if clear:
        cwapi.api_info.update({"potions_info": {}})


