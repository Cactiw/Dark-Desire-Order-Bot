"""
Функции, связанные с чайной лигой, а также парсингом квестов и тп
"""
from castle_files.bin.buttons import send_general_buttons


def tea_party(bot, update, user_data):
    user_data.update({"status": "tea_party", "location_id": 9})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def exploration(bot, update, user_data):
    user_data.update({"status": "exploration"})
