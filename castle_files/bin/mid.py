"""
Всякие функции, связанные с мидом - рассылки по гильдиям и так далее
"""
from castle_files.libs.guild import Guild
from castle_files.libs.castle.location import Location

from castle_files.bin.guild_chats import rangers_notify_start
from castle_files.bin.api import grassroots_update_players, grassroots_update_stock, send_potion_stats, \
    update_stock_for_fails

from castle_files.work_materials.globals import job, MID_CHAT_ID, moscow_tz, local_tz, dispatcher, SUPER_ADMIN_ID, \
    high_access_list

from bin.service_functions import count_next_battle_time

from telegram.error import TelegramError


import threading
import datetime
import time


def mailing(bot, update):
    mes = update.message
    text = mes.text.partition(" ")[2]
    if len(text) <= 2:
        bot.send_message(update.message.chat_id, text="Слишком коротко.", reply_to_message_id=mes.message_id)
        return
    do_mailing(bot, text)
    if mes.text.startswith('/debrief'):
        throne = Location.get_location(2)
        format_values = throne.special_info.get("enter_text_format_values")
        format_values[1] = text
        throne.special_info.update({"enter_text_format_values": format_values})
        throne.update_location_to_database()
        bot.send_message(update.message.chat_id, text="Успешно отправлено!\n"
                                                      "Дебриф изменён", reply_to_message_id=mes.message_id)
    else:
        bot.send_message(update.message.chat_id, text="Успешно отправлено!", reply_to_message_id=mes.message_id)


def do_mailing(bot, text):
    for guild_id in Guild.guild_ids:
        guild = Guild.get_guild(guild_id=guild_id)
        if guild is None:
            continue
        if (guild.division is None or guild.division not in ["Луки", "Траст"]) and guild.mailing_enabled:
            bot.send_message(chat_id=guild.chat_id, text=text, parse_mode='HTML')


def mailing_pin(bot, update):
    threading.Thread(target=mail_and_pin, args=[bot, update]).start()


def mail_and_pin(bot, update):
    mes = update.message
    text = mes.text.partition("mailing_pin")[2]
    for guild_id in Guild.guild_ids:
        guild = Guild.get_guild(guild_id=guild_id)
        if guild is None:
            continue
        if guild.division == "Луки" or not guild.mailing_enabled:
            continue
        try:
            message = bot.sync_send_message(chat_id=guild.chat_id, text=text, parse_mode='HTML')
            bot.pinChatMessage(chat_id=message.chat_id, message_id=message.message_id)
        except TelegramError:
            pass
    bot.send_message(update.message.chat_id, text="Успешно отправлено!", reply_to_message_id=mes.message_id)


def plan_battle_jobs():
    plan_mid_notifications()
    next_battle_time = moscow_tz.localize(count_next_battle_time()).astimezone(tz=local_tz).replace(tzinfo=None)
    job.run_once(after_battle, next_battle_time)
    job.run_once(grassroots_update_players, next_battle_time - datetime.timedelta(hours=1, minutes=41, seconds=30))

    job.run_once(grassroots_update_stock, next_battle_time - datetime.timedelta(hours=0, minutes=37, seconds=39),
                 context={"change_send": False})
    job.run_once(grassroots_update_stock, next_battle_time - datetime.timedelta(hours=0, minutes=15, seconds=39),
                 context={"change_send": False})
    job.run_once(grassroots_update_stock, next_battle_time - datetime.timedelta(hours=0, minutes=7, seconds=39),
                 context={"change_send": False})
    job.run_once(grassroots_update_stock, next_battle_time - datetime.timedelta(hours=0, minutes=3, seconds=12),
                 context={"change_send": False})
    job.run_once(grassroots_update_stock, next_battle_time + datetime.timedelta(hours=0, minutes=4, seconds=0),
                 context={"change_send": True})

    # job.run_once(grassroots_update_stock, next_battle_time + datetime.timedelta(hours=0, minutes=0, seconds=1),
    #              context={"change_send": False})

    job.run_once(update_stock_for_fails, next_battle_time + datetime.timedelta(hours=0, minutes=12, seconds=0),
                 context={"change_send": True})

    job.run_once(update_stock_for_fails, next_battle_time + datetime.timedelta(hours=0, minutes=20, seconds=0),
                 context={"change_send": True})

    # job.run_once(grassroots_update_stock, 0.1, context={"change_send": True})
    # job.run_once(update_stock_for_fails, 5, context={"change_send": True})

    time_to_send = next_battle_time - datetime.timedelta(hours=1)
    now = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
    if time_to_send > now:
        job.run_once(send_potion_stats, time_to_send, context=[False])

    time_to_send = next_battle_time - datetime.timedelta(minutes=30)
    if time_to_send > now:
        job.run_once(send_potion_stats, time_to_send, context=[False])

    time_to_send = next_battle_time - datetime.timedelta(minutes=7, seconds=30)
    if time_to_send > now:
        job.run_once(send_potion_stats, time_to_send, context=[True])

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


# Заполнение списка мида, запускать при старте бота и при обновлении состава
def fill_mid_players(other_process=False):
    high_access_list.clear()
    throne = Location.get_location(2)
    if other_process:
        throne.load_location(other_process=True)
    mid_players = throne.special_info.get("mid_players")
    for player_id in mid_players:
        high_access_list.append(player_id)