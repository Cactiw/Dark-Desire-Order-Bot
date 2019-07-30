"""
Здесь находятся функции обработки событий, связаннх с мобами
"""

from castle_files.work_materials.globals import MOB_CHAT_ID
from castle_files.work_materials.filters.general_filters import filter_is_pm

import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def mob(bot, update):
    mes = update.message
    link = re.search("/fight_(.*)$", mes.text)
    if link is None:
        bot.send_message(chat_id=mes.chat_id, text="Ошибка.")
        return
    link = link.group(1)
    response = "Обнаруженные мобы:\n"
    for string in mes.text.splitlines():
        parse = re.search("(.+) lvl\\.(\\d+)", string)
        if parse is not None:
            name = parse.group(1)
            lvl = int(parse.group(2))
            response += "<b>{}</b> 🏅: <code>{}</code>\n".format(name, lvl)
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton(text="⚔️В бой!",
                                                          url=u"https://t.me/share/url?url=/fight_{}".format(link))]])
    if filter_is_pm(mes):
        bot.send_message(chat_id=MOB_CHAT_ID, text=response, parse_mode='HTML', reply_markup=buttons)
    else:
        bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML', reply_markup=buttons)
    return
