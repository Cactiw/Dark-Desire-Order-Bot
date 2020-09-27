from castle_files.work_materials.globals import cursor, job, dispatcher, SUPER_ADMIN_ID, CENTRAL_SQUARE_CHAT_ID, \
    moscow_tz, conn, utc, castles, emodji_to_castle_names, WORLDTOP_CHANGES_CHANNEL_ID, SON_CHAT_ID
from castle_files.bin.service_functions import get_time_remaining_to_battle, check_access, get_admin_ids, \
    count_battle_id, count_battles_in_this_week, plan_work
from castle_files.bin.reports import count_battle_time

from castle_files.libs.guild import Guild
from castle_files.libs.player import Player
from castle_files.libs.bot_async_messaging import MAX_MESSAGE_LENGTH

from castle_files.work_materials.globals import dispatcher
from castle_files.bin.telethon_script import castles_stats_queue
from castle_files.bin.api import check_guilds_api_access
from castle_files.bin.alliances import parse_alliance_battle_results

from telegram.error import TelegramError
from telegram import ChatPermissions

import re
import time
import datetime
import logging
import copy
import traceback


ping_by_chat_id = {}

ranger_aiming_minutes = [0, 180, 165, 150, 135, 120, 105, 95, 85, 75, 65, 60, 55, 50, 45, 40]

MAX_TOP_PLAYERS_SHOW = 5
MAX_TOP_PLAYERS_SHOW_WEEK = 10


def load_worldtop(battle_id: int = None) -> dict:
    """
    Загружает /worldtop после битвы с battle_id
    :return: { str: int }
    """
    if battle_id is None:
        battle_id = count_battle_id()
    request = "select ferma, amber, oplot, rassvet, tortuga, night, skala from worldtop where battle_id = %s"
    cursor.execute(request, (battle_id,))
    row = cursor.fetchone()
    if not row:
        return {}
    worldtop = {k: v for k, v in zip(castles, row)}
    sort_worldtop(worldtop)
    return worldtop


def save_worldtop(worldtop: dict, battle_id: int = None):
    try:
        if battle_id is None:
            battle_id = count_battle_id()
        request = "insert into worldtop(battle_id, "
        args = [battle_id]
        for k, v in list(worldtop.items()):
            request += "{}, ".format(emodji_to_castle_names.get(k))
            args.append(v)
        request = request[:-2] + ')' + 'values(%s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(request, args)
    except Exception:
        logging.error(traceback.format_exc())


def get_castle_place_in_worldtop(worldtop: dict, castle: str) -> int:
    place = 1
    for k, v in list(worldtop.items()):
        if k == castle:
            return place
        place += 1
    return None


def sort_worldtop(worldtop):
    t = dict(sorted(list(worldtop.items()), key=lambda x: x[1], reverse=True))
    worldtop.clear()
    for k, v in list(t.items()):
        worldtop.update({k: v})
    return worldtop



def parse_stats():
    data = castles_stats_queue.get()
    while data is not None:
        message_id = data.get("message_id")
        debug = data.get("debug", False)
        data = data.get("data")
        # logging.error("Got data in parse: {}".format(data))
        if 'Результаты сражений:' in data:
            # Результаты битвы замков
            if not debug:
                response_all = "Игроки, попавшие в топ:\n"
                for guild_id in Guild.guild_ids:
                    response = ""
                    guild = Guild.get_guild(guild_id=guild_id)
                    tag = guild.tag
                    for castle_results_string in data.split("\n\n"):
                        if tag in castle_results_string:
                            try:
                                attacked_castle = re.search('[🍁☘🖤🐢🦇🌹🍆]', castle_results_string).group(0)
                            except TypeError:
                                attacked_castle = "???"
                            nicknames_list = re.findall(".\\[{}\\][^🍁☘🖤🐢🦇🌹🍆🎖\n]+".format(tag), castle_results_string)
                            print(nicknames_list)
                            for nickname in nicknames_list:
                                if response == "":
                                    response = "Игроки, попавшие в топ:\n"
                                response += "{}{} <b>{}</b>\n".format("🛡️" if nickname[0] == attacked_castle else"⚔️",
                                                                      attacked_castle, nickname[:-1])

                                response_all += "{}{} <b>{}</b>\n".format("🛡️" if nickname[0] == attacked_castle else"⚔️",
                                                                          attacked_castle, nickname[:-1])

                    if response != "":
                        if guild.chat_id is None:
                            continue
                        dispatcher.bot.send_message(chat_id=guild.chat_id, text=response, parse_mode='HTML')
                if response_all != "Игроки, попавшие в топ:\n":
                    dispatcher.bot.send_message(chat_id=CENTRAL_SQUARE_CHAT_ID, text=response_all, parse_mode='HTML')
            worldtop_strings = data.split("\n\n")[-1].splitlines()
            worldtop = load_worldtop(battle_id=count_battle_id() - 1)
            old_worldtop = copy.deepcopy(worldtop)
            for string in worldtop_strings:
                parse = re.search("(.).* \\+(\\d+) 🏆 очков", string)
                if parse is None:
                    continue
                castle = parse.group(1)
                count = int(parse.group(2))
                score = worldtop.get(castle)
                score += count
                worldtop.update({castle: score})
                sort_worldtop(worldtop)
                logging.info("Worldtop updated: {}: {}".format(castle, count))
            save_worldtop(worldtop)
            if not debug:
                send_worldtop_update(old_worldtop, worldtop)
            logging.info("Worldtop at the end: {}".format(worldtop))
        elif data.startswith("🤝Headquarters news:") or data.startswith("🗺State of map:"):
            # Итоги штабов альянсов
            logging.info("Got alliance news")
            try:
                parse_alliance_battle_results(data, message_id, debug)
            except Exception:
                logging.error(traceback.format_exc())
        else:
            #  Сообщение о пиратстве
            response_by_tags = {}
            data = data.replace("Attackers:", "   🗡Атакующие:")
            data = data.replace("Defenders:", "   🛡Обороняющиеся:")
            guild_list = re.split("[⚔🛡] ..?Гильдия", data)
            for guild_str in guild_list:
                new_str = guild_str
                new_str = "{}".format('⚔️' if 'атакована' in new_str else '🛡') + new_str
                tags = re.findall("[🍁☘🖤🐢🦇🌹🍆](\\w+)", guild_str)
                tags = list(set(tags))
                for tag in tags:
                    new_str = new_str.replace(tag, "<b>{}</b>".format(tag))
                for tag in tags:
                    lst = response_by_tags.get(tag)
                    if lst is None:
                        lst = "Итоги гильдейских битв с вашим участием:\n\n"
                        response_by_tags.update({tag: lst})
                    lst += new_str + "\n"
                    response_by_tags.update({tag: lst})
                # dispatcher.bot.send_message(chat_id=SUPER_ADMIN_ID, text=guild_str, parse_mode='HTML')
            import json
            # logging.error("Guild list for parse_stats: {}".format(json.dumps(guild_list, indent=4, ensure_ascii=False)))
            logging.error("Response by tags: {}".format(json.dumps(response_by_tags, indent=4, ensure_ascii=False)))
            print(guild_list)
            print(json.dumps(response_by_tags, indent=4, ensure_ascii=False))
            for tag, string in list(response_by_tags.items()):
                guild = Guild.get_guild(guild_tag=tag)
                if guild is None:
                    continue
                dispatcher.bot.send_message(chat_id=guild.chat_id, text=string, parse_mode='HTML')
        data = castles_stats_queue.get()


def send_worldtop_update(old_worldtop: dict, worldtop: dict):
    send_chats = [SON_CHAT_ID]
    response = "Worldtop changes:\n"
    i = 0
    for k, v in list(worldtop.items()):
        i += 1
        change = v - old_worldtop.get(k)
        place_change = get_castle_place_in_worldtop(old_worldtop, k) - i
        response += "# <code>{}({}){}:{:>5}🏆(+{:>2})</code>\n".format(
            i, "{}{}".format("🔺" if place_change > 0 else "🔻" if place_change < 0 else "▪️",
                               # "+" if place_change > 0 else "-" if place_change < 0 else " ",
                               abs(place_change)),
            k, v, change)
    mes = dispatcher.bot.sync_send_message(chat_id=WORLDTOP_CHANGES_CHANNEL_ID, text=response, parse_mode='HTML')
    for chat_id in send_chats:
        dispatcher.bot.forward_message(chat_id=chat_id, from_chat_id=mes.chat_id, message_id=mes.message_id)



def show_worldtop(bot, update, args):
    battle_id = None
    if args:
        try:
            battle_id = int(args[0])
            if battle_id < 0:
                battle_id = count_battle_id() + battle_id
        except ValueError:
            pass
    worldtop = load_worldtop(battle_id=battle_id)
    if worldtop is None and battle_id is None:
        battle_id = count_battle_id()
        for i in range(6):
            worldtop = load_worldtop(battle_id - i)
            if worldtop is not None:
                break
    response = "Worldtop: {}\n".format("битва {}\n({}):".format(
        battle_id, count_battle_time(battle_id).strftime("%d/%m/%y %H:%M:%S")) if battle_id is not None else "")
    i = 1
    for k, v in list(worldtop.items()):
        response += "# {} {}: <code>{:>5}</code> 🏆 очков\n".format(i, k, v)
        i += 1
    bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML')


def guild_top_battles(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    if 'academy' in mes.text:
        guild = Guild.get_academy()
    else:
        guild = Guild.get_guild(player.guild)
    if guild is None:
        bot.send_message(chat_id=update.message.chat_id, text='Гильдейские топы доступны только членам гильдий.')
        return
    if not guild.check_high_access(player.id):
        bot.send_message(chat_id=update.message.chat_id,
                         text='Гильдейские топы доступны только командирам и замам гильдий.')
        return
    response = get_top_text(guild, 3)
    for text in response:
        bot.send_message(chat_id=mes.chat_id, text=text, parse_mode='HTML')


def get_top_text(guild, battles_for_count, max_players=None, curr_cursor=None) -> [str]:
    if max_players is None:
        max_players = 10000
    if curr_cursor is None:
        curr_cursor = cursor
    total_battles = count_battles_in_this_week()
    players = []
    for player_id in guild.members:
        player = Player.get_player(player_id, notify_on_error=False)
        if player is None:
            continue
        request = "select exp, gold, stock from reports where player_id = %s and battle_id >= %s"
        curr_cursor.execute(request, (player_id, count_battle_id(message=None) - battles_for_count + 1))  # За последние 3 битвы
        row = curr_cursor.fetchone()
        exp, gold, stock = 0, 0, 0
        while row is not None:
            exp += row[0]
            gold += row[1]
            stock += row[2]
            row = curr_cursor.fetchone()
        reports = player.get_reports_count()[0]
        players.append([player, exp, gold, stock, "{}/{} ({}%)".format(reports, total_battles, reports * 100 //
                                                                       total_battles)])
    ret = []
    response = "📈Топ <b>{}</b> за {} по битвам:\n".format(guild.tag, "день" if battles_for_count == 3 else "неделю")

    tops = ["🔥По опыту:", "💰По золоту:", "📦По стоку:", "⚔️Участие в битвах на этой неделе:"]
    for i, top in enumerate(tops):
        response += "\n<b>{}</b>\n".format(top)
        players.sort(key=lambda x: x[i + 1] if isinstance(x[i + 1], int) else int(x[i + 1].partition("/")[0]),
                     reverse=True)
        for j, elem in enumerate(players):
            if (j < max_players or j == len(players) - 1) or (i == (len(tops) - 1) and battles_for_count == 21):
                response += "{}){}{} — {}<code>{}</code>" \
                            "\n".format(j + 1, elem[0].castle,
                                        "{}{}".format(elem[0].nickname.partition("]")[2] if "]" in elem[0].nickname else
                                                      elem[0].nickname, '🎗' if elem[0].id == guild.commander_id else
                                                                        ""), top[0], elem[i + 1])
            elif j == max_players:
                response += "...\n"
            if len(response) > MAX_MESSAGE_LENGTH:
                ret.append(response)
                response = ""
    if response != "":
        ret.append(response)
    return ret


# Рассылка ежедневных топов по ги
def top_notify(bot, job):
    cursor = conn.cursor()
    for guild_id in Guild.guild_ids:
        guild = Guild.get_guild(guild_id=guild_id)
        if guild is None or guild.division == "Луки" or not guild.members:  # or guild.tag != 'СКИ':
            continue
        response = get_top_text(guild, 3, curr_cursor=cursor, max_players=MAX_TOP_PLAYERS_SHOW)
        if guild.settings is None or guild.settings.get("tops_notify") in [None, True]:
            for text in response:
                bot.send_message(chat_id=guild.chat_id, text=text, parse_mode='HTML')

    total_battles = count_battles_in_this_week()
    if total_battles >= 21:
        # Рассылка еженедельного топа
        for guild_id in Guild.guild_ids:
            guild = Guild.get_guild(guild_id=guild_id)
            if guild is None or guild.division == "Луки" or not guild.members:  # or guild.tag != 'СКИ':
                continue
            response = get_top_text(guild, 21, curr_cursor=cursor, max_players=MAX_TOP_PLAYERS_SHOW_WEEK)
            if guild.settings is None or guild.settings.get("tops_notify") in [None, True]:
                for text in response:
                    bot.send_message(chat_id=guild.chat_id, text=text, parse_mode='HTML')

    time.sleep(1)
    plan_top_notify()


# Рассылка с напоминанием о арене и крафте в чаты ги в 12 по мск
def arena_notify(bot, job):
    cursor = conn.cursor()
    for guild_id in Guild.guild_ids:
        guild = Guild.get_guild(guild_id=guild_id)
        if guild is None or guild.division == "Луки":
            continue
        if guild.settings is None or guild.settings.get("arena_notify") in [None, True]:
            bot.send_message(chat_id=guild.chat_id, text="Через час обнуление арен и дневного лимита опыта за крафт.")
    time.sleep(1)
    plan_arena_notify()


def plan_arena_notify():
    plan_work(arena_notify, 12, 0, 0)


def plan_top_notify():
    plan_work(top_notify, 19, 0, 0)


def notify_guild_attack(bot, update):
    mes = update.message
    remaining_time = get_time_remaining_to_battle()
    forward_message_date = utc.localize(mes.forward_date).astimezone(tz=moscow_tz).replace(tzinfo=None)
    if forward_message_date - datetime.datetime.now() > datetime.timedelta(minutes=2):
        return 0
    if remaining_time > datetime.timedelta(minutes=30):
        pass
        return 0
    ready_to_battle = mes.text.count("[⚔]") + mes.text.count("[🛡]")
    sleeping = mes.text.count("[🛌]") + mes.text.count("[⚒]")
    response = "<b>{0}</b>\nГотово к битве: <b>{1}</b>\nНе готово к битве, но занято <b>{2}</b>\n" \
               "Спит: <b>{3}</b>\n\nВремя до битвы: {4}\n".format(mes.text.splitlines()[0], ready_to_battle,
                                                                  mes.text.count("\n") - ready_to_battle - sleeping,
                                                                  sleeping, ":".join(str(remaining_time).partition(".")[0].split(":")[0:3]))
    request = "select guild_id from guilds where chat_id = %s"
    cursor.execute(request, (mes.chat_id,))
    row = cursor.fetchone()
    if row is None:
        return
    guild = Guild.get_guild(guild_id=row[0])
    set = guild.settings.get("battle_notify") if guild.settings is not None else True
    if guild is None or set is False:
        return
    if mes.chat_id != guild.chat_id:
        return
    if mes.from_user.id not in get_admin_ids(bot, chat_id=mes.chat_id) and not check_access(mes.from_user.id):
        bot.send_message(chat_id=mes.chat_id, text="Доступ только у админов", parse_mode='HTML',
                         reply_to_message_id=mes.message_id)
        return
    do_not_ready = []
    sleeping = []
    for string in mes.text.splitlines()[1:]:
        if not ("[⚔]" in string or "[🛡]" in string):
            nickname = string.partition("]")[2][1:]
            do_not_ready.append(nickname)
            if "[🛌]" in string or "[⚒]" in string:
                sleeping.append(nickname)

    in_dict_do_not_ready = []
    in_dict_sleeping = []
    ping_dict = {"do not ready": in_dict_do_not_ready, "sleeping": in_dict_sleeping}
    for player_id in guild.members:
        player = Player.get_player(player_id, notify_on_error=False)
        if player is None:
            continue
        db_nickname = player.nickname.partition("]")[2]
        if db_nickname in do_not_ready:
            in_dict_do_not_ready.append(player.username)
            if db_nickname in sleeping:
                in_dict_sleeping.append(player.username)

    ping_by_chat_id.update({mes.chat_id : ping_dict})
    response += "Пингануть тех, кто спит: /notify_guild_sleeping\n" \
                "Пингануть всех, кто не готов: /notify_guild_not_ready"
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode = 'HTML')


def notify_guild_to_battle(bot, update):
    mes = update.message
    chat_dict = ping_by_chat_id.get(mes.chat_id)
    if chat_dict is None:
        return
    if mes.from_user.id not in get_admin_ids(bot, chat_id=mes.chat_id) and not check_access(mes.from_user.id):
        bot.send_message(chat_id=mes.chat_id, text="Доступ только у админов", parse_mode='HTML')
        return
    if mes.text.partition("@")[0].split("_")[2] == "sleeping":
        target_list = chat_dict.get("sleeping")
    else:
        target_list = chat_dict.get("do not ready")
    i = 0
    response = ""
    for username in target_list:
        if i >= 4:
            response += "\n БИТВА!"
            bot.send_message(chat_id=mes.chat_id, text = response)
            response = ""
            i = 0
        response += "@{0} ".format(username)
        i += 1
    response += "\n БИТВА!"
    bot.send_message(chat_id=mes.chat_id, text=response)


def mute(bot, update, args):
    mes = update.message
    if (mes.from_user.id != SUPER_ADMIN_ID) and (mes.from_user.id not in get_admin_ids(bot, chat_id=mes.chat_id)):
        return
    if mes.reply_to_message is None:
        return
    if mes.reply_to_message.from_user.id == SUPER_ADMIN_ID:
        bot.send_message(chat_id=update.message.chat_id, text='Неа -__-')
        return
    if not args:
        return
    current = time.time()
    try:
        ban_for = (float(args[0]) * 60)
    except ValueError:
        bot.send_message(chat_id=update.message.chat_id, text='Неверный синтаксис')
        return
    current += ban_for
    try:
        bot.restrictChatMember(chat_id=mes.chat_id, user_id = mes.reply_to_message.from_user.id, until_date=current,
                               permissions=ChatPermissions(can_send_other_messages=False, can_send_messages=False))
    except TelegramError:
        bot.send_message(chat_id=update.message.chat_id, text='Ошибка. Проверьте, что бот имеет требуемые права.')
        return
    bot.send_message(chat_id=update.message.chat_id, text='Выполнено!', reply_to_message_id=update.message.message_id)
    return


def unrestrict(bot, update, args):
    if update.message.from_user.id != SUPER_ADMIN_ID:
        return
    chat_id = int(args[0])
    current = time.time()
    current += 30
    bot.restrictChatMember(chat_id=chat_id, user_id=SUPER_ADMIN_ID, until_date=current,
                           permissions=ChatPermissions(can_send_other_messages=True, can_send_messages=True))
    bot.send_message(chat_id=SUPER_ADMIN_ID, text="Ограничения сняты")
    # dispatcher.bot.unban_chat_member(chat_id=chat_id, user_id=SUPER_ADMIN_ID)


def send_message_to_chat(bot, update):
    mes = update.message
    if mes.from_user.id != SUPER_ADMIN_ID:
        return
    pattern = re.compile("/\\S+ (-?\\d+) (.+)", re.DOTALL)
    parse = re.match(pattern, mes.text)
    if parse is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис. Образец: /send_message_to_chat {chat_id} {text}")
        return
    chat_id, text = int(parse.group(1)), parse.group(2)
    bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')


def ranger_notify(bot, job):
    context = job.context
    response = "Поднимай свой лук, <b>{0}</b>\n@{1}".format(context[1], context[0])
    bot.send_message(chat_id=context[2], text=response, parse_mode='HTML')


def rangers_notify_start(bot, update):
    cursor = conn.cursor()
    time_to_battle = get_time_remaining_to_battle()
    print("time_to_battle", time_to_battle)
    try:
        callback_chat_id = update.message.chat_id
    except AttributeError:
        try:
            callback_chat_id = int(update)
        except TypeError:
            return
    count = 0
    request = "select id from players where class_skill_lvl is not NULL"
    cursor.execute(request)
    row = cursor.fetchone()
    while row is not None:
        player = Player.get_player(row[0])
        if player is None:
            row = cursor.fetchone()
            continue
        if player.settings is not None and player.settings.get("rangers_notify") is False:
            row = cursor.fetchone()
            continue
        guild = Guild.get_guild(guild_id=player.guild)
        if guild is None:
            row = cursor.fetchone()
            continue
        telegram_username = player.username
        username = player.nickname
        class_skill_lvl = player.class_skill_lvl
        context = [telegram_username, username, guild.chat_id]
        print(class_skill_lvl)
        time_to_aim_mins = ranger_aiming_minutes[class_skill_lvl] if \
            class_skill_lvl < len(ranger_aiming_minutes) else 40

        time_to_aim = datetime.timedelta(minutes=time_to_aim_mins)
        print("time_to_aim", time_to_aim)
        time_to_notify = time_to_battle - time_to_aim - datetime.timedelta(minutes=1)
        print(time_to_notify)
        # time_to_notify = datetime.timedelta(minutes=1)    # TEST
        if time_to_notify >= datetime.timedelta(minutes=0):
            job.run_once(ranger_notify, time_to_notify, context=context)

        row = cursor.fetchone()
        count += 1
    cursor.close()
    bot.send_message(chat_id=callback_chat_id, text="Запланировано оповещение <b>{0}</b> бедных лучников".format(count),
                     parse_mode='HTML')
