"""
В этом модуле находятся общие callback-функции, которые нельзя отнести к другим категориям
"""

from castle_files.bin.buttons import send_general_buttons
from castle_files.work_materials.filters.general_filters import filter_is_pm

from castle_files.work_materials.globals import conn, SUPER_ADMIN_ID

from castle_files.libs.player import Player

from psycopg2 import ProgrammingError

import sys


# Некорректный ввод
def unknown_input(bot, update, user_data):
    if filter_is_pm(update.message):
        player = Player.get_player(update.message.from_user.id, notify_on_error=False)
        if player is None:
            return
        send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def sql(bot, update):
    if update.message.from_user.id != SUPER_ADMIN_ID:
        return
    cursor = conn.cursor()
    mes = update.message
    request = mes.text.partition(" ")[2]
    try:
        cursor.execute(request)
    except Exception:
        error = sys.exc_info()
        response = ""
        for i in range(0, len(error)):
            response += str(sys.exc_info()[i]) + '\n'
        bot.send_message(chat_id=mes.chat_id, text=response)
        return
    row = None
    try:
        row = cursor.fetchone()
    except ProgrammingError:
        bot.send_message(chat_id=mes.chat_id, text="Empty. Row count: {}".format(cursor.cursor.rowcount))
        return
    response = ""
    while row:
        for i in range(0, len(row)):
            response += str(row[i]) + " "
        row = cursor.fetchone()
        response += "\n\n"
    if response == "":
        bot.send_message(chat_id=mes.chat_id, text="Empty. Row count: {}".format(cursor.cursor.rowcount))
        return
    bot.send_message(chat_id=mes.chat_id, text=response)
