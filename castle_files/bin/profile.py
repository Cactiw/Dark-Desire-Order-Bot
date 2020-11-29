"""
В этом модуле содержатся функции замкового бота для работы с профилями, как по запросу, так и в базе данных
(например, приём и обновление /hero)
"""

from castle_files.work_materials.globals import DEFAULT_CASTLE_STATUS, cursor, moscow_tz, construction_jobs, MERC_ID, \
    classes_to_emoji, dispatcher, class_chats, CASTLE_BOT_ID, SUPER_ADMIN_ID, king_id, conn, utc, castle_chats
from castle_files.work_materials.equipment_constants import get_equipment_by_code, get_equipment_by_name
from castle_files.libs.player import Player
from castle_files.libs.guild import Guild
from castle_files.libs.castle.location import Location

from castle_files.bin.buttons import send_general_buttons, get_profile_buttons, get_profile_settings_buttons
from castle_files.bin.service_functions import check_access, dict_invert, plan_work, count_battle_id, \
    get_forward_message_time, get_message_forward_time
from castle_files.bin.reports import count_battle_time
from castle_files.bin.statuses import get_status_text_by_id, get_status_message_by_text
from castle_files.bin.api import auth
from castle_files.bin.quest_triggers import on_doc_status

from castle_files.work_materials.filters.general_filters import filter_is_pm
from castle_files.work_materials.level_constants import levels

from telegram.error import TelegramError

import re
import logging
import traceback
import datetime
import random
import json


class_chats_inverted = dict_invert(class_chats)


def revoke_all_class_links(bot, update):
    if not check_access(update.message.from_user.id):
        return
    barracks = Location.get_location(1)
    barracks.special_info.update({"class_links": {}})
    barracks.update_location_to_database()
    bot.send_message(chat_id=update.message.chat_id, text="Все ссылки сброшены!")


def revoke_class_link(game_class):
    chat_id = class_chats.get(game_class)
    if chat_id is None:
        return -1
    barracks = Location.get_location(1)
    class_links = barracks.special_info.get("class_links")
    if class_links is None:
        class_links = {}
        barracks.special_info.update({"class_links": class_links})
    try:
        invite_link = dispatcher.bot.exportChatInviteLink(chat_id)
        if invite_link is not None:
            invite_link = invite_link[22:]  # Обрезаю https://t.me/joinchat/
            class_links.update({game_class: invite_link})
            barracks.update_location_to_database()
    except TelegramError:
        logging.error(traceback.format_exc())
        return 1


def class_chat_check(mes):
    if mes.from_user.id in [CASTLE_BOT_ID, SUPER_ADMIN_ID, king_id] or check_access(mes.from_user.id):
        return False
    if mes.new_chat_members is not None:
        users = mes.new_chat_members
    else:
        users = [mes.from_user]
    for user in users:
        player = Player.get_player(user.id)
        if player is None or player.game_class is None or class_chats.get(player.game_class) != mes.chat_id or \
                player.castle != '🖤':
            return True
    return False


def class_chat_player_check(player_id, chat_id):
    player = Player.get_player(player_id)
    if player is None or player.game_class is None or class_chats.get(player.game_class) != chat_id or \
            player.castle != '🖤':
        return True
    return False


def class_chat_kick(bot, update):
    mes = update.message
    if mes.new_chat_members is not None:
        users = mes.new_chat_members
    else:
        users = [update.message.from_user]
    for user in users:
        if class_chat_player_check(user.id, mes.chat_id):
            try:
                cl = class_chats_inverted.get(mes.chat_id)
                text = "Это чат <b>{}</b>. Он не для тебя.".format(cl)
                if mes.chat_id == class_chats.get('Sentinel'):
                    text = "Ты зашел в чат Б-гоизбранных Стражей Скалы. Но этот чат не для тебя, ничтожество. " \
                           "Иди погуляй, алебарду тебе в задницу"
                bot.kickChatMember(chat_id=mes.chat_id, user_id=user.id)
                bot.send_message(chat_id=mes.chat_id,
                                 text=text, parse_mode='HTML')
            except TelegramError:
                return


def castle_chat_check(message):
    if message.new_chat_members:
        users = message.new_chat_members
    else:
        users = [message.from_user]
    for user in users:
        player = Player.get_player(user.id)
        if message.from_user.id in [CASTLE_BOT_ID, SUPER_ADMIN_ID, king_id] or check_access(message.from_user.id):
            return False
        if player is None:
            return True
        if player is None or player.castle != '🖤':
            return True
    return False


def remove_players_from_chat(bot, update):
    message = update.message
    if message.new_chat_members:
        users = message.new_chat_members
    else:
        users = [message.from_user]
    for user in users:
        user_id = user.id
        player = Player.get_player(user.id)
        if message.from_user.id in [CASTLE_BOT_ID, SUPER_ADMIN_ID, king_id] or check_access(message.from_user.id):
            return
        if player is None or player.castle != '🖤':
            try:
                text = "Этот чат только для игроков 🖤Скалы"
                bot.kickChatMember(chat_id=message.chat_id, user_id=user_id)
                bot.send_message(chat_id=message.chat_id,
                                 text=text, parse_mode='HTML')
            except TelegramError:
                pass


def set_castle_chat(bot, update):
    mes = update.message
    if mes.from_user.id != SUPER_ADMIN_ID and not check_access(mes.from_user.id):
        return
    if mes.chat_id == mes.from_user.id:
        bot.send_message(chat_id=mes.chat_id, text="Команда запрещена в ЛС")
        return
    on = 'on' in update.message.text
    if on:
        if mes.chat_id in castle_chats:
            bot.send_message(chat_id=mes.chat_id, text="Чат уже установлен как замковый")
            return
        castle_chats.append(mes.chat_id)
        text = "Чат отмечен как замковый. Бот будет удалять любых участников не из Скалы, " \
               "или с отсутствующими профилями"
    else:
        if mes.chat_id not in castle_chats:
            bot.send_message(chat_id=mes.chat_id, text="Чат и так не замковый")
            return
        castle_chats.remove(mes.chat_id)
        text = "Теперь чат разрешён для всех участников."
    bot.send_message(chat_id=mes.chat_id, text=text)


def get_profile_text(player, self_request=True, user_data=None, requested_player=None):
    barracks = Location.get_location(1)
    class_links = barracks.special_info.get("class_links")
    if class_links is None:
        class_links = {}
        barracks.special_info.update({"class_links": class_links})
    try:
        class_format = (classes_to_emoji.get(player.game_class, "❔") + player.game_class) if \
            player.game_class is not None else "Воин"
    except Exception:
        class_format = "Воин"
        logging.error(traceback.format_exc())
        logging.error("id:{} nickname:{} class:{} username:{}".format(player.id, player.nickname,
                                                                      player.game_class, player.username))
    response = "<b>{}</b> - {} {}\n".format(player.nickname, class_format,
                                            "🖤Скалы" if player.castle == '🖤' else player.castle)
    response += "{}id: <code>{}</code>, ".format("@{}, ".format(player.username) if player.username is not None else "",
                                                 player.id)
    if user_data is None:
        user_data = dispatcher.user_data.get(player.id)
    if player.status is not None:
        response += "Статус: <b>{}</b>\n".format(get_status_text_by_id(player.status, player.id))
    response += "🏅: <code>{}</code>, 🔥: <code>{}</code> ⚔: <code>{}</code>, 🛡: <code>{}</code>" \
                "\n".format(player.lvl, player.exp or "???", player.attack, player.defense)
    response += ("👝: {}, ".format(player.pogs) if player.pogs is not None else "") + \
                ("❤️: {}, ".format(player.hp) if player.hp else "") + \
                ("💧: {}, ".format(player.mana) if player.mana else "") + \
        "🔘: <code>{}</code>\n".format(player.reputation)
    guild = Guild.get_guild(guild_id=player.guild) if player.guild is not None else None
    response += "Гильдия: {} | {}/{}🔋\n".format("<code>{}</code>".format(guild.tag) if guild is not None else "нет",
                                                player.stamina, player.max_stamina)
    if guild is not None and self_request:
        response += "Покинуть гильдию: /leave_guild\n"
    elif guild is not None and guild.check_high_access(requested_player.id) and \
            (requested_player.guild == guild.id or guild.is_academy()):
        response += "Удалить из гильдии: /remove_player_{}\n".format(player.id)
    if self_request:
        if player.game_class is not None and player.castle == '🖤' and player.game_class not in ['Master', 'Esquire']:
            try:
                if class_links.get(player.game_class) is None:
                    revoke_class_link(player.game_class)
                invite_link = class_links.get(player.game_class)
                response += "<a href=\"{}\">\n📚Классовый чат</a>\n".format("https://t.me/joinchat/" + invite_link)
            except Exception:
                logging.error(traceback.format_exc())
    response += "\nЭкипировка:\n"
    eq_list = list(player.equipment.values())
    for equipment in eq_list:
        if equipment is None:
            continue
        response += equipment.format()

    r1, r2, r3 = player.get_reports_count()

    try:
        if guild is not None and guild.commander_id == player.id:
            response += "\n<b>🎗Командир гильдии</b>\n"
        if guild is not None and player.id in guild.assistants:
            response += "\n<b>🎗Зам командира гильдии</b>\n"
    except Exception:
        logging.error(traceback.format_exc())

    response += "\nРепорты(эта неделя / прошлая / всего): <code>{}</code> / <code>{}</code> / <code>{}</code>" \
                "\n".format(r1, r2, r3)
    response += "Регистрация в боте: <code>{}</code>\n".format(player.created.strftime("%d/%m/%y %H:%M:%S") if
                                                                 player.created is not None else "Оппозит")
    response += "Последнее обновление профиля: " \
                "<code>{}</code>\n".format(player.last_updated.strftime("%d/%m/%y %H:%M:%S") if
                                           player.last_updated is not None else "неизвестно")
    if user_data is None:
        return response
    status = user_data.get("status")
    if status is not None and status in ["sawmill", "quarry", "construction"] or "quest_name" in user_data:
        if "quest_name" in user_data:
            quest_name = user_data.get("quest_name")
            response += "\n<b>Вы {}. Это займёт несколько минут.</b>" \
                        "".format("на разведке" if quest_name == 'exploration' else
                                  "копаете котлован" if quest_name == 'pit' else "")
        else:
            if player is not None:
                j = construction_jobs.get(player.id)
                if j is not None:
                    seconds_left = j.get_time_left()
                    response += "\nВы заняты делом. Окончание через <b>{:02.0f}:{:02.0f}</b>" \
                                "".format(seconds_left // 60, (seconds_left % 60) // 1)
    return response


# Функция вывода профиля
def profile(bot, update, user_data=None):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    response = get_profile_text(player, user_data=user_data)
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML',
                     reply_markup=get_profile_buttons(player, whois_access=True, self_request=True),
                     disable_web_page_preview=True)


trade_divisions_access_list = [320365073, 407981701, 98625707, 205356091, 491614325, 374281599, 116028074, 284826167,
                               133078153, 401404607, 681483083]
# Игроки, которым дал доступ к хуизу в связи с альянсами


def check_whois_access(user_id):
    try:
        return check_access(user_id) or user_id == MERC_ID or user_id in trade_divisions_access_list or \
               Guild.get_guild(guild_tag="АКАДЕМИЯ").check_high_access(user_id)
    except Exception:
        return False


def view_profile(bot, update):
    mes = update.message
    requested_player_id = mes.from_user.id
    requested_player = Player.get_player(requested_player_id)
    if requested_player is None:
        return
    has_access = True
    guild = Guild.get_guild(guild_id=requested_player.guild)
    if not check_whois_access(requested_player_id):
        if guild is None or not guild.check_high_access(requested_player_id):
            # bot.send_message(chat_id=mes.chat_id, text="Право распоряжаться людьми необходимо заслужить.",
            #                  reply_to_message_id=mes.message_id)
            has_access = False
    # Доступ к хуизу есть
    reply = False
    if mes.text.startswith("/dok") or mes.text.startswith("/doc"):
        if mes.reply_to_message is not None:
            #  Реплай в чате
            reply = True
            player_ids = [mes.reply_to_message.from_user.id]
        elif has_access is False:
            return
        elif "@" in update.message.text:
            # Поиск по юзерке
            player_ids = []
            for username in mes.text.split()[1:]:
                request = "select id from players where username = %s"
                cursor.execute(request, (username.partition("@")[2],))
                row = cursor.fetchone()
                if row is None:
                    bot.send_message(chat_id=mes.chat_id, text="Игрок {} не найден.".format(username))
                    continue
                player_ids.append(row[0])
            if not player_ids:
                return
        else:
            # Поиск по нику в игре
            request = "select id from players where lower(nickname) = %s or lower(nickname) like %s"
            # print(request % mes.text.partition(" ")[2] % "%]" + mes.text.partition(" ")[2])
            cursor.execute(request, (mes.text.partition(" ")[2].lower(), "%]" + mes.text.partition(" ")[2].lower()))
            row = cursor.fetchone()
            if row is None:
                bot.send_message(chat_id=mes.chat_id, text="Игрок не найден.")
                return
            player_ids = [row[0]]
    else:
        player_id = re.search("_(\\d+)", mes.text)
        player_ids = [int(player_id.group(1))]
    if not player_ids:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return
    for player_id in player_ids:
        player = Player.get_player(player_id)
        if player is None or (mes.text.startswith("/view_profile") and (guild is None or player.guild != guild.id)):
            if player is not None and player.guild is not None:
                guild = Guild.get_guild(player.guild)
                if guild is not None:
                    if requested_player_id in guild.assistants or requested_player_id == guild.commander_id:
                        pass
                    else:
                        bot.send_message(chat_id=mes.chat_id, text="Игрок не найден.")
                        return
        if reply and player.status is not None:
            # Сообщение со статусом
            bot.send_message(chat_id=mes.chat_id, text=get_status_message_by_text(
                get_status_text_by_id(player.status, player.id)), parse_mode='HTML', reply_to_message_id=mes.message_id)
            on_doc_status(requested_player)
        if not has_access:
            bot.send_message(chat_id=mes.chat_id, text="Право распоряжаться людьми необходимо заслужить.",
                             reply_to_message_id=mes.message_id)
            return
        buttons = get_profile_buttons(player)
        if (player.guild is None or player.guild != requested_player.guild) and not check_whois_access(requested_player_id):
            guild = Guild.get_guild(guild_id=player.guild)
            bot.send_message(chat_id=mes.from_user.id,
                             text="Вы не знаете этого человека, однако его форма позволяет вам сделать вывод, что он "
                                  "служит {}".format("в гильдии <b>{}</b>".format(guild.tag) if guild is not None else
                                                     "как вольный наёмник (без гильдии)"),
                             parse_mode='HTML', reply_markup=buttons)
            return
        buttons = get_profile_buttons(player, whois_access=True)
        response = get_profile_text(player, self_request=False, requested_player=requested_player)
        bot.send_message(chat_id=mes.from_user.id, text=response, parse_mode='HTML', reply_markup=buttons)


def guild_history(bot, update):
    data = update.callback_query.data
    mes = update.callback_query.message
    requested_player_id = re.search("_(\\d+)", data)
    if requested_player_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка. Попробуйте вызвать сообщение заного.")
        return
    requested_player_id = int(requested_player_id.group(1))
    player = Player.get_player(player_id=update.callback_query.from_user.id)
    if player is None:
        return
    player_guild = Guild.get_guild(player.guild) if player.guild is not None else None
    if player.id != requested_player_id:
        if not check_whois_access(player.id) and (
                player_guild is None or (player_guild is not None and not player_guild.check_high_access(player.id))):
            bot.answerCallbackQuery(callback_query_id=update.callback_query.id)
            bot.send_message(chat_id=mes.chat_id, text="Доступ запрещён.")
            return
    requested_player = Player.get_player(requested_player_id, notify_on_error=False)
    if requested_player is None:
        bot.send_message(chat_id=mes.chat_id, text="Игрок не найден.")
        return
    if requested_player.guild_history is None:
        requested_player.guild_history = []
    response = "Гильдии, в которых состоял <b>{}</b>:\n<em>Выше — позже</em>\n\n".format(requested_player.nickname)
    for i, guild_id in enumerate(requested_player.guild_history):
        guild = Guild.get_guild(guild_id)
        if guild is None:
            continue
        commander = Player.get_player(guild.commander_id)
        if commander is None:
            continue
        response += "<b>{}</b>, <code>{:3<}</code>: Командир: <b>{}</b> - @{}" \
                    "\n".format(i + 1, guild.tag, commander.nickname, commander.username)
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


def reports_history(bot, update):
    data = update.callback_query.data
    mes = update.callback_query.message
    player = Player.get_player(player_id=update.callback_query.from_user.id)
    if player is None:
        return

    requested_player_id = re.search("_(\\d+)", data)
    if requested_player_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка. Попробуйте вызвать сообщение заного.")
        return
    requested_player_id = int(requested_player_id.group(1))

    requested_player = Player.get_player(requested_player_id, notify_on_error=False)
    if requested_player is None:
        bot.send_message(chat_id=mes.chat_id, text="Игрок не найден.")
        return
    if player.id != requested_player.id and not check_whois_access(player.id) and (
            requested_player.guild is None or requested_player.guild != player.guild):
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id)
        bot.send_message(chat_id=mes.chat_id, text="Доступ запрещён.")
        return
    response = "Отчёты по последним битвам <b>{}</b>:\n".format(requested_player.nickname)
    request = "select battle_id, attack, defense, exp, gold, stock from reports where player_id = %s order by " \
              "battle_id desc limit 30"
    cursor.execute(request, (requested_player.id,))
    row = cursor.fetchone()
    while row is not None:
        response += "🕒{} ⚔️:<code>{:<3},🛡:{:<3},🔥:{:<4},💰:{:<3},📦:{:<3}</code>" \
                    "\n".format(count_battle_time(row[0]).strftime("%H:%M %d/%m"), row[1], row[2], row[3], row[4],
                                row[5])
        row = cursor.fetchone()
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


urned_players = [29821655]


# Функция для добавления или обновления профиля в базе данных, вызывается, когда бот получает хиро в лс
def hero(bot, update, user_data):
    mes = update.message
    text = mes.text
    castle = re.search("([🍁☘️🖤🐢🦇🌹🍆🎖]+)(.+)", text)
    nickname = castle.group(2)
    castle = castle.group(1)
    if castle != '🖤':
        pass
        # Игрок не из Скалы
        # bot.send_message(chat_id=mes.from_user.id, text="Пользователям не из Скалы запрещена регистрация!")
        # return
    player = Player.get_player(mes.from_user.id, notify_on_error=False)
    if player is not None and player.id == 402027858 and player.castle != '🖤' and castle == '🖤':
        # Рыбак вернулся!
        bot.send_message(chat_id=player.id,
                         text="Стражи с гулким стуком ударяют копьями о землю. Врата медленно "
                              "отворяются, открывая взору такие знакомые, но в то же время изменившиеся улицы.\n"
                              "<b>С возвращением домой!</b>", parse_mode='HTML')
    if player is None and mes.chat_id != mes.from_user.id:
        # Добавление новых пользователей только в личке у бота
        return
    forward_message_date = get_forward_message_time(mes)
    print(forward_message_date)
    if datetime.datetime.now() - forward_message_date > datetime.timedelta(seconds=30) and \
            mes.from_user.id not in urned_players:
        bot.send_message(chat_id=mes.chat_id, text="Этот профиль старше 30 секунд. Пришли актуальный профиль!",
                         reply_to_message_id=mes.message_id)
        return
    # Парсинг хиро
    guild_tag = re.search("[🍁☘🖤🐢🦇🌹🍆🎖]\\[(.+)\\]", text)
    if guild_tag:
        guild_tag = guild_tag.group(1)
    lvl = int(re.search("🏅Уровень: (\\d+)", text).group(1))
    attack = int(re.search("⚔Атака: (\\d+)", text).group(1))
    defense = int(re.search("🛡Защита: (\\d+)", text).group(1))
    stamina = re.search("🔋Выносливость: (\\d+)/(\\d+)", text)
    stamina, max_stamina = tuple(map(lambda x: int(x), stamina.groups()))
    pet = re.search("Питомец:\n.(\\s.+\\(\\d+ lvl\\))", text)
    exp = int(re.search("🔥Опыт: (\\d+)", text).group(1))
    last_updated = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
    if pet:
        pet = pet.group(1)
    # Парсинг экипировки
    print("parsing eq")
    player_equipment = {
        "main_hand": None,
        "second_hand": None,
        "head": None,
        "gloves": None,
        "armor": None,
        "boots": None,
        "cloaks": None
    }
    equip_strings = text.partition("🎽Экипировка")[2].splitlines()[1:]
    for string in equip_strings:
        # clear_name = re.search("\\+?\\d?\\s?(.+?)\\s\\+", string)
        clear_name = re.search("(⚡?\\+?\\d*\\s?(.+?))\\s\\+((\\d*)⚔)?\\s*\\+?(\\d*)🛡?", string)
        if clear_name is None:
            # logging.warning("Error while parsing item_string\n{}".format(string))
            continue
        else:
            pass
            # logging.info("successful parsed {},, Got: {}".format(string, clear_name.group(1)))
        full_name = clear_name.group(1)
        eq_attack = int(clear_name.group(4)) if clear_name.group(4) is not None and clear_name.group(4) != "" else 0
        eq_defense = int(clear_name.group(5)) if clear_name.group(5) != "" else 0
        clear_name = clear_name.group(2)
        eq = get_equipment_by_name(clear_name)
        if eq is None:
            logging.warning("Equipment with name {} is None".format(clear_name))
            continue
        eq.name = full_name
        eq.attack = eq_attack
        eq.defense = eq_defense
        player_equipment.update({eq.place: eq})
    if player is None:
        if mes.from_user.username is None:
            bot.send_message(chat_id=mes.chat_id, text="Регистрация без имени пользователя невозможна. Пожалуйста, "
                                                       "установите его в настройках аккаунта Telegram")
            return
        player = Player(mes.from_user.id, mes.from_user.username, nickname, guild_tag, None, lvl, attack, defense,
                        stamina, pet, player_equipment, castle=castle, last_updated=last_updated, created=last_updated,
                        exp=exp, max_stamina=max_stamina)
        # Добавляем игрока в бд
        player.insert_into_database()
        player = player.reload_from_database()

        user_data.update({"status": DEFAULT_CASTLE_STATUS, "location_id": 0})
        bot.send_message(chat_id=mes.chat_id,
                         text="Добро пожаловать в 🖤Скалу, <b>{}</b>!\n\n<a href=\"https://t.me/joinchat/DdKE7kUfsmDVIC2DJymw_A\">Чат центральной площади</a>\n\nДля добавления информации о классе "
                              "необходимо прислать ответ @ChatWarsBot на кнопку \"🏅Герой\" (рекомендуется сделать для "
                              "получения доступа к некоторых дополнительным фишкам, особенно стражникам).\n\n"
                              "<em>Вы всегда можете отключить рп составляющую бота командой </em>/change_rp.<em> "
                              "Обратите внимание, что это сделает недоступными некоторые функции "
                              "бота.</em>".format(player.nickname),
                         parse_mode='HTML')
        if filter_is_pm(mes):
            send_general_buttons(mes.from_user.id, user_data)
        auth(bot, update)

    else:
        # Обновляем существующую информацию
        player.username = mes.from_user.username
        player.nickname = nickname
        player.guild_tag = guild_tag
        player.lvl = lvl
        player.attack = attack
        player.defense = defense
        player.stamina = stamina
        player.max_stamina = max_stamina
        player.pet = pet
        player.equipment = player_equipment
        player.castle = castle
        player.last_updated = last_updated
        player.exp = exp
        player.update()
        bot.send_message(chat_id=mes.chat_id, text="Профиль успешно обновлён, <b>{}</b>!".format(player.nickname),
                         parse_mode='HTML')
        if player.guild is not None:
            guild = Guild.get_guild(player.guild)
            guild.calculate_attack_and_defense()
            guild.sort_players_by_exp()


def get_profile_settings_text(player):
    response = "{}<b>{}</b>\n<em>⚙Настройки:</em>\n\n".format(player.castle, player.nickname)
    settings = player.settings
    if settings is None:
        settings = {}
        player.settings = settings
    sold_notify, stock_change, rangers_notify, mobs_notify = settings.get("sold_notify"), settings.get("stock_change"),\
        settings.get("rangers_notify"), settings.get("mobs_notify")
    if sold_notify is None:
        sold_notify = True
    response += "<code>{:<26}</code> <b>{}</b>\n".format("🛒Уведомления о продаже",
                                                         "✅включены" if sold_notify else "❌отключены")
    if stock_change is None:
        stock_change = True
    response += "<code>{:<26}</code> <b>{}</b>\n".format("📦Изменения в стоке",
                                                         "✅включены" if stock_change else "❌отключены")
    # if player.game_class == 'Ranger' and player.class_skill_lvl is not None:
    if player.class_skill_lvl is not None:
        if rangers_notify is None:
            rangers_notify = True
        response += "<code>{:<26}</code> <b>{}</b>\n".format("📌Пинг на аим",
                                                             "✅включён" if rangers_notify else "❌отключён")

    if mobs_notify is None:
        mobs_notify = True
    response += "<code>{:<26}</code> <b>{}</b>\n".format("📌Пинг на мобов",
                                                         "✅включен" if mobs_notify else "❌отключен")

    autospend = settings.get("autospend", False)
    response += "<code>{:<26}</code> <b>{}</b>\n".format(
        "💰Автослив золота", "✅включен" if autospend else "❌отключен"
    )
    return response


def profile_settings(bot, update):
    data = update.callback_query.data
    mes = update.callback_query.message
    player = Player.get_player(update.callback_query.from_user.id)
    if player is None:
        return
    response = get_profile_settings_text(player)
    buttons = get_profile_settings_buttons(player)
    bot.send_message(chat_id=update.callback_query.from_user.id, text=response, parse_mode='HTML', reply_markup=buttons)
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)
    print(response)
    pass


def change_profile_setting(bot, update):
    data = update.callback_query.data
    mes = update.callback_query.message
    player = Player.get_player(update.callback_query.from_user.id)
    if player is None:
        return
    set = {"prsstocknotify": "stock_change", "prssoldnotify": "sold_notify", "prsaimping": "rangers_notify",
           "prsmobsping": "mobs_notify"}
    setting = set.get(data.partition("_")[0])
    state = player.settings.get(setting)
    if state is None:
        state = True
    player.settings.update({setting: not state})
    player.update()
    response = get_profile_settings_text(player)
    buttons = get_profile_settings_buttons(player)
    bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=response, parse_mode='HTML',
                        reply_markup=buttons)
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


def add_class_from_player(bot, update):
    translate = {
        "рыцарь": "Knight",
        "защитник": "Sentinel",
        "рейнджер": "Ranger",
        "алхимик": "Alchemist",
        "кузнец": "Blacksmith",
        "добытчик": "Collector",
    }
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        bot.send_message(chat_id=mes.from_user.id, text="Сначала необходимо зарегистрироваться. Для этого необходимо "
                                                        "прислать ответ @ChatWarsBot на команду /hero")
        return
    forward_message_date = get_forward_message_time(mes)
    if datetime.datetime.now() - forward_message_date > datetime.timedelta(seconds=30):
        bot.send_message(chat_id=mes.chat_id, text="Этот профиль старше 30 секунд. Пришли актуальный профиль!",
                         reply_to_message_id=mes.message_id)
        return
    game_class = re.search("🖤{} (\\w+) Скалы".format(re.escape(player.nickname)), mes.text)
    if game_class is None:
        bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка.", reply_to_message_id=mes.message_id)
        return
    game_class = game_class.group(1)
    if game_class.lower() in translate:
        game_class = translate.get(game_class.lower())
    player.game_class = game_class
    player.update_to_database()
    bot.send_message(chat_id=mes.from_user.id, text="Информация о классе обновлена, <b>{}</b>! Теперь ты "
                                                    "<b>{}</b>!".format(player.nickname, player.game_class),
                     parse_mode='HTML')


def update_ranger_class_skill_lvl(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    if player.game_class != 'Ranger':
        # bot.send_message(chat_id=mes.chat_id,
        #                  text="Учёт уровня скиллов пока доступен только лучникам. Для добавления информации о классе "
        #                       "необходимо прислать ответ @ChatWarsBot на кнопку \"🏅Герой\"")
        # return
        pass  # Reborned players can have a different class
    class_skill = int(mes.text.partition("Aiming")[0][:-2].split()[-1])
    logging.info("class_skill = {0}".format(class_skill))
    player.class_skill_lvl = class_skill
    player.update()
    bot.send_message(chat_id=mes.from_user.id, text="Информация о скиллах обновлена, <b>{}</b>".format(player.nickname),
                     parse_mode='HTML')


def profile_exp(bot, update):
    data = update.callback_query.data
    mes = update.callback_query.message
    player_id = re.search("_(\\d+)", data)
    if player_id is None:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                                text="Произошла ошибка. Попробуйте открыть все меню сначала.")
        return
    player_id = int(player_id.group(1))
    player = Player.get_player(player_id)
    if player is None:
        return
    response = "Изменения в опыте <b>{}</b>:\n".format(player.nickname)
    previous_exp = None
    print(player.exp_info)
    if not player.exp_info:
        response += "<em>Пусто</em>"
    else:
        for battle_id, exp in list(player.exp_info.items())[-14:]:
            battle_id = int(battle_id)
            if previous_exp is not None:
                response += "{}: +🔥<code>{}</code>\n".format(count_battle_time(battle_id).strftime("%d/%m/%y"),
                                                              exp - previous_exp)
            previous_exp = exp
        response += "{}: +🔥<code>{}</code>" \
                    "\n".format(datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None).strftime("%d/%m/%y"),
                                player.exp - previous_exp)
        prediction_data = list(player.exp_info.values())[-4:]
        prediction_data = [prediction_data[i] - prediction_data[i - 1] for i in range(1, len(prediction_data))]
        if prediction_data:
            avg_exp = sum(prediction_data) / len(prediction_data)
            need_reach = levels.get(player.lvl + 1, {}).get("exp")
            if need_reach is not None:
                remain = need_reach - player.exp
                if remain < 0:
                    logging.error("Wrong info about level exp: {} {} {}".format(player.nickname, player.lvl, player.exp))
                else:
                    response += "\nВ среднем <code>{}</code>🔥 в день.\n" \
                                "До следующего уровня приблизительно <b>{}</b> дней.".format(
                                    int(avg_exp),
                                    int(remain // avg_exp) + (1 if remain % avg_exp else 0) if avg_exp > 0 else "❔"
                        )

    bot.send_message(chat_id=update.callback_query.from_user.id, text=response, parse_mode='HTML')
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


def remember_exp(bot, job):
    cursor = conn.cursor()
    request = "select id, exp, exp_info from players"
    cursor.execute(request)
    rows = cursor.fetchall()
    battle_id = count_battle_id(None)
    for row in rows:
        player_id, exp, exp_info = row
        player = Player.get_player(player_id)
        if exp_info is None:
            exp_info = {}
        exp_info.update({str(battle_id): exp})
        exp_info = {k: v for k, v in sorted(list(exp_info.items()), key=lambda x: int(x[0]))}
        player.exp_info = exp_info
        player.update()
        # request = "update players set exp_info = %s where id = %s"
        # cursor.execute(request, (json.dumps(exp_info, ensure_ascii=False), player_id))
    plan_remember_exp()


def plan_remember_exp():
    plan_work(remember_exp, 0, 0, 0)
    # remember_exp(None, None)


def get_rangers(bot, update):
    mes = update.message
    if not check_whois_access(mes.from_user.id):
        return
    response = "Лучники 🖤Скалы:\n"
    request = "select '@' || username, nickname, lvl from players where game_class = 'Ranger' order by lvl desc"
    cursor.execute(request)
    row = cursor.fetchone()
    while row is not None:
        response += "{} <b>{}</b> 🏅:{}\n".format(*row)
        row = cursor.fetchone()
    bot.send_message(chat_id=mes.from_user.id, text=response, parse_mode='HTML')


def set_status(bot, update):
    mes = update.message
    if not check_access(mes.from_user.id):
        return
    parse = re.search("set_status (\\d+) (.*)", mes.text)
    if parse is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис", reply_to_message_id=mes.message_id)
        return
    player_id = int(parse.group(1))
    new_status = parse.group(2)
    player = Player.get_player(player_id, notify_on_error=False)
    if player is None:
        bot.send_message(chat_id=mes.chat_id, text="Игрок не найден.", reply_to_message_id=mes.message_id)
        return
    if new_status == "":
        player.status = None
    else:
        player.status = new_status
    player.update()
    bot.send_message(chat_id=mes.chat_id, text="Обновление статуса успешно!", reply_to_message_id=mes.message_id)

