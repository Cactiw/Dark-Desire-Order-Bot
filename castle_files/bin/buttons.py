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
            InlineKeyboardButton("Отключить приказы" if guild.orders_enabled else "Включить приказы",
                                 callback_data="gco_{}".format(guild.id))
        ],
    ]
    return InlineKeyboardMarkup(buttons)
