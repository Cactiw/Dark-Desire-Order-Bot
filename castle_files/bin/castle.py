"""
В этом модуле находятся функции, связанные с "игровым" замком - виртуальным замком Скалы в боте
"""
from castle_files.bin.buttons import send_general_buttons
from castle_files.libs.castle.location import Location


def back(bot, update, user_data):
    statuses_back = {
        "barracks": "central_square",
        "central_square": "default",
        "throne_room": "central_square",
        "mid_feedback": "throne_room"
    }
    status = user_data.get("status")
    if status is None:
        send_general_buttons(update.message.from_user.id, user_data, bot=bot)
    new_status = statuses_back.get(status)
    new_location = Location.get_id_by_status(new_status)
    user_data.update({"status": new_status, "location_id": new_location})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def guide_signs(bot, update):
    bot.send_message(chat_id=update.message.from_user.id,
                     text="Указатели гласят:\n")


def welcome(bot, update, user_data):
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def central_square(bot, update, user_data):
    user_data.update({"status": "central_square", "location_id": 0})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def barracks(bot, update, user_data):
    user_data.update({"status": "barracks", "location_id": 1})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def throne_room(bot, update, user_data):
    user_data.update({"status": "throne_room", "location_id": 2})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)

