"""
Здесь находятся функции обработки событий, связаннх с мобами
"""

from castle_files.work_materials.globals import MOB_CHAT_ID, moscow_tz, utc, cursor
from castle_files.work_materials.filters.general_filters import filter_is_pm

from castle_files.libs.player import Player
from castle_files.libs.guild import Guild
from castle_files.libs.castle.location import Location

import datetime
import re
import logging
import traceback
import requests
import json

import psycopg2

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

PING_LIMIT = 4


def get_mobs_text_and_buttons(link, mobs, lvls, helpers, forward_message_date, buffs, minutes):
    response = "Обнаруженные мобы{}:\n".format(", засада!" if minutes == 5 else "")
    avg_lvl = 0
    for i, name in enumerate(mobs):
        lvl = lvls[i]
        avg_lvl += lvl
        response += "<b>{}</b> 🏅: <code>{}</code>\n{}".format(name, lvl, "  ╰ {}\n".format(buffs[i]) if buffs[i] != ""
                                                              else "")
    avg_lvl /= len(lvls)
    if helpers:
        response += "\n" + get_helpers_text(helpers)

    now = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
    remaining_time = datetime.timedelta(minutes=minutes) - (now - forward_message_date)
    if remaining_time < datetime.timedelta(0):
        response += "\nВремени не осталось!"
    else:
        response += "\nОсталось: <b>{}</b>".format("{:02d}:{:02d}".format(int(remaining_time.total_seconds() // 60),
                                                                          int(remaining_time.total_seconds() % 60)))
    buttons = [[InlineKeyboardButton(text="⚔ {}-{}🏅".format(int(avg_lvl - 5), int(avg_lvl + 10)),
                                     url=u"https://t.me/share/url?url=/fight_{}".format(link)),
                InlineKeyboardButton(text="🤝Помогаю!", callback_data="mob_partify_{}".format(link))]]
    if len(helpers) >= 5:
        buttons[0].pop(1)
    return [response, InlineKeyboardMarkup(buttons), avg_lvl]


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
    request = "insert into mobs(link, mob_names, mob_lvls, date_created, created_player, on_channel, buffs) values (" \
              "%s, %s, %s, %s, %s, %s, %s)"
    is_pm = filter_is_pm(mes)
    helpers = []
    try:
        cursor.execute(request, (link, names, lvls, forward_message_date, mes.from_user.id, is_pm, buffs))
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
    response, buttons, avg_lvl = get_mobs_text_and_buttons(link, names, lvls, helpers, forward_message_date, buffs,
                                                           minutes)
    player = Player.get_player(mes.from_user.id)
    if is_pm and (player is None or player.castle == '🖤'):
        if 'It\'s an ambush!'.lower() in mes.text.lower():
            bot.send_message(chat_id=mes.chat_id, text="Засады не отправляются на канал. "
                                                       "Зовите бойцов вашей гильдии на помощь!")
        else:
            bot.send_message(chat_id=MOB_CHAT_ID, text=response, parse_mode='HTML', reply_markup=buttons)
            bot.send_message(chat_id=mes.chat_id, text="Отправлено на канал. Спасибо!")
            try:
                # requests.post('http://127.0.0.1:5555/addMob',
                #               json=json.dumps({"castle": '🖤', "text": mes.text, "telegram_id": mes.from_user.id,
                #                                "forward_date": forward_message_date.timestamp()}, ensure_ascii=False),
                #               timeout=0.3)

                pass
                # Верно!
                requests.post('http://ec2-18-184-54-121.eu-central-1.compute.amazonaws.com:5555/addMob',
                              json=json.dumps({"castle": '🖤', "text": mes.text, "telegram_id": mes.from_user.id,
                                               "forward_date": forward_message_date.timestamp()}, ensure_ascii=False),
                              timeout=0.3)
            except Exception:
                logging.error(traceback.format_exc())
    else:
        ping_count = 0
        if not is_pm:
            barracks = Location.get_location(1)
            try:
                ping_list = barracks.special_info.get("mobs_notify").get(str(mes.chat_id)).copy()
            except Exception:
                ping_list = None
            if not ping_list:
                ping_list = []
            if player.guild is not None or ping_list:
                guild = Guild.get_guild(guild_id=player.guild)
                if guild is not None and guild.chat_id == mes.chat_id:
                    ping_list += guild.members
                if ping_list:
                    ping = []
                    for pl_id in ping_list:
                        pl = Player.get_player(pl_id)
                        if avg_lvl - 5 <= pl.lvl <= avg_lvl + 10:
                            on = pl.settings.get("mobs_notify")
                            if on is None:
                                on = True
                            if on and pl.id != mes.from_user.id:
                                ping.append(pl.username)
                    if ping:
                        text = "Мобы!\n"
                        for username in ping:
                            text += "@{} ".format(username)
                            ping_count += 1
                            if ping_count >= PING_LIMIT:
                                bot.send_message(chat_id=mes.chat_id, text=text)
                                text = "Мобы!\n"
                                ping_count = 0
                        if text != "Мобы!\n":
                            bot.send_message(chat_id=mes.chat_id, text=text)
        bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML', reply_markup=buttons)
    return


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
    request = "select mob_names, mob_lvls, date_created, helpers, buffs from mobs where link = %s"
    cursor.execute(request, (link,))
    row = cursor.fetchone()
    if row is None:
        bot.send_message(chat_id=update.callback_query.from_user.id, text="Событие не найдено")
        return
    names, lvls, forward_message_date, helpers, buffs = row
    if update.callback_query.from_user.username in helpers:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Ты уже помог!", show_alert=True)
        return
    if len(helpers) >= 5:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Уже собралось достаточно помощников!",
                                show_alert=True)
    else:
        helpers.append(update.callback_query.from_user.username)
    minutes = 5 if 'засада' in mes.text else 3
    response, buttons, avg_lvl = get_mobs_text_and_buttons(link, names, lvls, helpers, forward_message_date, buffs, minutes)

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
            if cur_player.settings.get("pretend") and cur_player.lvl in range(lvl - 5, lvl + 11):
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


