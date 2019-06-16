from castle_files.work_materials.globals import cursor, job, dispatcher, SUPER_ADMIN_ID, CENTRAL_SQUARE_CHAT_ID, \
    moscow_tz, local_tz, conn
from castle_files.bin.service_functions import get_time_remaining_to_battle, check_access, get_admin_ids, \
    count_battle_id, count_battles_in_this_week

from castle_files.libs.guild import Guild
from castle_files.libs.player import Player

from castle_files.work_materials.globals import dispatcher
from castle_files.bin.telethon_script import castles_stats_queue

from telegram.error import TelegramError

import re
import time
import datetime


ping_by_chat_id = {}

ranger_aiming_minutes = [0, 180, 165, 150, 135, 120, 105, 95, 85, 75, 65, 60, 55, 50, 45, 40]

MAX_TOP_PLAYERS_SHOW = 5


def parse_stats():
    data = castles_stats_queue.get()
    while data:
        response_all = "Игроки, попавшие в топ:\n"
        for castle_results_string in data.split("\n\n"):
            for guild_id in Guild.guild_ids:
                guild = Guild.get_guild(guild_id=guild_id)
                tag = guild.tag
                if tag in castle_results_string:
                    response = ""
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
                        dispatcher.bot.send_message(chat_id=guild.chat_id, text=response, parse_mode='HTML')
        if response_all != "Игроки, попавшие в топ:\n":
            dispatcher.bot.send_message(chat_id=CENTRAL_SQUARE_CHAT_ID, text=response_all, parse_mode='HTML')
        data = castles_stats_queue.get()


# Запускается один раз при старте бота; осуществляет планирование всех рассылок, привязанных ко времени и
# прочие задания.
def plan_daily_tasks():
    plan_arena_notify()
    plan_top_notify()


# Функция, планирующая работу на конкретное время сегодня, или завтра, если это время сегодня уже прошло
def plan_notify(callback, hour, minute, second):
    time_to_send = datetime.time(hour=hour, minute=minute, second=second)
    time_now = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None).time()
    day_to_send = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None).date()
    date_to_send = datetime.datetime.combine(day_to_send, datetime.time(hour=0))
    if time_to_send < time_now:
        date_to_send += datetime.timedelta(days=1)
    date_to_send = date_to_send.date()
    send_time = datetime.datetime.combine(date_to_send, time_to_send)  # Время в мск
    send_time = moscow_tz.localize(send_time).astimezone(tz=local_tz).replace(tzinfo=None)  # Локальное время
    job.run_once(callback, when=send_time, context=[])


def plan_arena_notify():
    plan_notify(arena_notify, 12, 0, 0)


def plan_top_notify():
    plan_notify(top_notify, 18, 0, 0)


# Рассылка ежедневных топов по ги
def top_notify(bot, job):
    cursor = conn.cursor()
    total_battles = count_battles_in_this_week()
    for guild_id in Guild.guild_ids:
        guild = Guild.get_guild(guild_id=guild_id)
        if guild is None or guild.division == "Луки" or not guild.members:  # or guild.tag != 'СКИ':
            continue
        players = []
        for player_id in guild.members:
            player = Player.get_player(player_id, notify_on_error=False)
            if player is None:
                continue
            request = "select exp, gold, stock from reports where player_id = %s and battle_id >= %s"
            cursor.execute(request, (player_id, count_battle_id(message=None) - 2))  # За последние 3 битвы
            row = cursor.fetchone()
            exp, gold, stock = 0, 0, 0
            while row is not None:
                exp += row[0]
                gold += row[1]
                stock += row[2]
                row = cursor.fetchone()
            reports = player.get_reports_count()[0]
            players.append([player, exp, gold, stock, "{}/{} ({}%)".format(reports, total_battles, reports * 100 //
                                                                           total_battles)])
        response = "📈Топ <b>{}</b> за день по битвам:\n".format(guild.tag)

        tops = ["🔥По опыту:", "💰По золоту:", "📦По стоку:", "⚔️Участие в битвах на этой неделе:"]
        for i, top in enumerate(tops):
            response += "\n<b>{}</b>\n".format(top)
            players.sort(key=lambda x: x[i + 1] if isinstance(x[i + 1], int) else int(x[i + 1].partition("/")[0]),
                         reverse=True)
            for j, elem in enumerate(players):
                if j < MAX_TOP_PLAYERS_SHOW or j == len(players) - 1:
                    response += "<code>{}</code>){}<code>{:<10}</code> — {}<code>{}</code>" \
                                "\n".format(j + 1, elem[0].castle, "{}{}".format(elem[0].nickname.partition("]")[2] if
                                            "]" in elem[0].nickname else elem[0].nickname, '🎗' if
                                            elem[0].id == guild.commander_id else ""), top[0], elem[i + 1])
                elif j == MAX_TOP_PLAYERS_SHOW:
                    response += "...\n"

        if guild.settings is None or guild.settings.get("tops_notify") in [None, True]:
            bot.send_message(chat_id=guild.chat_id, text=response, parse_mode='HTML')


# Рассылка с напоминанием о арене и крафте в чаты ги в 12 по мск
def arena_notify(bot, job):
    cursor = conn.cursor()
    for guild_id in Guild.guild_ids:
        guild = Guild.get_guild(guild_id=guild_id)
        if guild is None or guild.division == "Луки":
            continue
        if guild.settings is None or guild.settings.get("arena_notify") in [None, True]:
            bot.send_message(chat_id=guild.chat_id, text="Через час обнуление арен и дневного лимита опыта за крафт.")


def notify_guild_attack(bot, update):
    mes = update.message
    remaining_time = get_time_remaining_to_battle()
    if mes.forward_date - datetime.datetime.now() > datetime.timedelta(minutes=2):
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
    set = guild.settings.get("battle_notify")
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
        bot.send_message(chat_id=update.message.chat_id,
                         text='Неверный синтаксис')
        return
    current += ban_for
    try:
        bot.restrictChatMember(chat_id=mes.chat_id, user_id = mes.reply_to_message.from_user.id, until_date=current)
    except TelegramError:
        bot.send_message(chat_id=update.message.chat_id, text='Ошибка. Проверьте, что бот имеет требуемые права.')
        return
    bot.send_message(chat_id=update.message.chat_id, text='Выполнено!', reply_to_message_id=update.message.message_id)
    return


def ranger_notify(bot, job):
    context = job.context
    response = "Поднимай свой лук, <b>{0}</b>\n@{1}".format(context[1], context[0])
    bot.send_message(chat_id=context[2], text=response, parse_mode='HTML')


def rangers_notify_start(bot, update):
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
    request = "select id from players where game_class = 'Ranger' and class_skill_lvl is not NULL"
    cursor.execute(request)
    row = cursor.fetchone()
    while row is not None:
        player = Player.get_player(row[0])
        if player is None:
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
        time_to_notify = time_to_battle - time_to_aim
        print(time_to_notify)
        # time_to_notify = datetime.timedelta(minutes=1)    # TEST
        if time_to_notify >= datetime.timedelta(minutes=0):
            job.run_once(ranger_notify, time_to_notify, context=context)

        row = cursor.fetchone()
        count += 1
    bot.send_message(chat_id=callback_chat_id, text="Запланировано оповещение <b>{0}</b> бедных лучников".format(count),
                     parse_mode='HTML')
