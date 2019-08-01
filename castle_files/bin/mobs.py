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


def get_mobs_text(mobs, lvls, helpers, forward_message_date):
    response = "Обнаруженные мобы:\n"
    for i, name in enumerate(mobs):
        lvl = lvls[i]
        response += "<b>{}</b> 🏅: <code>{}</code>\n".format(name, lvl)
    if helpers:
        response += "\n" + get_helpers_text(helpers)

    now = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
    remaining_time = datetime.timedelta(minutes=3) - (now - forward_message_date)
    if remaining_time < datetime.timedelta(0):
        response += "\nВремени не осталось!"
    else:
        response += "\nОсталось: <b>{}</b>".format("{:02d}:{:02d}".format(int(remaining_time.total_seconds() // 60),
                                                                          int(remaining_time.total_seconds() % 60)))
    return response


def mob(bot, update):
    mes = update.message
    link = re.search("/fight_(.*)$", mes.text)
    if link is None:
        bot.send_message(chat_id=mes.chat_id, text="Ошибка.")
        return
    link = link.group(1)
    names, lvls = [], []
    for string in mes.text.splitlines():
        parse = re.search("(.+) lvl\\.(\\d+)", string)
        if parse is not None:
            name = parse.group(1)
            lvl = int(parse.group(2))
            names.append(name)
            lvls.append(lvl)
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton(text="⚔️В бой!",
                                                          url=u"https://t.me/share/url?url=/fight_{}".format(link)),
                                     InlineKeyboardButton(text="🤝Помогаю!",
                                                          callback_data="mob_partify_{}".format(link))]])
    try:
        forward_message_date = local_tz.localize(mes.forward_date).astimezone(tz=moscow_tz).replace(tzinfo=None)
    except Exception:
        forward_message_date = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
    request = "insert into mobs(link, mob_names, mob_lvls, date_created, created_player, on_channel) values (" \
              "%s, %s, %s, %s, %s, %s)"
    is_pm = filter_is_pm(mes)
    helpers = []
    try:
        cursor.execute(request, (link, names, lvls, forward_message_date, mes.from_user.id, is_pm))
    except psycopg2.IntegrityError:
        # logging.error(traceback.format_exc())
        if is_pm:
            request = "select on_channel, helpers from mobs where link = %s"
            cursor.execute(request, (link,))
            row = cursor.fetchone()
            if row[0]:
                bot.send_message(chat_id=mes.chat_id, text="Данный моб уже на канале",
                                 reply_to_message_id=mes.message_id)
                return
            request = "update mobs set on_channel = true where link = %s"
            cursor.execute(request, (link,))
            helpers = row[1]
    response = get_mobs_text(names, lvls, helpers, forward_message_date)
    if is_pm:
        bot.send_message(chat_id=MOB_CHAT_ID, text=response, parse_mode='HTML', reply_markup=buttons)
        bot.send_message(chat_id=mes.chat_id, text="Отправлено на канал. Спасибо!")
    else:
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
    request = "select mob_names, mob_lvls, date_created, helpers from mobs where link = %s"
    cursor.execute(request, (link,))
    row = cursor.fetchone()
    if row is None:
        bot.send_message(chat_id=update.callback_query.from_user.id, text="Событие не найдено")
        return
    names, lvls, forward_message_date, helpers = row
    if len(helpers) >= 3:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Уже собралось достаточно помощников!",
                                show_alert=True)
        return
    if update.callback_query.from_user.username in helpers:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Ты уже помог!", show_alert=True)
        return
    helpers.append(update.callback_query.from_user.username)
    response = get_mobs_text(names, lvls, helpers, forward_message_date)
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton(text="⚔️В бой!",
                                                          url=u"https://t.me/share/url?url=/fight_{}".format(link)),
                                     InlineKeyboardButton(text="🤝Помогаю!",
                                                          callback_data="mob_partify_{}".format(link))]])
    try:
        bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=response,
                            reply_markup=buttons, parse_mode='HTML')
    except Exception:
        logging.error(traceback.format_exc())
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id, text="Успешно добавлено")
    request = "update mobs set helpers = %s where link = %s"
    cursor.execute(request, (helpers, link))
