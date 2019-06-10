"""
Всякие функции, связанные с мидом - рассылки по гильдиям и так далее
"""
from castle_files.libs.guild import Guild
from order_files.bin.pult_callback import count_next_battle_time

from castle_files.bin.guild_chats import rangers_notify_start

from castle_files.work_materials.globals import job, MID_CHAT_ID, moscow_tz, local_tz, dispatcher, SUPER_ADMIN_ID

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
        if guild.division != "Луки":
            bot.send_message(chat_id=guild.chat_id, text=text, parse_mode='HTML')
    bot.send_message(update.message.chat_id, text="Успешно отправлено!", reply_to_message_id=mes.message_id)


def mailing_pin(bot, update):
    threading.Thread(target=mail_and_pin, args=[bot, update]).start()


def mail_and_pin(bot, update):
    mes = update.message
    text = mes.text.partition("mailing_pin")[2]
    for guild_id in Guild.guild_ids:
        guild = Guild.get_guild(guild_id=guild_id)
        if guild.division == "Луки":
            continue
        try:
            message = bot.sync_send_message(chat_id=guild.chat_id, text=text, parse_mode='HTML')
            bot.pinChatMessage(chat_id=message.chat_id, message_id=message.message_id)
        except TelegramError:
            pass
    bot.send_message(update.message.chat_id, text="Успешно отправлено!", reply_to_message_id=mes.message_id)


def plan_battle_jobs():
    plan_mid_notifications()
    job.run_once(after_battle, moscow_tz.localize(count_next_battle_time()).astimezone(tz=local_tz).replace(tzinfo=None))
    rangers_notify_start(bot=dispatcher.bot, update=SUPER_ADMIN_ID)


def after_battle(bot, job):
    time.sleep(1)
    plan_battle_jobs()
    threading.Thread(target=unpin_orders, args=()).start()


def unpin_orders():
    for guild_id in Guild.guild_ids:
        guild = Guild.get_guild(guild_id=guild_id)
        if guild.settings is None or guild.settings.get("unpin") in [None, True]:
            try:
                dispatcher.bot.unpinChatMessage(chat_id=guild.chat_id)
            except TelegramError:
                pass


def plan_arena_notify():
    time_to_send = datetime.time(hour=12, minute=0, second=0)
    time_now = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None).time()
    day_to_send = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None).date()
    date_to_send = datetime.datetime.combine(day_to_send, datetime.time(hour=0))
    if time_to_send < time_now:
        date_to_send += datetime.timedelta(days=1)
    date_to_send = date_to_send.date()
    send_time = datetime.datetime.combine(date_to_send, time_to_send)  # Время в мск
    send_time = moscow_tz.localize(send_time).astimezone(tz=local_tz).replace(tzinfo=None)  # Локальное время
    job.run_once(arena_notify, when=send_time, context=[])


def arena_notify(bot, job):
    for guild_id in Guild.guild_ids:
        guild = Guild.get_guild(guild_id=guild_id)
        if guild.settings is None or guild.settings.get("arena_notify") in [None, True]:
            bot.send_message(chat_id=guild.chat_id, text="Через час обнуление арен и дневного лимита опыта за крафт.")


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

