"""
Здесь находятся функции обработки событий, связаннх с мобами
"""

from castle_files.work_materials.globals import MOB_CHAT_ID, moscow_tz, local_tz, cursor
from castle_files.work_materials.filters.general_filters import filter_is_pm

import datetime
import re
import logging
import traceback

import psycopg2

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def mob(bot, update):
    mes = update.message
    link = re.search("/fight_(.*)$", mes.text)
    if link is None:
        bot.send_message(chat_id=mes.chat_id, text="Ошибка.")
        return
    link = link.group(1)
    response = "Обнаруженные мобы:\n"
    names, lvls = [], []
    for string in mes.text.splitlines():
        parse = re.search("(.+) lvl\\.(\\d+)", string)
        if parse is not None:
            name = parse.group(1)
            lvl = int(parse.group(2))
            names.append(name)
            lvls.append(lvl)
            response += "<b>{}</b> 🏅: <code>{}</code>\n".format(name, lvl)
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton(text="⚔️В бой!",
                                                          url=u"https://t.me/share/url?url=/fight_{}".format(link))]])
    try:
        forward_message_date = local_tz.localize(mes.forward_date).astimezone(tz=moscow_tz).replace(tzinfo=None)
    except Exception:
        forward_message_date = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
    now = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
    remaining_time = datetime.timedelta(minutes=3) - (now - forward_message_date)
    if remaining_time < datetime.timedelta(0):
        response += "\nВремени не осталось!"
    else:
        response += "Осталось: <b>{}</b>".format("{:02d}:{:02d}".format(int(remaining_time.total_seconds() // 60),
                                                                        int(remaining_time.total_seconds() % 60)))
    request = "insert into mobs(link, mob_names, mob_lvls, date_created, created_player, on_channel) values (" \
              "%s, %s, %s, %s, %s, %s)"
    is_pm = filter_is_pm(mes)
    try:
        cursor.execute(request, (link, names, lvls, forward_message_date, mes.from_user.id, is_pm))
    except psycopg2.IntegrityError:
        # logging.error(traceback.format_exc())
        if is_pm:
            request = "select on_channel from mobs where link = %s"
            cursor.execute(request, (link,))
            row = cursor.fetchone()
            if row[0]:
                bot.send_message(chat_id=mes.chat_id, text="Данный моб уже на канале",
                                 reply_to_message_id=mes.message_id)
                return
            request = "update mobs set on_channel = true where link = %s"
            cursor.execute(request, (link,))
    if is_pm:
        bot.send_message(chat_id=MOB_CHAT_ID, text=response, parse_mode='HTML', reply_markup=buttons)
        bot.send_message(chat_id=mes.chat_id, text="Отправлено на канал. Спасибо!")
    else:
        bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML', reply_markup=buttons)
    return
