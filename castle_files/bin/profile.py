"""
В этом модуле содержатся функции замкового бота для работы с профилями, как по запросу, так и в базе данных
(например, приём и обновление /hero)
"""

from castle_files.work_materials.equipment_constants import get_equipment_by_code, equipment_names
from castle_files.libs.player import Player
from castle_files.libs.guild import Guild

from castle_files.bin.buttons import get_general_buttons

import re
import logging


# Функция вывода профиля
def profile(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    response = "<b>{}</b> - Воин 🖤Скалы\n".format(player.nickname)
    response += "{}id: <code>{}</code>\n".format("@{}, ".format(player.username) if player.username is not None else "",
                                                 player.id)
    response += "🏅: <code>{}</code>, ⚔: <code>{}</code>, 🛡: <code>{}</code>\n".format(player.lvl, player.attack,
                                                                                      player.defense)
    guild = Guild.get_guild(guild_id=player.guild) if player.guild is not None else None
    response += "Гильдия: {}\n".format("<code>{}</code>".format(guild.tag) if guild is not None else "нет")
    if guild is not None:
        response += "Покинуть гильдию: /leave_guild\n"
    response += "\nЭкипировка:\n"
    eq_list = list(player.equipment.values())
    if eq_list:
        for equipment in eq_list:
            response += "<b>{}</b><code>{}</code><code>{}</code>" \
                        "\n".format(equipment.name, "+ {}⚔".format(equipment.attack) if equipment.attack is not None else "",
                                    "+ {}🛡".format(equipment.defense) if equipment.defense is not None else "")
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


# Функция для добавления или обновления профиля в базе данных, вызывается, когда бот получает хиро в лс
def hero(bot, update, user_data):
    mes = update.message
    text = mes.text
    castle = text[0]
    if castle != '🖤':
        # Игрок не из Скалы
        bot.send_message(chat_id=mes.from_user.id, text="Пользователям не из Скалы запрещена регистрация!")
        return
    player = Player.get_player(mes.from_user.id)
    if player is None and mes.chat_id != mes.from_user.id:
        # Добавление новых пользователей только в личке у бота
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
        print(string)
        clear_name = re.search("\\+?\\d?\\s?(.+?)\\s\\+", string)
        if clear_name is None:
            logging.warning("Error while parsing item_string\n{}".format(string))
            continue
        else:
            logging.info("successful parsed {},, Got: {}".format(string, clear_name.group(1)))
        clear_name = clear_name.group(1)
        names_list = list(equipment_names.items())
        code = None
        for name, item_code in names_list:
            if name in clear_name:
                code = item_code
                break
        if code is None:
            logging.warning("Item code is None for item {}".format(clear_name))
            continue
        eq = get_equipment_by_code(code)
        if eq is None:
            logging.warning("Equipment with code {} is None".format(code))
            continue
        player_equipment.update({eq.place: eq})
    if player is None:
        player = Player(mes.from_user.id, mes.from_user.username, nickname, guild_tag, None, lvl, attack, defense,
                        stamina, pet, player_equipment)
        # Добавляем игрока в бд
        player.insert_into_database()
        user_data.update({"status": "default"})
        bot.send_message(chat_id=mes.chat_id, text="Добро пожаловать в 🖤Скалу, <b>{}</b>!".format(player.nickname),
                         parse_mode='HTML', reply_markup=get_general_buttons(user_data))
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
