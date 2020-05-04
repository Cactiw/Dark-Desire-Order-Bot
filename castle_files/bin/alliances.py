
from castle_files.libs.player import Player
from castle_files.libs.guild import Guild
from castle_files.libs.alliance import Alliance, AllianceResults
from castle_files.libs.alliance_location import AllianceLocation

from castle_files.bin.service_functions import get_time_remaining_to_battle, get_message_forward_time, \
    get_message_and_player_id
from castle_files.bin.buttons import get_alliance_inline_buttons

from castle_files.work_materials.globals import dispatcher, cursor, job
from castle_files.work_materials.filters.general_filters import filter_is_pm


import logging
import traceback
import re
import time
import datetime

from telegram import InlineKeyboardMarkup
from functools import reduce, wraps

ALLOWED_LIST = ['Creepy Balboa', 'Enchanted Warrior', 'Coarse Mercury']


def alliance_access(func):
    @wraps(func)
    def wrapper(bot, update, *args, **kwargs):
        message, player_id = get_message_and_player_id(update)
        if Alliance.get_player_alliance(Player.get_player(player_id, notify_on_error=False)) is None:
            return
        return func(bot, update, *args, **kwargs)
    return wrapper


def high_access(func):
    @wraps(func)
    def wrapper(bot, update, *args, **kwargs):
        message, player_id = get_message_and_player_id(update)
        player = Player.get_player(player_id)
        guild = Guild.get_guild(player.guild)
        if guild is None or not guild.check_high_access(player.id):
            bot.send_message(chat_id=message.chat_id,
                             text="Данная функция доступна только командирам гильдий и их заместителям.")
            return
        return func(bot, update, *args, **kwargs)
    return wrapper


def update_alliance(bot, update):
    mes = update.message
    forward_message_date = get_message_forward_time(mes)
    if datetime.datetime.now() - forward_message_date > datetime.timedelta(seconds=30):
        bot.send_message(chat_id=mes.chat_id, text="Это устаревший альянс.", reply_to_message_id=mes.message_id)
        return
    name = re.search("🤝(.+?) ?\n", mes.text).group(1)
    if name not in ALLOWED_LIST:
        return
    alliance = Alliance.get_or_create_alliance_by_name(name)
    owner = re.search("Owner:.*\\[(.+)\\](.*)", mes.text)
    owner_tag = owner.group(1)
    guild = Guild.get_guild(guild_tag=owner_tag)
    player = Player.get_player(mes.from_user.id)
    if guild is not None and guild.id == player.guild:
        guild.alliance_id = alliance.id
        guild.update_to_database()
        alliance.creator_id = guild.commander_id
        alliance.update()
        bot.send_message(chat_id=mes.chat_id,
                         text="Информация об альянсе и гильдии обновлена. Теперь пришли мне 📋 Roster!")


@alliance_access
def view_alliance(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    player_guild = Guild.get_guild(player.guild)
    alliance = Alliance.get_player_alliance(player)
    guilds = alliance.get_alliance_guilds()
    res = "🤝<b>{}</b>\n".format(alliance.name)
    res += "Владелец: {}\n".format(Player.get_player(alliance.creator_id).nickname)
    res += "Гильдии альянса: {}".format(" ".join(map(lambda guild: "{}[{}]".format(guild.castle, guild.tag), guilds)))
    buttons = None
    if player_guild.check_high_access(player.id):
        buttons = InlineKeyboardMarkup(get_alliance_inline_buttons(alliance))
    bot.send_message(chat_id=mes.chat_id, text=res, parse_mode='HTML', reply_markup=buttons)


@alliance_access
@high_access
def alliance_stats(bot, update):
    mes = update.callback_query.message
    data = update.callback_query.data
    alliance_id = int(re.search("_(\\d+)", data).group(1))
    player = Player.get_player(update.callback_query.from_user.id)
    player_guild = Guild.get_guild(player.guild)
    if not player_guild.check_high_access(player.id):
        bot.answerCallbackQuery(update.callback_query.id,
                                text="Данная функция доступна только командирам гильдий и их заместителям.",
                                show_alert=True)
        return
    alliance = Alliance.get_player_alliance(player)
    if alliance is None or alliance.id != alliance_id:
        bot.answerCallbackQuery(update.callback_query.id, text="Альянс не соответствует Вашему. Начните сначала.",
                                show_alert=True)
        return
    guilds = alliance.get_alliance_guilds()
    response = "📊Статистика <b>{}</b>:\n".format(alliance.name)
    total_stats = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    for guild in guilds:
        stats = reduce(
            add_player_stats,
            map(lambda player_id: Player.get_player(player_id), guild.members),
            [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        )
        response += "<b>{}</b>\n{}\n".format(guild.tag, format_leagues_stats(stats))
        total_stats = add_stats_to_total(total_stats, stats)
    response += "\n<b>Всего:</b>\n{}\n".format(format_leagues_stats(total_stats))
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
    bot.answerCallbackQuery(update.callback_query.id)


def add_player_stats(value: [[int, int, int], [int, int, int], [int, int, int]], player: Player):
    if player.lvl < 20:
        return value
    lst = value[(player.lvl >= 40) + (player.lvl >= 60)]
    lst[0] += player.attack
    lst[1] += player.defense
    lst[2] += 1
    return value


def add_stats_to_total(total, new_stats):
    for i in range(len(total)):
        total[i][0] += new_stats[i][0]
        total[i][1] += new_stats[i][1]
        total[i][2] += new_stats[i][2]
    return total


def format_leagues_stats(stats: [[int, int, int], [int, int, int], [int, int, int]]) -> str:
    return "<code>20-39 {:>5}⚔️{:>5}🛡 {:>2}👥\n40-59 {:>5}⚔️{:>5}🛡 {:>2}👥\n60+  {:>6}⚔️{:>6}🛡 {:>2}👥</code>" \
           "\n".format(*reduce(lambda res, l: res + l, stats, []))


@alliance_access
def alliance_roster(bot, update):
    alliance = Alliance.get_player_alliance(Player.get_player(update.message.from_user.id))
    if alliance is None:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Вы не состоите в альянсе. Пусть создатель альянса отправил ответ чв на 🤝Альянс, "
                              "а затем - 📋 Roster")
        return
    forward_message_date = get_message_forward_time(update.message)
    if datetime.datetime.now() - forward_message_date > datetime.timedelta(seconds=30):
        bot.send_message(chat_id=update.message.chat_id, text="Это устаревший состав.",
                         reply_to_message_id=update.message.message_id)
        return
    tags = re.findall("\\[(\\w+)\\]", update.message.text)
    for guild_tag in tags:
        guild = Guild.get_guild(guild_tag=guild_tag)
        if guild is None:
            continue
        guild.alliance_id = alliance.id
        guild.update_to_database()
    bot.send_message(chat_id=update.message.chat_id,
                     text="Состав альянса обновлён.\n"
                          "Установите чат МИДа альянса командой /set_alliance_hq_chat {chat_id}\n"
                          "<em>chat_id можно получить при помощи команды /chat_info в нужном чате.</em>",
                     parse_mode='HTML')


@alliance_access
def set_alliance_hq_chat(bot, update, args):
    try:
        chat_id = int(args[0])
    except Exception:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Неверный синтаксис.\nПример: /set_alliance_hq_chat -1234567890")
        return
    alliance = Alliance.get_player_alliance(Player.get_player(update.message.from_user.id))
    if alliance is None:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Альянс не найден. Обратитесь к создателю альянса, или командиру (его заместителю).")
        return
    alliance.hq_chat_id = chat_id
    alliance.update()
    bot.send_message(chat_id=update.message.chat_id, text="Альянс обновлён.")


def get_player_and_guild_and_alliance(player_id: int):
    player = Player.get_player(player_id, notify_on_error=False)
    guild = Guild.get_guild(player.guild) if player is not None else None
    alliance = Alliance.get_alliance(guild.alliance_id) if guild is not None else None
    return player, guild, alliance


def add_alliance_location(bot, update):
    mes = update.message
    player, guild, alliance = get_player_and_guild_and_alliance(mes.from_user.id)
    try:
        parse = re.search("simple combination: (\\w+)", mes.text)
        link = parse.group(1)

        parse = re.search("You found hidden (location (.+) lvl.(\\d+)|headquarter (.+))", mes.text)
        if parse.group(4) is not None:
            return add_alliance_link(parse.group(4), link)
        name, lvl = parse.group(2), int(parse.group(3))

    except Exception:
        logging.error(traceback.format_exc())
        if filter_is_pm(mes):
            bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка")
        return
    request = "select id from alliance_locations where link = %s"
    cursor.execute(request, (link,))
    row = cursor.fetchone()
    if row is not None:
        return
    request = "select id from alliance_locations where name = %s and lvl = %s and link is null " \
              "and expired is false limit 1"
    cursor.execute(request, (name, lvl))
    row = cursor.fetchone()
    if row is not None:
        location = AllianceLocation.get_location(row[0])
        location.link = link
        location.update()
    else:
        location = AllianceLocation(None, link, name, None, lvl, None, 0, False, False)
        location.figure_type()
        location.insert_to_database()
    if alliance is not None and alliance.hq_chat_id is not None:
        bot.send_message(chat_id=alliance.hq_chat_id, parse_mode='HTML',
                         text="Новая локация: <b>{} Lvl.{}</b>\n{}".format(name, lvl, link))


def add_alliance_link(name, link):
    alliance = Alliance.get_or_create_alliance_by_name(name)
    if alliance.link is None:
        alliance.link = link
        alliance.update()


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
        AllianceLocation.set_possible_expired()
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
            location.can_expired = False
            emoji = get_map_battle_emoji(battle_result, attack, defense)
            location_result += "{}{}🏅{}\n".format(emoji, name, lvl)

            if new_owner is not None:
                alliance = Alliance.get_or_create_alliance_by_name(new_owner)
                location.owner_id = alliance.id
                location.turns_owned = 0
                location_result += "   ╰🎪 {}\n".format(alliance.name)
            location.update()

            locations_to_results.append([location, location_result])

        AllianceResults.set_location_text(sort_and_add_types_to_location_list(locations_to_results))


@alliance_access
def ga_map(bot, update):
    mes = update.message
    locations = AllianceLocation.get_active_locations()
    res = "🗺 Карта альянсов:\n"
    player = Player.get_player(mes.from_user.id)
    guild = Guild.get_guild(player.guild)
    alliance = Alliance.get_alliance(guild.alliance_id) if guild is not None else None
    location_to_text: {AllianceLocation: str} = []
    for location in locations:
        text = "{}{}{}{}" \
               "\n".format(
                location.emoji, '❇️' if location.is_active() else '',
                "<a href=\"t.me/share/url?url={}\">{} Lvl.{}</a>".format(
                    "/ga_atk_{}".format(location.link) if alliance is None or location.owner_id != alliance.id else
                    "/ga_def_{}".format(location.link), location.name,
                    location.lvl) if location.link is not None else "{} Lvl.{}".format(location.name, location.lvl),
                "<a href=\"t.me/share/url?url=/ga_expire {}\">⚠</a>️".format(location.link) if
                location.can_expired else "")
        alli_name = Alliance.get_alliance(location.owner_id).name if location.owner_id is not None else "Пустует!"
        text += "      🎪{} {}\n".format(alli_name, location.turns_owned)
        location_to_text.append([location, text])

    res += sort_and_add_types_to_location_list(location_to_text)

    alliance = Alliance.get_player_alliance(Player.get_player(mes.from_user.id))
    if alliance is not None:
        res = alliance.add_flag_to_name(res)
    bot.send_message(chat_id=mes.chat_id, text=res, parse_mode='HTML')


@alliance_access
@high_access
def ga_expire(bot, update):
    try:
        link = re.match("/ga_expire (.+)", update.message.text).group(1)
    except Exception:
        bot.send_message(chat_id=update.message.chat_id, text="Неверный синтаксис",
                         reply_to_message_id=update.message.message_id)
        return
    location = AllianceLocation.get_location_by_link(link)
    if location is None:
        bot.send_message(chat_id=update.message.chat_id, text="Локация не найдена, или уже истекла.",
                         reply_to_message_id=update.message.message_id)
        return
    location.expired = True
    location.update()
    bot.send_message(chat_id=update.message.chat_id, text="{} помечена как истёкшая".format(location.format_name()))


@alliance_access
def alliance_pin(bot, update):
    player = Player.get_player(update.message.from_user.id)
    alliance = Alliance.get_player_alliance(player)
    new_text: str = update.message.text
    changed = False
    parse = re.findall("/ga_(atk|def)_(\\w+)", update.message.text)
    for cmd, link in parse:
        location = AllianceLocation.get_location_by_link(link)
        if location is None:
            cur_alliance = Alliance.get_alliance_by_link(link)
            if cur_alliance is None:
                continue
            new_text = re.sub("/ga_{}_{}".format(cmd, link),
                              "<a href=\"t.me/share/url?url=/ga_{}_{}\">{}{}</a>".format(
                                  cmd, link, "⚔️" if cmd == "atk" else "🛡", cur_alliance.name), new_text)
            changed = True
        else:
            new_text = re.sub("/ga_{}_{}".format(cmd, link),
                              "<a href=\"t.me/share/url?url=/ga_{}_{}\">{}{}</a>".format(
                                  cmd, link, "⚔️" if cmd == "atk" else "🛡", location.format_name()), new_text)
            changed = True
            # if cur_alliance == alliance:
    if changed:
        bot.send_message(chat_id=update.message.chat_id, text=new_text, parse_mode='HTML',
                         reply_to_message_id=update.message.message_id)



