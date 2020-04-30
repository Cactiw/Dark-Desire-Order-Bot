
from castle_files.libs.player import Player
from castle_files.libs.guild import Guild
from castle_files.libs.alliance import Alliance
from castle_files.libs.alliance_location import AllianceLocation

from castle_files.work_materials.globals import dispatcher, cursor

import logging
import traceback
import re


def get_player_and_guild_and_alliance(player_id: int):
    player = Player.get_player(player_id, notify_on_error=False)
    guild = Guild.get_guild(player.guild) if player is not None else None
    alliance = Alliance.get_alliance(guild.alliance_id) if guild is not None else None
    return player, guild, alliance


def add_location(bot, update):
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


def get_hq_battle_emoji(result, attack, defense) -> str:
    emojis = {
        "defended successfully": "🛡",
        "closely defended": "🛡⚡️",
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
        "closely protected": "🛡⚡️",
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


alliance_results = ""


def parse_alliance_battle_results(results: str):
    global alliance_results
    total_results = "🤝Headquarters news:\n"
    if results.startswith("🤝Headquarters news:"):
        # Сводки с самих альянсов
        alliance_results = ""
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
            total_results += "{}<b>{}</b>{}{}\n".format(emoji, name, " -{}📦".format(stock) if stock > 0 else "",
                                                        " -{}🎖".format(glory) if glory > 0 else "")
        alliance_results = total_results + "\n\n"
    elif results.startswith("🗺State of map:"):
        # Сводки с локаций
        for result in results.partition("\n")[2].split("\n\n"):
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
            alliance_results += "{}<b>{}</b>🏅{}\n".format(emoji, name, lvl)

            if new_owner is not None:
                alliance = Alliance.get_or_create_alliance_by_name(new_owner)
                location.owner_id = alliance.id
                location.turns_owned = 0
                location.update()
                alliance_results += "    🔸️{}\n".format(alliance.name)

        for alliance in Alliance.get_all_alliances():
            if alliance.hq_chat_id is not None:
                dispatcher.bot.send_message(
                    chat_id=alliance.hq_chat_id, parse_mode='HTML',
                    text=alliance_results.replace(alliance.name, "{}{}".format(alliance.name, "🔻")))


