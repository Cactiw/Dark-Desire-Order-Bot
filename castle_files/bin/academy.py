"""
Здесь находятся функции для работы с гильдией АКАДЕМИЯ
"""

from castle_files.libs.guild import Guild
from castle_files.libs.player import Player

from castle_files.bin.service_functions import great_format_time

from castle_files.work_materials.globals import ACADEMY_HQ_CHAT_ID, SUPER_ADMIN_ID, moscow_tz, job

import datetime
import time
import logging


SUNDAY_INDEX = 6
ACADEMY_NOTIFY_HOUR = 12


def change_headmaster(bot, update, player, guild, user_data):
    """
    Функция изменения ректора Академии
    """
    guild.commander_id = player.id
    guild.update_to_database()
    if "status" in user_data:
        user_data.pop("status")
    if "edit_guild_id" in user_data:
        user_data.pop("edit_guild_id")
    bot.send_message(chat_id=update.message.chat_id, text="Командиром гильдии <b>{}</b> назначен <b>{}</b> "
                                                          "{}".format(guild.tag, player.nickname,
                                                                      "(@{})".format(player.username)
                                                                      if player.username is not None else ""),
                     parse_mode='HTML')


def add_teacher(bot, update):
    """
    Фукнция добавления учителя
    """
    mes = update.message
    academy = Guild.get_guild(guild_tag="АКАДЕМИЯ")
    if academy is None:
        bot.send_message(chat_id=mes.chat_id, text="Академия не найдена. Обратитесь к @Cactiw")
        return
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    if player.id != academy.commander_id:
        bot.send_message(chat_id=update.message.chat_id, text="Только глава академии может добавлять учителей.")
        return
    if mes.reply_to_message is None:
        bot.send_message(chat_id=update.message.chat_id, text="Сообщение должно являться ответом на сообщение игрока, "
                                                              "которого необходимо сделать учителем.")
        return
    player_to_add = Player.get_player(update.message.reply_to_message.from_user.id)
    if player_to_add is None:
        bot.send_message(chat_id=update.message.chat_id, text="Игрок для добавления не найден.")
        return
    if academy.check_high_access(player_to_add.id):
        bot.send_message(chat_id=update.message.chat_id, text="Игрок уже имеет необходимые права.")
        return
    academy.assistants.append(player_to_add.id)
    academy.update_to_database()
    bot.send_message(chat_id=update.message.chat_id,
                     text="<b>{}</b> теперь учитель!".format(player_to_add.nickname),
                     parse_mode='HTML', reply_to_message_id=update.message.message_id)


def del_teacher(bot, update):
    """
    Функция удаления учителя
    """
    mes = update.message
    academy = Guild.get_guild(guild_tag="АКАДЕМИЯ")
    if academy is None:
        bot.send_message(chat_id=mes.chat_id, text="Академия не найдена. Обратитесь к @Cactiw")
        return
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    if player.id != academy.commander_id:
        bot.send_message(chat_id=update.message.chat_id, text="Только глава академии может удалять учителей.")
        return
    if mes.reply_to_message is None:
        bot.send_message(chat_id=update.message.chat_id, text="Сообщение должно являться ответом на сообщение игрока, "
                                                              "которого необходимо снять с должности учителя.")
        return
    player_to_add = Player.get_player(update.message.reply_to_message.from_user.id)
    if player_to_add is None:
        bot.send_message(chat_id=update.message.chat_id, text="Игрок для удаления не найден.")
        return
    if academy.commander_id == player_to_add.id:
        bot.send_message(chat_id=update.message.chat_id, text="Нельзя снять главу академии.")
        return
    if not academy.check_high_access(player_to_add.id):
        bot.send_message(chat_id=update.message.chat_id, text="Игрок и так не учитель.")
        return
    academy.assistants.remove(player_to_add.id)
    academy.update_to_database()
    bot.send_message(chat_id=update.message.chat_id,
                     text="<b>{}</b> больше не учитель!".format(player_to_add.nickname),
                     parse_mode='HTML', reply_to_message_id=update.message.message_id)


def send_guilds_stats(bot, job):
    """
    Раз в неделю отправляет в штаб академки инфу о текущем составе гильдий
    """
    response = "Гильдии Скалы на {}:\n" \
               "<em>👥 - число игроков по боту, 👥(API) - число игроков в ги по АПИ, 🏅 - уровень гильдии</em>\n" \
               "".format(datetime.date.today().strftime("%d/%m/%y"))
    for guild_id in Guild.guild_ids:
        guild = Guild.get_guild(guild_id)
        if not guild.is_active():
            continue
        if guild.castle != "🖤":
            continue
        lvl, members = guild.api_info.get("lvl"), guild.api_info.get("members")
        response += "<b>{}</b> 👥{} {}\n".format(guild.tag, guild.members_count,
                                                "(API - {}) 🏅{}".format(members, lvl) if lvl else "")
    bot.send_message(chat_id=ACADEMY_HQ_CHAT_ID, text=response, parse_mode='HTML')

    time.sleep(1)
    plan_academy_guilds_stats_send()


def plan_academy_guilds_stats_send():
    today = datetime.date.today()
    target = datetime.datetime.combine(today + datetime.timedelta(days=SUNDAY_INDEX - today.weekday()),
                                       datetime.time(ACADEMY_NOTIFY_HOUR))
    if target - datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None) < datetime.timedelta(0):
        # Время уже прошло, планируем на следующую неделю
        target += datetime.timedelta(days=7)
    job.run_once(send_guilds_stats, target)
    logging.info("Academy guild stats notify planned on {}".format(great_format_time(target)))

