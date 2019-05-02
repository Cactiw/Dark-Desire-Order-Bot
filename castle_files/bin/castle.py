"""
В этом модуле находятся функции, связанные с "игровым" замком - виртуальным замком Скалы в боте
"""
from castle_files.bin.buttons import send_general_buttons


def back(bot, update, user_data):
    statuses_back = {
        "barracks": "central_square",
        "central_square": "default"
    }
    status = user_data.get("status")
    if status is None:
        send_general_buttons(update.message.from_user.id, user_data, bot=bot)
    new_status = statuses_back.get(status)
    user_data.update({"status": new_status})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def welcome(bot, update, user_data):
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def central_square(bot, update, user_data):
    user_data.update({"status": "central_square"})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def barracks(bot, update, user_data):
    user_data.update({"status": "barracks"})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)
