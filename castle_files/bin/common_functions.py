"""
В этом модуле находятся общие callback-функции, которые нельзя отнести к другим категориям
"""

from castle_files.bin.buttons import get_general_buttons


# Некорректный ввод
def unknown_input(bot, update, user_data):
    bot.send_message(chat_id=update.message.chat_id, text="Некорректный ввод",
                     reply_markup=get_general_buttons(user_data))
