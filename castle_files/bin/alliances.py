
from castle_files.libs.player import Player
from castle_files.libs.guild import Guild
from castle_files.libs.alliance import Alliance, AllianceResults
from castle_files.libs.alliance_location import AllianceLocation

from castle_files.bin.service_functions import get_time_remaining_to_battle

from castle_files.work_materials.globals import dispatcher, cursor, job

import logging
import traceback
import re
import time


def get_player_and_guild_and_alliance(player_id: int):
    player = Player.get_player(player_id, notify_on_error=False)
    guild = Guild.get_guild(player.guild) if player is not None else None
    alliance = Alliance.get_alliance(guild.alliance_id) if guild is not None else None
    return player, guild, alliance


def add_alliance_location(bot, update):
    mes = update.message
    player, guild, alliance = get_player_and_guild_and_alliance(mes.from_user.id)
    try:
        parse = re.search("You found hidden location (\\w+) lvl.(\\d+)", mes.text)
        name, lvl = parse.group(1), int(parse.group(2))
        parse = re.search("simple combination: (\\w+)", mes.text)
        link = parse.group(1)
    except Exception:
        logging.error(traceback.format_exc())
        bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка")
        return
    request = "select id from alliance_locations where link = %s"
    cursor.execute(request, (link,))
    row = cursor.fetchone()
    if row is not None:
        return
    request = "select id from alliance_locations where name = %s and lvl = %s and link is null " \
              "and expired is not false limit 1"
    cursor.execute(request, (name, lvl))
    row = cursor.fetchone()
    if row is not None:
        location = AllianceLocation.get_location(row[0])
        location.link = link
        location.update()
    else:
        location = AllianceLocation(None, link, name, None, lvl, None, 0, False)
        location.figure_type()
        location.insert_to_database()
    if alliance is not None and alliance.hq_chat_id is not None:
        bot.send_message(chat_id=alliance.hq_chat_id, parse_mode='HTML',
                         text="Новая локация: <b>{} Lvl.{}</b>\n{}".format(name, lvl, link))


def plan_clear_alliance_results(*args):
    job.run_once(clear_results, get_time_remaining_to_battle())


def clear_results(*args):
    AllianceResults.clear()
    time.sleep(1)
    plan_clear_alliance_results()



def get_hq_battle_emoji(result, attack, defense) -> str:
    emojis = {
        "defended successfully": "🛡",
        "closely defended": "🔱🛡⚡️",
        "easily breached": "⚔️😎",
        "breached": "⚔️",
        "closely breached": "⚔️⚡️",
    }
    if result == "easily defended":
        if attack is None:
            emoji = "🛡😴"
        else:
            emoji = "🛡👌"
    else:
        emoji = emojis.get(result)
    return emoji


def get_map_battle_emoji(result, attack, defense) -> str:
    emojis = {
        "protected": "🛡",
        "closely protected": "🔱🛡⚡️",
        "Easy win": "⚔️😎",
        "win": "⚔️",
        "Massacre": "⚔️⚡️",
    }
    if result == "easily protected":
        if attack is None:
            emoji = "🛡😴"
        else:
            emoji = "🛡👌"
    else:
        emoji = emojis.get(result)
    return emoji


def sort_and_add_types_to_location_list(location_to_text: [AllianceLocation, str]) -> str:
    """
    Сортирует локации по типу и уровню; Объединяет в один текст, подписывает тип локаций перед группой
    :param location_to_text: [AllianceLocation: str]
    :return: str
    """
    location_to_text.sort(key=lambda x: (x[0].type, x[0].lvl))
    current_type = None
    res = ""
    for location, text in location_to_text:
        if location.type != current_type:
            res += "\n<b>{}</b>\n".format(location.type)
            current_type = location.type
        res += text
    return res


def parse_alliance_battle_results(results: str):
    if results.startswith("🤝Headquarters news:"):
        # Сводки с самих альянсов
        total_results = "🤝Headquarters news:\n"
        for result in results.partition("\n")[2].split("\n\n\n"):
            parse = re.search("(.+) was (.+)[.:]", result)
            if parse is None:
                logging.error("Error in parse headquarters news: {}".format(traceback.format_exc()))
                continue
            stock, glory = 0, 0
            name, battle_result = parse.group(1), parse.group(2)
            attack = re.search("🎖Attack: (.+)\n", result)
            defense = re.search("🎖Defense: (.+)\n", result)
            gained = re.search("for (\\d+)?📦 and (\\d+)?🎖", result)
            if gained is not None:
                stock, glory = int(gained.group(1)) if gained.group(1) is not None else 0, \
                               int(gained.group(2)) if gained.group(2) is not None else 0
            emoji = get_hq_battle_emoji(battle_result, attack, defense)
            total_results += "{}{}{}{}\n".format(emoji, name, " -{}📦".format(stock) if stock > 0 else "",
                                                        " -{}🎖".format(glory) if glory > 0 else "")
        AllianceResults.set_hq_text(total_results)
    elif results.startswith("🗺State of map:"):
        # Сводки с локаций
        AllianceLocation.increase_turns_owned()
        locations_to_results = []
        for result in results.partition("\n")[2].split("\n\n"):
            location_result = ""
            parse = re.search("(.+) lvl\\.(\\d+) ((was (.+))|(belongs to (.*?)(:|\\. (.+):)))\n", result)
            attack = re.search("🎖Attack: (.+)\n", result)
            defense = re.search("🎖Defense: (.+)\n", result)
            if parse is None:
                logging.error("Error in parse map news: {}".format(traceback.format_exc()))
                continue
            name, lvl = parse.group(1), int(parse.group(2))
            battle_result = parse.group(5) if parse.group(5) is not None else parse.group(9) if \
                parse.group(9) is not None else "win"
            new_owner = parse.group(7)

            location = AllianceLocation.get_or_create_location_by_name_and_lvl(name, lvl)
            emoji = get_map_battle_emoji(battle_result, attack, defense)
            location_result += "{}{}🏅{}\n".format(emoji, name, lvl)

            if new_owner is not None:
                alliance = Alliance.get_or_create_alliance_by_name(new_owner)
                location.owner_id = alliance.id
                location.turns_owned = 0
                location.update()
                location_result += "   ╰🎪 {}\n".format(alliance.name)

            locations_to_results.append([location, location_result])

        AllianceResults.set_location_text(sort_and_add_types_to_location_list(locations_to_results))


def ga_map(bot, update):
    mes = update.message
    locations = AllianceLocation.get_active_locations()
    res = "🗺 Карта альянсов:\n"
    location_to_text: {AllianceLocation: str} = []
    for location in locations:
        text = "{}{}{} Lvl.{}\n".format(location.emoji, '❇️' if location.is_active() else '', location.name, location.lvl)
        alli_name = Alliance.get_alliance(location.owner_id).name if location.owner_id is not None else "Пустует!"
        text += "      🎪{} {}\n".format(alli_name, location.turns_owned)
        location_to_text.append([location, text])

    res += sort_and_add_types_to_location_list(location_to_text)

    alliance = Alliance.get_player_alliance(Player.get_player(mes.from_user.id))
    if alliance is not None:
        res = alliance.add_flag_to_name(res)
    bot.send_message(chat_id=mes.chat_id, text=res, parse_mode='HTML')

