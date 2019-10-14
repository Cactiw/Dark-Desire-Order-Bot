"""
Здесь находятся функции обработки событий, связаннх с мобами
"""

from castle_files.work_materials.globals import MOB_CHAT_ID, moscow_tz, utc, cursor
from castle_files.work_materials.filters.general_filters import filter_is_pm
from castle_files.libs.player import Player
from castle_files.libs.guild import Guild

import datetime
import re
import logging
import traceback
import requests
import json

import psycopg2

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_mobs_text_and_buttons(link, mobs, lvls, helpers, forward_message_date, buffs):
    response = "Обнаруженные мобы:\n"
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
    remaining_time = datetime.timedelta(minutes=3) - (now - forward_message_date)
    if remaining_time < datetime.timedelta(0):
        response += "\nВремени не осталось!"
    else:
        response += "\nОсталось: <b>{}</b>".format("{:02d}:{:02d}".format(int(remaining_time.total_seconds() // 60),
                                                                          int(remaining_time.total_seconds() % 60)))
    buttons = [[InlineKeyboardButton(text="⚔ {}-{}🏅".format(int(avg_lvl - 5), int(avg_lvl + 10)),
                                     url=u"https://t.me/share/url?url=/fight_{}".format(link)),
                InlineKeyboardButton(text="🤝Помогаю!", callback_data="mob_partify_{}".format(link))]]
    if len(helpers) >= 3:
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
    response, buttons, avg_lvl = get_mobs_text_and_buttons(link, names, lvls, helpers, forward_message_date, buffs)
    player = Player.get_player(mes.from_user.id)
    if is_pm and (player is None or player.castle == '🖤'):
        bot.send_message(chat_id=MOB_CHAT_ID, text=response, parse_mode='HTML', reply_markup=buttons)
        bot.send_message(chat_id=mes.chat_id, text="Отправлено на канал. Спасибо!")
        try:
            # requests.post('http://127.0.0.1:5555/addMob',
            #               json=json.dumps({"castle": '🖤', "text": mes.text, "telegram_id": mes.from_user.id,
            #                                "forward_date": forward_message_date.timestamp()}, ensure_ascii=False),
            #               timeout=0.3)
            requests.post('http://104.40.129.51:5555/addMob',
                          json=json.dumps({"castle": '🖤', "text": mes.text, "telegram_id": mes.from_user.id,
                                           "forward_date": forward_message_date.timestamp()}, ensure_ascii=False),
                          timeout=0.3)
        except Exception:
            logging.error(traceback.format_exc())
    else:
        if not is_pm:
            if player.guild is not None:
                guild = Guild.get_guild(guild_id=player.guild)
                if guild is not None and guild.chat_id == mes.chat_id:
                    ping = []
                    for pl_id in guild.members:
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
    response, buttons, avg_lvl = get_mobs_text_and_buttons(link, names, lvls, helpers, forward_message_date, buffs)

    try:
        bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=response,
                            reply_markup=buttons, parse_mode='HTML')
    except Exception:
        logging.error(traceback.format_exc())
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Успешно добавлено")
    request = "update mobs set helpers = %s where link = %s"
    cursor.execute(request, (helpers, link))
