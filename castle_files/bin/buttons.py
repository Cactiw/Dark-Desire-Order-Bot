"""
Этот модуль содержит функции получения Inline, или обычных кнопок для отправки их в сообщении.
"""
from telegram import InlineKeyboardButton, KeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


def get_edit_guild_buttons(guild):
    buttons = [
        [
            InlineKeyboardButton("Изменить командира", callback_data="gccmdr_{}".format(guild.id)),
            InlineKeyboardButton("Изменить чат гильдии", callback_data="gccht_{}".format(guild.id)),
        ],
        [
            InlineKeyboardButton("Изменить дивизион", callback_data="gcdvs_{}".format(guild.id)),
            InlineKeyboardButton("Отключить приказы" if guild.orders_enabled else "Включить приказы",
                                 callback_data="gco_{}".format(guild.id))
        ],
        [
            InlineKeyboardButton("Отключить пины" if guild.pin_enabled else "Включить пины",
                                 callback_data="gcp_{}".format(guild.id)),
            InlineKeyboardButton("Включить уведомления" if guild.disable_notification else "Выключить уведомления",
                                 callback_data="gcn_{}".format(guild.id)),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def get_view_guild_buttons(guild):
    buttons = [
        [
            InlineKeyboardButton("Список игроков", callback_data="gipl_{}".format(guild.id)),
            InlineKeyboardButton("Покинуть гильдию", callback_data="gilv_{}".format(guild.id)),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


# Функция, которая возвращает кнопки для любого статуса. Принимает на вход user_data, в котором читает поле "status",
# далее генерирует и возвращает кнопки
def get_general_buttons(user_data):
    status = user_data.get("status")
    if status is None or status == "default":
        buttons = [
            [
                KeyboardButton("Профиль"),
                KeyboardButton("Гильдия"),
            ]
        ]
        return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
