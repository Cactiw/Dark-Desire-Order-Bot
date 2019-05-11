"""
Всякие функции, связанные с мидом - рассылки по гильдиям и так далее
"""
from castle_files.libs.guild import Guild
from order_files.bin.pult_callback import count_next_battle_time

from castle_files.work_materials.globals import job, MID_CHAT_ID, moscow_tz

from telegram.error import TelegramError


import re
import threading
import datetime
import time


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


def plan_battle_jobs():
    plan_mid_notifications()
    job.run_once(after_battle, count_next_battle_time)


def after_battle(bot, job):
    time.sleep(1)
    plan_battle_jobs()


def plan_mid_notifications():
    time_before_battle_to_notify = [
        datetime.timedelta(minutes=2),
        datetime.timedelta(minutes=1),
        datetime.timedelta(seconds=30),
        datetime.timedelta(seconds=20),
        datetime.timedelta(seconds=15),
        datetime.timedelta(seconds=10),
    ]
    battle_time = count_next_battle_time()
    for time in time_before_battle_to_notify:
        job.run_once(message_before_battle, battle_time - time)


def message_before_battle(bot, job):
    bot.send_message(chat_id=MID_CHAT_ID,
                     text=datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None).strftime("%M:%S"))

