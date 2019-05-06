"""
В этом модуле содержатся функции замкового бота для работы с профилями, как по запросу, так и в базе данных
(например, приём и обновление /hero)
"""

from castle_files.work_materials.globals import DEFAULT_CASTLE_STATUS
from castle_files.work_materials.equipment_constants import get_equipment_by_code, equipment_names
from castle_files.libs.player import Player
from castle_files.libs.guild import Guild

from castle_files.bin.buttons import send_general_buttons
from castle_files.bin.service_functions import check_access

from castle_files.work_materials.filters.general_filters import filter_is_pm

import re
import logging
import datetime


def get_profile_text(player, self_request=True):
    response = "<b>{}</b> - Воин 🖤Скалы\n".format(player.nickname)
    response += "{}id: <code>{}</code>\n".format("@{}, ".format(player.username) if player.username is not None else "",
                                                 player.id)
    response += "🏅: <code>{}</code>, ⚔: <code>{}</code>, 🛡: <code>{}</code>\n".format(player.lvl, player.attack,
                                                                                        player.defense)
    guild = Guild.get_guild(guild_id=player.guild) if player.guild is not None else None
    response += "Гильдия: {}\n".format("<code>{}</code>".format(guild.tag) if guild is not None else "нет")
    if guild is not None and self_request:
        response += "Покинуть гильдию: /leave_guild\n"
    response += "\nЭкипировка:\n"
    eq_list = list(player.equipment.values())
    for equipment in eq_list:
        if equipment is None:
            continue
        response += "<b>{}</b><code>{}</code><code>{}</code>" \
                    "\n".format(equipment.name, "+{}⚔ ".format(equipment.attack) if equipment.attack != 0 else "",
                                "+{}🛡 ".format(equipment.defense) if equipment.defense != 0 else "")
    return response


# Функция вывода профиля
def profile(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    response = get_profile_text(player)
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


def view_profile(bot, update):
    mes = update.message
    requested_player_id = mes.from_user.id
    requested_player = Player.get_player(requested_player_id)
    guild = Guild.get_guild(guild_id=requested_player.guild)
    if not check_access(requested_player_id):
        if guild is None or not guild.check_high_access(requested_player_id):
            bot.send_message(chat_id=mes.chat_id, text="Право распоряжаться людьми необходимо заслужить.")
            return
    # Доступ к хуизу есть
    player_id = re.search("_(\\d+)", mes.text)
    if player_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return
    player_id = int(player_id.group(1))
    player = Player.get_player(player_id)
    if player is None or player.guild != guild.id:
        bot.send_message(chat_id=mes.chat_id, text="Игрок не найден.")
        return
    response = get_profile_text(player, self_request=False)
    bot.send_message(chat_id=mes.from_user.id, text=response, parse_mode='HTML')


# Функция для добавления или обновления профиля в базе данных, вызывается, когда бот получает хиро в лс
def hero(bot, update, user_data):
    mes = update.message
    text = mes.text
    castle = text[0]
    if castle != '🖤':
        # Игрок не из Скалы
        bot.send_message(chat_id=mes.from_user.id, text="Пользователям не из Скалы запрещена регистрация!")
        return
    player = Player.get_player(mes.from_user.id, notify_on_error=False)
    if player is None and mes.chat_id != mes.from_user.id:
        # Добавление новых пользователей только в личке у бота
        return
    if datetime.datetime.now() - mes.forward_date > datetime.timedelta(seconds=30):
        bot.send_message(chat_id=mes.chat_id, text="Это устаревший профиль.", reply_to_message_id=mes.message_id)
        return
    # Парсинг хиро
    guild_tag = re.search("[🍁☘🖤🐢🦇🌹🍆🎖]\\[(.+)\\]", text)
    if guild_tag:
        guild_tag = guild_tag.group(1)
    nickname = text.splitlines()[0][1:]
    lvl = int(re.search("🏅Уровень: (\\d+)", text).group(1))
    attack = int(re.search("⚔Атака: (\\d+)", text).group(1))
    defense = int(re.search("🛡Защита: (\\d+)", text).group(1))
    stamina = int(re.search("🔋Выносливость: \\d+/(\\d+)", text).group(1))
    pet = re.search("Питомец:\n.(\\s.+\\(\\d+ lvl\\))", text)
    if pet:
        pet = pet.group(1)
    # Парсинг экипировки
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
        clear_name = re.search("(⚡?\\+?\\d*\\s?(.+?))\\s\\+(\\d*)⚔?\\s*\\+?(\\d*)🛡?", string)
        if clear_name is None:
            # logging.warning("Error while parsing item_string\n{}".format(string))
            continue
        else:
            pass
            # logging.info("successful parsed {},, Got: {}".format(string, clear_name.group(1)))
        full_name = clear_name.group(1)
        eq_attack = int(clear_name.group(3)) if clear_name.group(3) != "" else 0
        eq_defense = int(clear_name.group(4)) if clear_name.group(4) != "" else 0
        clear_name = clear_name.group(2)
        names_list = list(equipment_names.items())
        code = None
        for name, item_code in names_list:
            if name in clear_name:
                code = item_code
                break
        if code is None:
            # logging.warning("Item code is None for item {}".format(clear_name))
            continue
        eq = get_equipment_by_code(code)
        if eq is None:
            logging.warning("Equipment with code {} is None".format(code))
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
                        stamina, pet, player_equipment)
        # Добавляем игрока в бд
        player.insert_into_database()
        user_data.update({"status": DEFAULT_CASTLE_STATUS, "location_id": 0})
        bot.send_message(chat_id=mes.chat_id,
                         text="Добро пожаловать в 🖤Скалу, <b>{}</b>!\n\nДля добавления информации о классе "
                              "необходимо прислать ответ @ChatWarsBot на кнопку \"🏅Герой\" (рекомендуется сделать для "
                              "получения доступа к некоторых дополнительным фишкам, особенно стражникам).\n\n"
                              "<em>Вы всегда можете отключить рп составляющую бота командой </em>/change_rp.<em> "
                              "Обратите внимание, что это сделает недоступными некоторые функции "
                              "бота.</em>".format(player.nickname),
                         parse_mode='HTML')
        if filter_is_pm(mes):
            send_general_buttons(mes.from_user.id, user_data)

    else:
        # Обновляем существующую информацию
        player.username = mes.from_user.username
        player.nickname = nickname
        player.guild_tag = guild_tag
        player.lvl = lvl
        player.attack = attack
        player.defense = defense
        player.stamina = stamina
        player.pet = pet
        player.equipment = player_equipment
        player.update()
        bot.send_message(chat_id=mes.chat_id, text="Профиль успешно обновлён, <b>{}</b>!".format(player.nickname),
                         parse_mode='HTML')
        if player.guild is not None:
            guild = Guild.get_guild(player.guild)
            guild.calculate_attack_and_defense()
            guild.sort_players_by_exp()


def add_class_from_player(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        bot.send_message(chat_id=mes.from_user.id, text="Сначала необходимо зарегистрироваться. Для этого необходимо "
                                                        "прислать ответ @ChatWarsBot на команду /hero")
        return
    if datetime.datetime.now() - mes.forward_date > datetime.timedelta(seconds=30):
        bot.send_message(chat_id=mes.chat_id, text="Это устаревший профиль.", reply_to_message_id=mes.message_id)
        return
    game_class = re.search("🖤{} (\\w+) Скалы".format(re.escape(player.nickname)), mes.text)
    if game_class is None:
        bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка.", reply_to_message_id=mes.message_id)
        return
    game_class = game_class.group(1)
    player.game_class = game_class
    player.update_to_database()
    bot.send_message(chat_id=mes.from_user.id, text="Информация о классе обновлена, <b>{}</b>! Теперь ты "
                                                    "<b>{}</b>!".format(player.nickname, player.game_class),
                     parse_mode='HTML')
