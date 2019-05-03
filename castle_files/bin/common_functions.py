"""
В этом модуле находятся общие callback-функции, которые нельзя отнести к другим категориям
"""

from castle_files.bin.buttons import send_general_buttons
from castle_files.work_materials.filters.general_filters import filter_is_pm


# Некорректный ввод
def unknown_input(bot, update, user_data):
    if filter_is_pm(update.message):
        send_general_buttons(update.message.from_user.id, user_data, bot=bot)
