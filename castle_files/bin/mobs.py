"""
Здесь находятся функции обработки событий, связаннх с мобами
"""

from castle_files.work_materials.globals import MOB_CHAT_ID, moscow_tz, utc, cursor, mobs_messages, mobs_lock, \
    dispatcher, conn, ping_messages, classes_to_emoji
from castle_files.work_materials.filters.general_filters import filter_is_pm

from castle_files.libs.player import Player
from castle_files.libs.guild import Guild
from castle_files.libs.castle.location import Location

from castle_files.bin.api import cwapi

import datetime
import re
import logging
import traceback
import requests
import json
import time
import copy
import threading

import psycopg2

import castle_files.work_materials.globals as globals

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TimedOut, TelegramError

PING_LIMIT = 4
MOBS_UPDATE_INTERVAL_SECS = 10


def get_mobs_text_and_buttons(chat_id, link, mobs, lvls, helpers, forward_message_date, buffs, minutes,
                              created_player_id):
    created_player = Player.get_player(player_id=created_player_id, notify_on_error=False)
    response = "{}Обнаруженные мобы{}:\n".format(created_player.castle if created_player is not None else "",
                                                 ", засада!" if minutes == 5 else "")
    avg_lvl = 0
    champion = False
    for i, name in enumerate(mobs):
        lvl = lvls[i]
        if "⚜️Forbidden Champion" in name:
            champion = True
        else:
            avg_lvl += lvl
        emoji = get_mob_emoji(name)
        response += "{}<b>{}</b> 🏅: <code>{}</code>\n{}".format(
            emoji, name, lvl, "  ╰ {}\n".format(buffs[i]) if buffs[i] != "" else "")

    avg_lvl = (avg_lvl / len(lvls)) if not champion else max(lvls)
    if helpers:
        response += "\n" + get_helpers_text(helpers)
    minus, plus = (5 if not champion else 18), (7 if not champion else -8)
    ping = get_chat_helpers(chat_id, minus, plus, avg_lvl, created_player)
    response += "\n" + get_player_stats_text(created_player, forward_message_date, ping)

    now = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
    remaining_time = datetime.timedelta(minutes=minutes) - (now - forward_message_date)
    if remaining_time < datetime.timedelta(0):
        response += "\nВремени не осталось!"
    else:
        response += "\nОсталось: <b>{}</b>".format("{:02d}:{:02d}".format(int(remaining_time.total_seconds() // 60),
                                                                          int(remaining_time.total_seconds() % 60)))
    buttons = [[InlineKeyboardButton(text="⚔ {}-{}🏅".format(int(avg_lvl - minus), int(avg_lvl + plus)),
                                     url=u"https://t.me/share/url?url=/fight_{}".format(link)),
                InlineKeyboardButton(text="🤝Помогаю!", callback_data="mob_partify_{}".format(link))]]
    if len(helpers) >= 5:
        buttons[0].pop(1)
    return [response, InlineKeyboardMarkup(buttons), avg_lvl, remaining_time]


def get_mob_emoji(mob_name: str) -> str:
    emojis = {
        "Wolf": "🐺",
        "Bear": "🐻",
        "Boar": "🐗",
    }
    mob_class = re.search("forbidden (\\w+)", mob_name.lower())
    if mob_class is not None and not "⚜️Forbidden Champion" in mob_name:
        return classes_to_emoji.get(mob_class.group(1).capitalize(), '')
    for mob_class, emoji in list(emojis.items()):
        if mob_class in mob_name:
            return emoji
    return ''




def get_mobs_info_by_link(link):
    cursor = conn.cursor()
    request = "select mob_names, mob_lvls, date_created, helpers, buffs, minutes, created_player from mobs where link = %s"
    cursor.execute(request, (link,))
    row = cursor.fetchone()
    cursor.close()
    return row


def get_mobs_text_by_link(link, chat_id):
    mobs, lvls, forward_message_date, helpers, buffs, minutes, player_id = get_mobs_info_by_link(link)
    response = get_mobs_text_and_buttons(chat_id, link, mobs, lvls, helpers, forward_message_date, buffs, minutes,
                                         player_id)
    return response


def get_suitable_lvls(text):
    champion = False
    if "⚜️Forbidden Champion" in text:
        champion = True
    return (5 if not champion else 18), (7 if not champion else -8)


def get_chat_helpers(chat_id: int, minus, plus, avg_lvl: float, player: Player) -> ['Player']:
    if chat_id is None:
        return []
    barracks = Location.get_location(1)
    try:
        ping_list = barracks.special_info.get("mobs_notify").get(str(chat_id)).copy()
    except Exception:
        ping_list = None
    if not ping_list:
        ping_list = []
    ping_list = set(ping_list)
    if player.guild is not None or ping_list:
        guild = Guild.get_guild(guild_id=player.guild)
        if guild.is_academy() and chat_id == guild.chat_id:
            # Пинги для академки отключены
            return
        if guild is not None and guild.chat_id == chat_id:
            ping_list.update(guild.members)
    ping_list.discard(player.id)
    ping_list = list(filter(lambda player: avg_lvl - minus <= player.lvl <= avg_lvl + plus,
                            map(lambda player_id: Player.get_player(player_id), list(ping_list))))
    ping_list.sort(key=lambda player: player.hp if player.hp is not None else -1, reverse=True)
    return ping_list


def mob(bot, update):
    mes = update.message
    link = re.search("/fight_(.*)$", mes.text)
    if link is None:
        bot.send_message(chat_id=mes.chat_id, text="Ошибка.")
        return
    link = link.group(1)
    names, lvls, buffs = [], [], []
    for string in mes.text.splitlines():
        parse = re.search("(.+) lvl\\.(\\d+)", string)
        if parse is not None:
            name = parse.group(1)
            lvl = int(parse.group(2))
            names.append(name)
            lvls.append(lvl)
            buffs.append("")
        else:
            parse = re.search("  ╰ (.+)", string)
            if parse is not None:
                buff = parse.group(1)
                buffs.pop()
                buffs.append(buff)
    try:
        forward_message_date = utc.localize(mes.forward_date).astimezone(tz=moscow_tz).replace(tzinfo=None)
    except Exception:
        forward_message_date = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
    # forward_message_date = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None) - datetime.timedelta(
    #     minutes=2, seconds=30)  # Test only
    request = "insert into mobs(link, mob_names, mob_lvls, date_created, created_player, on_channel, buffs, " \
              "minutes) values (" \
              "%s, %s, %s, %s, %s, %s, %s, %s)"
    is_pm = filter_is_pm(mes)
    minutes = 5 if 'ambush' in mes.text else 3
    helpers = []
    try:
        cursor.execute(request, (link, names, lvls, forward_message_date, mes.from_user.id, is_pm, buffs, minutes))
    except psycopg2.IntegrityError:
        # logging.error(traceback.format_exc())
        request = "select on_channel, helpers from mobs where link = %s"
        cursor.execute(request, (link,))
        row = cursor.fetchone()
        helpers = row[1]
        if is_pm:
            if row[0]:
                bot.send_message(chat_id=mes.chat_id, text="Данный моб уже на канале",
                                 reply_to_message_id=mes.message_id)
                return
            request = "update mobs set on_channel = true where link = %s"
            cursor.execute(request, (link,))
    minutes = 5 if 'ambush' in mes.text else 3
    response, buttons, avg_lvl, remaining_time = get_mobs_text_and_buttons(mes.chat_id, link, names, lvls, helpers,
                                                                           forward_message_date, buffs, minutes,
                                                                           mes.from_user.id)
    player = Player.get_player(mes.from_user.id)
    if is_pm and (player is None or player.castle == '🖤'):
        if 'It\'s an ambush!'.lower() in mes.text.lower():
            bot.send_message(chat_id=mes.chat_id, text="Засады не отправляются на канал. "
                                                       "Зовите бойцов вашей гильдии на помощь!")
        elif remaining_time <= datetime.timedelta(0):
            bot.send_message(chat_id=mes.chat_id, text="Время истекло. На канал не отправлено.")
        # elif re.search("(boar|wolf|bear)", mes.text) is not None and 'resist' in mes.text:
        #     pass
        else:
            threading.Thread(target=send_mob_message_and_start_updating(bot, mes, player, response, buttons,
                                                                        is_pm, link, forward_message_date, [])).start()
            bot.send_message(chat_id=mes.chat_id, parse_mode='HTML',
                             text="Отправлено на <a href=\"https://t.me/mobs_skala_cw3\">канал</a>, а также в "
                                  "<a href=\"https://t.me/CwMobsNotifyBot\">бота</a>. Спасибо!")
            try:
                # requests.post('http://127.0.0.1:5555/addMob',
                #               json=json.dumps({"castle": '🖤', "text": mes.text, "telegram_id": mes.from_user.id,
                #                                "forward_date": forward_message_date.timestamp()}, ensure_ascii=False),
                #               timeout=0.3)

                pass
                # Верно!
                requests.post('http://144.91.112.129:5555/addMob',
                              json=json.dumps({"castle": '🖤', "text": mes.text, "telegram_id": mes.from_user.id,
                                               "forward_date": forward_message_date.timestamp()}, ensure_ascii=False),
                              timeout=0.3)
            except Exception:
                logging.error(traceback.format_exc())
    else:
        ping = []
        if remaining_time > datetime.timedelta(0):
            if not is_pm:
                minus, plus = get_suitable_lvls(mes.text)
                ping_list = get_chat_helpers(mes.chat_id, minus, plus, avg_lvl, player)
                if ping_list:
                    for pl in ping_list:
                        on = pl.settings.get("mobs_notify")
                        if on is None:
                            on = True
                        if on and pl.id != mes.from_user.id:
                            ping.append(pl.username)
                    if ping:
                        threading.Thread(target=send_notify, args=(link, mes.chat_id, ping)).start()

        threading.Thread(target=send_mob_message_and_start_updating,
                         args=(bot, mes, player, response, buttons, is_pm, link, forward_message_date, ping)).start()
    return


def send_notify(link, chat_id, ping):
    ping_count = 0
    text = "Мобы!\n"

    with mobs_lock:
        messages = ping_messages.get(link)
        if messages is None:
            messages = []
            ping_messages.update({link: messages})

    for username in ping:
        text += "@{} ".format(username)
        ping_count += 1
        if ping_count >= PING_LIMIT:
            # Ну походу надо Promise реализовывать, ибо тут лимиты не будут соблюдаться,
            # но вроде пока пользуюся не активно, можно попозже сделать
            mes = dispatcher.bot.sync_send_message(chat_id=chat_id, text=text)
            with mobs_lock:
                messages.append(mes)
            text = "Мобы!\n"
            ping_count = 0
    if text != "Мобы!\n":
        mes = dispatcher.bot.sync_send_message(chat_id=chat_id, text=text)
        with mobs_lock:
            messages.append(mes)



def send_mob_message_and_start_updating(bot, mes, player, response, buttons, is_pm, link, forward_message_date, ping):
    if is_pm:
        chat_id = MOB_CHAT_ID
    else:
        chat_id = mes.chat_id
    if player is None:
        access = False
    elif player.api_info.get("token") is None:
        bot.send_message(chat_id=player.id,
                         text="Для отображения информации о ваших статах и хп предоставьте достук бота к API (/auth)")
        access = False
    else:
        access = True
        response += "\n\nИнформация о игроке запрошена, ожидайте ответа API..."
    new_mes = bot.sync_send_message(chat_id=chat_id, text=response, reply_markup=buttons, parse_mode='HTML')
    with mobs_lock:
        lst = mobs_messages.get(link)
        if lst is None:
            lst = []
            mobs_messages.update({link: lst})
        lst.append({"chat_id": chat_id, "message_id": new_mes.message_id,
                    "cw_send_time": forward_message_date.timestamp(), "access": access,
                    "last_update_time": time.time()})
    if access:
        for pl in ping:
            if pl.has_api_access:
                cwapi.update_player(player_id=pl.id, player=pl)
        player.api_info.update({"mobs_link": link})
        player.update()
        cwapi.update_player(player_id=player.id, player=player)


def get_player_stats_text(player: Player, forward_message_date, ping):
    if player is None or player.api_info.get("token") is None:
        return ""
    response = "Отправивший игрок:\n{}\n".format(player.format_mobs_stats(forward_message_date, bool(ping)))
    if ping:
        response += "\nПодходящие игроки чата:\n"
        for player in ping:
            response += "{}\n".format(player.format_mobs_stats(forward_message_date))
    return response


def mobs_messages_update_monitor():
    logging.info("Started mobs messages updating")
    while globals.processing:
        try:
            with mobs_lock:
                iter_dict = copy.deepcopy(mobs_messages)
            for link in list(iter_dict):
                update_mobs_messages_by_link(link)

        except Exception:
            logging.error(traceback.format_exc())
        time.sleep(1)


def update_mobs_messages_by_link(link, force_update=False):
    now = time.time()
    lst = mobs_messages.get(link)
    if not lst:
        return
    text, buttons, avg_lvl, remaining_time = get_mobs_text_by_link(link, None)
    if remaining_time < datetime.timedelta(0):
        delete_messages = ping_messages.get(link)
        delete_expired_pings(delete_messages)
        with mobs_lock:
            mobs_messages.pop(link)
            if delete_messages:
                ping_messages.pop(link)
        force_update = True
    for mes_info in lst:
        chat_id, message_id, cw_send_time, access,\
            last_update_time = mes_info.get("chat_id"), mes_info.get("message_id"), \
            mes_info.get("cw_send_time"), mes_info.get("access"), mes_info.get("last_update_time")
        text, buttons, avg_lvl, remaining_time = get_mobs_text_by_link(link, chat_id)

        if force_update or now - last_update_time >= MOBS_UPDATE_INTERVAL_SECS:
            try:
                logging.info("Remaining time: {}".format(remaining_time))
                dispatcher.bot.editMessageText(chat_id=chat_id, message_id=message_id, text=text,
                                               reply_markup=buttons, parse_mode='HTML')
                time.sleep(0.3)
            except TimedOut:
                logging.warning("Got TimeoutError while updating mobs message, sleeping...")
                time.sleep(1)
            mes_info.update({"last_update_time": time.time()})


def delete_expired_pings(messages: list):
    if messages:
        for message in messages:
            try:
                dispatcher.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
            except Exception:
                logging.warning("Can not delete mobs ping message: {}".format(traceback.format_exc()))


def get_helpers_text(helpers):
    response = "Помощники:\n"
    for username in helpers:
        response += "@{}\n".format(username)
    return response


def mob_help(bot, update):
    data = update.callback_query.data
    mes = update.callback_query.message
    link = re.search("mob_partify_(.+)", data)
    if link is None:
        bot.send_message(chat_id=update.callback_query.from_user.id, text="Произошла ошибка.")
        return
    link = link.group(1)
    try:
        names, lvls, forward_message_date, helpers, buffs, minutes, player_id = get_mobs_info_by_link(link)
    except (ValueError, TypeError):
        bot.send_message(chat_id=update.callback_query.from_user.id, text="Событие не найдено")
        return
    if update.callback_query.from_user.username in helpers:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Ты уже помог!", show_alert=True)
        return
    if len(helpers) >= 5:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Уже собралось достаточно помощников!",
                                show_alert=True)
    else:
        helpers.append(update.callback_query.from_user.username)
    minutes = 5 if 'засада' in mes.text else 3
    response, buttons, avg_lvl, remailing_time = get_mobs_text_and_buttons(mes.chat_id, link, names, lvls, helpers,
                                                                           forward_message_date, buffs, minutes,
                                                                           player_id)

    try:
        bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=response,
                            reply_markup=buttons, parse_mode='HTML')
    except Exception:
        logging.error(traceback.format_exc())
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Успешно добавлено")
    request = "update mobs set helpers = %s where link = %s"
    cursor.execute(request, (helpers, link))


def get_fight_club_txt(link, lvl, helpers, forward_message_date):
    response = "Подпольный бой!\n🏅Уровень: <b>{}</b>\n".format(lvl)
    if helpers:
        response += "\n"
        for username in helpers:
            response += "{}\n".format(username)

    now = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
    remaining_time = datetime.timedelta(minutes=3) - (now - forward_message_date)
    if remaining_time < datetime.timedelta(0):
        response += "\nВремени не осталось!"
    else:
        response += "\nОсталось: <b>{}</b>".format("{:02d}:{:02d}".format(int(remaining_time.total_seconds() // 60),
                                                                          int(remaining_time.total_seconds() % 60)))
    return response


def fight_club(bot, update):
    mes = update.message
    link = re.search("/fight_(.*)$", mes.text)
    if link is None:
        bot.send_message(chat_id=mes.chat_id, text="Ошибка.")
        return
    link = link.group(1)
    player = Player.get_player(mes.from_user.id)
    try:
        forward_message_date = utc.localize(mes.forward_date).astimezone(tz=moscow_tz).replace(tzinfo=None)
    except Exception:
        forward_message_date = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
    request = "select mob_lvls, helpers from mobs where link = %s"
    cursor.execute(request, (link,))
    row = cursor.fetchone()
    helpers = []
    lvl = player.lvl
    if row is not None:
        lvls, helpers = row
        lvl = lvls[0]
    response = get_fight_club_txt(link, lvl, helpers, forward_message_date)
    buttons = [[InlineKeyboardButton(text="⚔ {}-{}🏅".format(int(lvl - 5), int(lvl + 10)),
                                     url=u"https://t.me/share/url?url=/fight_{}".format(link)),
                InlineKeyboardButton(text="🤝Помогаю!", callback_data="fight_club_partify_{}".format(link))]]
    guild = Guild.get_guild(chat_id=mes.chat_id)
    if guild is not None:
        ping = []
        for player_id in guild.members:
            cur_player = Player.get_player(player_id)
            if cur_player is None:
                continue
            if cur_player.settings.get("pretend") and cur_player.lvl in range(lvl - 5, lvl + 11) and \
                    player.username not in ping:
                ping.append(player.username)
            if len(ping) >= 4:
                text = "Подпольный бой!\n"
                for username in ping:
                    text += "@{} ".format(username)
                bot.send_message(chat_id=mes.chat_id, text=text)
                ping.clear()
        if ping:
            text = "Подпольный бой!\n"
            for username in ping:
                text += "@{} ".format(username)
            bot.send_message(chat_id=mes.chat_id, text=text)
    if guild is not None:
        response += "\n\n<em>Подписаться на уведомления о клубах в чате ги:</em> /pretend"
    bot.send_message(chat_id=mes.chat_id, text=response, reply_markup=InlineKeyboardMarkup(buttons), parse_mode='HTML')
    request = "insert into mobs(link, mob_names, mob_lvls, date_created, created_player) values (" \
              "%s, %s, %s, %s, %s)"
    try:
        cursor.execute(request, (link, ["Fight Club"], [lvl], forward_message_date, mes.from_user.id))
    except psycopg2.IntegrityError:
        pass


def fight_club_help(bot, update):
    data = update.callback_query.data
    mes = update.callback_query.message
    link = re.search("fight_club_partify_(.+)", data)
    if link is None:
        bot.send_message(chat_id=update.callback_query.from_user.id, text="Произошла ошибка.")
        return
    link = link.group(1)
    request = "select mob_lvls, date_created, helpers from mobs where link = %s"
    cursor.execute(request, (link,))
    row = cursor.fetchone()
    if row is None:
        bot.send_message(chat_id=update.callback_query.from_user.id, text="Событие не найдено")
        return
    lvls, forward_message_date, helpers = row
    lvl = lvls[0]
    player = Player.get_player(update.callback_query.from_user.id)
    if player is None:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Для помощи необходима регистрация!",
                                show_alert=True)
        return
    helper_row = "@{} 🏅:{}".format(player.username, player.lvl)
    if helper_row in helpers:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Ты уже помогаешь!", show_alert=True)
        return
    helpers.append(helper_row)
    response = get_fight_club_txt(link, lvl, helpers, forward_message_date)
    buttons = [[InlineKeyboardButton(text="⚔ {}-{}🏅".format(int(player.lvl - 5), int(player.lvl + 10)),
                                     url=u"https://t.me/share/url?url=/fight_{}".format(link)),
                InlineKeyboardButton(text="🤝Помогаю!", callback_data="fight_club_partify_{}".format(link))]]
    try:
        bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=response,
                            reply_markup=InlineKeyboardMarkup(buttons), parse_mode='HTML')
    except Exception:
        logging.error(traceback.format_exc())
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Успешно добавлено")
    request = "update mobs set helpers = %s where link = %s"
    cursor.execute(request, (helpers, link))


def pretend(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    current = player.settings.get("pretend")
    if current is None:
        current = False
    current = not current
    player.settings.update({"pretend": current})
    player.update()
    bot.send_message(chat_id=mes.chat_id,
                     text="Пинги на подпольные бои <b>{}</b>".format("✅включены" if current else "❌отключены"),
                     parse_mode='HTML')
    return


def mobs_notify(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    barracks = Location.get_location(1)
    chats = barracks.special_info.get("mobs_notify")
    if chats is None:
        chats = {}
        barracks.special_info.update({"mobs_notify": chats})
    current = chats.get(str(mes.chat_id))
    if current is None:
        current = []
        chats.update({str(mes.chat_id): current})
    try:
        current.remove(player.id)
        bot.send_message(chat_id=mes.chat_id,
                         text="<b>{}</b> удалён из списка пинга чата на мобов.".format(player.nickname),
                         parse_mode='HTML')
    except ValueError:
        current.append(player.id)
        bot.send_message(chat_id=mes.chat_id,
                         text="<b>{}</b> добавлен в список пинга чата на мобов.".format(player.nickname),
                         parse_mode='HTML')
    barracks.update_location_to_database()
