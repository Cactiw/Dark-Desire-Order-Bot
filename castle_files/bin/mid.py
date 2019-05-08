"""
Всякие функции, связанные с мидом - рассылки по гильдиям и так далее
"""
from castle_files.libs.guild import Guild

from telegram.error import TelegramError

import re
import threading


def mailing(bot, update):
    mes = update.message
    text = mes.text.partition("mailing ")[2]
    for guild_id in Guild.guild_ids:
        guild = Guild.get_guild(guild_id=guild_id)
        bot.send_message(chat_id=guild.chat_id, text=text, parse_mode='HTML')
    bot.send_message(update.message.chat_id, text="Успешно отправлено!", reply_to_message_id=mes.message_id)


def mailing_pin(bot, update):
    threading.Thread(target=mail_and_pin, args=[bot, update]).start()


def mail_and_pin(bot, update):
    mes = update.message
    text = mes.text.partition("mailing_pin")[2]
    for guild_id in Guild.guild_ids:
        guild = Guild.get_guild(guild_id=guild_id)
        try:
            message = bot.sync_send_message(chat_id=guild.chat_id, text=text, parse_mode='HTML')
            bot.pinChatMessage(chat_id=message.chat_id, message_id=message.message_id)
        except TelegramError:
            pass
    bot.send_message(update.message.chat_id, text="Успешно отправлено!", reply_to_message_id=mes.message_id)
