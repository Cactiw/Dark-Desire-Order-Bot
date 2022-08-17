from castle_files.work_materials.globals import cursor, castles, CASTLE_BOT_ID, SUPER_ADMIN_ID
from castle_files.libs.bot_async_messaging import MAX_MESSAGE_LENGTH

from castle_files.libs.player import Player
from castle_files.libs.guild import Guild
from castle_files.libs.trade_union import TradeUnion

from castle_files.libs.bot_async_messaging import MAX_MESSAGE_LENGTH
from castle_files.work_materials.filters.general_filters import filter_is_pm

from telegram.error import TelegramError
import re
import logging
import traceback
import threading

kick_players_from_union = True

union_chats = {}


def add_union(bot, update):
    mes = update.message
    name = re.search("Trade Union: (.*)", mes.text)
    creator_nick = re.search("🏅Owner:['{}](.*)".format(''.join(castles)), mes.text)
    if name is None:
        bot.send_message(chat_id=mes.chat_id, text="Ошибка распознавания имени")
        return
    if creator_nick is None:
        bot.send_message(chat_id=mes.chat_id, text="Ошибка распознавания ника создателя")
        return
    name = name.group(1)
    creator_nick = creator_nick.group(1)
    request = "select id from players where nickname = %s"
    cursor.execute(request, (creator_nick,))
    row = cursor.fetchone()
    if row is None:
        bot.send_message(chat_id=mes.chat_id, text="Создатель профсоюза не зарегистрирован в боте. "
                                                   "Регистрация необходима для работы.")
        # return
    creator = Player.get_player(row[0], notify_on_error=False)
    view_link = re.search("View: /tu_view_(.*)", mes.text)
    view_link = view_link.group(1) if view_link is not None else None
    request = "select id from trade_unions where name = %s"
    cursor.execute(request, (name,))
    row = cursor.fetchone()
    if row is not None:
        bot.send_message(chat_id=mes.chat_id, text="Этот профсоюз уже зарегистрирован!")
        return
    request = "insert into trade_unions(creator_id, name, players, view_link) values (%s, %s, %s, %s)"
    cursor.execute(request, (creator.id, name, [creator.id], view_link))
    bot.send_message(chat_id=mes.chat_id, text="Профсоюз <b>{}</b> успешно зарегистрирован!".format(name),
                     parse_mode='HTML')
    
    
def add_union_assistant(bot, update):
    mes = update.message
    union = TradeUnion.get_union(creator_id=update.message.from_user.id)
    if union is None:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Только создатель и замы профсоюза могут добавлять замов.")
        return
    new_id = re.search(" (\\d+)", mes.text)
    if new_id is None:
        bot.send_message(chat_id=update.message.chat_id, text="Неверный синтаксис.")
        return
    new_id = int(new_id.group(1))
    if new_id not in union.players:
        bot.send_message(chat_id=update.message.chat_id, text="Замом можно сделать только члена профсоюза.")
        return
    if new_id in union.assistants:
        bot.send_message(chat_id=update.message.chat_id, text="Этот игрок уже является заместителем.")
        return
    union.assistants.append(new_id)
    union.update_to_database()
    bot.send_message(chat_id=mes.chat_id, text="Заместитель успешно добавлен!")


def del_union_assistant(bot, update):
    mes = update.message
    union = TradeUnion.get_union(creator_id=update.message.from_user.id)
    if union is None:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Только создатель и замы профсоюза могут удалять замов.")
        return
    new_id = re.search(" (\\d+)", mes.text)
    if new_id is None:
        bot.send_message(chat_id=update.message.chat_id, text="Неверный синтаксис.")
        return
    new_id = int(new_id.group(1))
    if new_id not in union.assistants:
        bot.send_message(chat_id=update.message.chat_id, text="Этот игрок не является заместителем.")
        return
    union.assistants.remove(new_id)
    union.update_to_database()
    bot.send_message(chat_id=mes.chat_id, text="Заместитель успешно удалён!")


def union_list(bot, update):
    mes = update.message
    union = TradeUnion.get_union(creator_id=update.message.from_user.id)
    if union is None:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Только создатель и замы профсоюза могут вносить его состав.")
        return
    for string in update.message.text.splitlines():
        if string[0] in castles:
            request = "select id from players where nickname = %s"
            cursor.execute(request, (string[1:].partition(" /")[0],))
            row = cursor.fetchone()
            if row is None:
                continue
            if row[0] not in union.players:
                union.players.append(row[0])
    union.update_to_database()
    bot.send_message(chat_id=mes.chat_id, text="Список <b>{}</b> успешно обновлён!".format(union.name),
                     parse_mode='HTML')


def count_union_stats(bot, update):
    mes = update.message
    if not filter_is_pm(mes):
        bot.send_message(chat_id=mes.chat_id, text="Команда разрешена только в лс, чтобы не пинговать людей.",
                         reply_to_message_id=mes.message_id)
        return
    union = TradeUnion.get_union(creator_id=mes.from_user.id)
    if union is None:
        bot.send_message(chat_id=mes.chat_id, text="Только создатель и замы профсоюза могут вносить его состав.")
        return
    attack = 0
    defense = 0
    count = 0
    for player_id in union.players:
        player = Player.get_player(player_id, notify_on_error=False)
        if player is None:
            continue
        attack += player.attack
        defense += player.defense
        count += 1
    response = "Суммарные статы по <b>{}</b>:\n⚔️: <code>{}</code>, 🛡: <code>{}</code>\n" \
               "Всего людей: <code>{}</code>".format(union.name, attack, defense, count)
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


def split_union(bot, update):
    mes = update.message
    args = mes.text.split()[1:]
    if not filter_is_pm(mes):
        bot.send_message(chat_id=mes.chat_id, text="Команда разрешена только в лс, чтобы не пинговать людей.",
                         reply_to_message_id=mes.message_id)
        return
    union = TradeUnion.get_union(creator_id=mes.from_user.id)
    if union is None:
        bot.send_message(chat_id=mes.chat_id, text="Только создатель и замы профсоюза могут вносить его состав.")
        return
    players = []
    total_stats = 0
    attr = "attack" if "attack" in mes.text else "defense"
    alt = "alt" in mes.text
    for player_id in union.players:
        player = Player.get_player(player_id, notify_on_error=False)
        if player is None:
            continue
        players.append(player)
        total_stats += player.__getattribute__(attr)
    try:
        ratios = args[0].split(":")
        need_stats = []  # Сколько статов в каждую часть ( уже в готовых числах )
        sum_parts = 0
        player_groups = []
        for part in ratios:
            sum_parts += int(part)
            player_groups.append([])
        for part in ratios:
            need_stats.append(int(part) * total_stats / sum_parts)
    except (ValueError, IndexError):
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return
    players.sort(key=lambda pl: pl.__getattribute__(attr), reverse=True)
    for player in players:
        # Поиск минимального остатка необходимых статов в данной группе, > 0 после добавления этого игрока туда
        min_stats_remain = 10000000000 if not alt else -1
        min_stats_remain_num = -1
        max_under_zero_stats_remain = -10000000000
        max_under_zero_stats_remain_num = -1
        for i, stats in enumerate(need_stats):
            current_remain = stats - player.__getattribute__(attr)
            if (not alt and 0 < current_remain < min_stats_remain) or (alt and 0 < current_remain > min_stats_remain):
                min_stats_remain_num = i
                min_stats_remain = current_remain
            elif max_under_zero_stats_remain < current_remain < 0:
                max_under_zero_stats_remain_num = i
                max_under_zero_stats_remain = current_remain
        if min_stats_remain_num >= 0:  # Нашлось свободное место под этого игрока
            player_groups[min_stats_remain_num].append(player)
            need_stats[min_stats_remain_num] -= player.__getattribute__(attr)
        else:
            # Закидываем в группу, добавление в которую вызовет минимальное отклонение от цели
            player_groups[max_under_zero_stats_remain_num].append(player)
            need_stats[max_under_zero_stats_remain_num] -= player.__getattribute__(attr)
    response = "Рассчёт распределения статов подготовлен:\n"
    full = "full" in mes.text
    for i, group in enumerate(player_groups):
        response += "Группа {}:\n".format(i)
        sum_stats = 0
        for player in group:
            if full:
                response_new = "<b>{}</b> — @{} {}<code>{}</code>" \
                               "\n".format(player.nickname, player.username, "⚔️" if attr == "attack" else "🛡",
                                           player.__getattribute__(attr))
            else:
                response_new = "@{}\n".format(player.username)
            if len(response + response_new) > MAX_MESSAGE_LENGTH - 100:
                bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
                response = ""
            response += response_new
            sum_stats += player.__getattribute__(attr)
        if full:
            response += "Всего в группе {}: <code>{}</code>\n\n".format("⚔️" if attr == "attack" else "🛡", sum_stats)
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


def top_union_stats(bot, update):
    mes = update.message
    MAX_PLAYERS_PRINT = 20
    if not filter_is_pm(mes):
        bot.send_message(chat_id=mes.chat_id, text="Команда разрешена только в лс, чтобы не пинговать людей.",
                         reply_to_message_id=mes.message_id)
        return
    union = TradeUnion.get_union(creator_id=mes.from_user.id)
    if union is None:
        bot.send_message(chat_id=mes.chat_id, text="Только создатель и замы профсоюза могут вносить его состав.")
        return
    players = []
    for player_id in union.players:
        player = Player.get_player(player_id, notify_on_error=False)
        if player is None:
            continue
        players.append(player)
    if "attack" in mes.text:
        players.sort(key=lambda x: x.attack, reverse=True)
    else:
        players.sort(key=lambda x: x.defense, reverse=True)
    count = 1
    response = "Топы статов по <b>{}</b>:\n".format(union.name)
    for player in players:
        response += "{}: <b>{}</b> {}<code>{}</code> @{}" \
                    "\n".format(count, player.nickname, "⚔:" if "attack" in mes.text else "🛡:",
                                player.attack if "attack" in mes.text else player.defense, player.username)
        if count >= MAX_PLAYERS_PRINT:
            break
        count += 1

    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


def add_to_union_user_id(bot, update):
    mes = update.message
    union = TradeUnion.get_union(creator_id=update.message.from_user.id)
    if union is None:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Только создатель и замы профсоюза могут вносить его состав.")
        return
    player_id = re.search(" (\\d+)", mes.text)
    if player_id is None:
        bot.send_message(chat_id=update.message.chat_id, text="Неверный синтаксис.")
        return
    player_id = int(player_id.group(1))
    if player_id not in union.players:
        union.players.append(player_id)
        union.update_to_database()
        bot.send_message(chat_id=update.message.chat_id,
                         text="Игрок успешно добавлен в профсоюз <b>{}</b>.".format(union.name), parse_mode='HTML')
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Игрок уже в профсоюзе <b>{}</b>.".format(union.name), parse_mode='HTML')


def clear_union_list(bot, update):
    global kick_players_from_union
    mes = update.message
    union = TradeUnion.get_union(creator_id=update.message.from_user.id)
    if union is None:
        bot.send_message(chat_id=update.message.chat_id, text="Только создатель и замы профсоюза могут удалять состав.")
        return
    union.players = [union.creator_id]
    union.update_to_database()
    bot.send_message(chat_id=mes.chat_id, text="Список <b>{}</b> успешно очищен. "
                                               "Пришлите форварды состава профсоюза заного.".format(union.name),
                     parse_mode='HTML')
    kick_players_from_union = False
    threading.Timer(function=set_kick_flag, interval=60).start()


def set_kick_flag():
    global kick_players_from_union
    kick_players_from_union = True


def print_union_players(bot, update):
    mes = update.message
    union = TradeUnion.get_union(creator_id=update.message.from_user.id)
    if union is None:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Только создатель и замы профсоюза могут просматривать состав.")
        return
    response = "Участники <b>{}</b>:\n".format(union.name)
    for player_id in union.players:
        player = Player.get_player(player_id, notify_on_error=False)
        if player is None:
            continue
        response_new = "{}<b>{}</b> — @{} <code>{}</code>\n".format(player.castle, player.nickname, player.username,
                                                                    player.id)
        if len(response + response_new) > MAX_MESSAGE_LENGTH:
            bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
            response = ""
        response += response_new
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


def add_union_chat_id(bot, update):
    mes = update.message
    if mes.from_user.id == SUPER_ADMIN_ID:
        union = TradeUnion.get_union(union_id=1)
    else:
        union = TradeUnion.get_union(creator_id=update.message.from_user.id)
    if union is None:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Только создатель и замы профсоюза могут изменять чат профсоюза")
        return
    union.chat_id = mes.chat_id
    union.update_to_database()
    bot.send_message(chat_id=mes.chat_id, text="Этот чат теперь официальный чат профсоюза <b>{}</b>".format(union.name),
                     parse_mode='HTML')
    fill_union_chats()


def fill_union_chats():
    request = "select name, chat_id from trade_unions where chat_id is not null"
    cursor.execute(request)
    row = cursor.fetchone()
    union_chats.clear()
    while row is not None:
        union_chats.update({row[0]: row[1]})
        row = cursor.fetchone()


def check_and_kick(bot, update):
    if kick_players_from_union is False:
        return
    mes = update.message
    union = TradeUnion.get_union(chat_id=update.message.chat_id)
    if union is None:
        return
    if mes.from_user.id not in union.players and mes.from_user.id != CASTLE_BOT_ID:
        try:
            bot.kickChatMember(chat_id=mes.chat_id, user_id=update.message.from_user.id)
            bot.send_message(chat_id=mes.chat_id,
                             text="Только членам <b>{}</b> разрешено находиться в этом чате."
                                  "Возможно, стоит обновить состав".format(union.name),
                             parse_mode='HTML')
        except TelegramError:
            return
            # logging.error(traceback.format_exc())


def view_guild_players_in_union(bot, update):
    mes = update.message
    if not filter_is_pm(mes):
        bot.send_message(chat_id=mes.chat_id, text="Команда разрешена только в лс, чтобы не пинговать людей.",
                         reply_to_message_id=mes.message_id)
        return
    curr_player = Player.get_player(mes.from_user.id)
    if curr_player is None:
        return
    guild_id = curr_player.guild
    if guild_id is None:
        bot.send_message(chat_id=mes.chat_id,
                         text="Вы не состоите в гильдии. Вступите в гильдию в игре и попросите "
                              "командира добавить вас в гильдейском чате.")
        return
    guild = Guild.get_guild(guild_id=guild_id)
    if guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена.")
        return
    if not guild.check_high_access(curr_player.id):
        bot.send_message(chat_id=mes.chat_id, text="Только замы и гм могут использовать эту команду.")
        return
    union_name = re.search(" (.*)", mes.text)
    if union_name is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис. Укажите название профсоюза после команды.")
        return
    union_name = union_name.group(1)
    union = TradeUnion.get_union(union_name=union_name)
    if union is None:
        bot.send_message(chat_id=mes.chat_id, text="Профсоюз не найден. Проверьте правильность ввода его имени.")
        return
    not_in_union = []
    response = "Список игроков в гильдии <b>{}</b> в профсоюзе <b>{}</b>\n".format(guild.tag, union.name)
    for player_id in guild.members:
        player = Player.get_player(player_id, notify_on_error=False)
        if player is None:
            continue
        if player_id in union.players:
            response += "<b>{}</b> — @{}\n".format(player.nickname, player.username)
        else:
            not_in_union.append(player)
    response += "\nВ других профсоюзах или без него:\n"
    for player in not_in_union:
        response += "<b>{}</b> — @{}\n".format(player.nickname, player.username)
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


def view_guild_unions(bot, update):
    mes = update.message
    if not filter_is_pm(mes):
        bot.send_message(chat_id=mes.chat_id, text="Команда разрешена только в лс, чтобы не пинговать людей.",
                         reply_to_message_id=mes.message_id)
        return
    curr_player = Player.get_player(mes.from_user.id)
    if curr_player is None:
        return
    guild_id = curr_player.guild
    if guild_id is None:
        bot.send_message(chat_id=mes.chat_id,
                         text="Вы не состоите в гильдии. Вступите в гильдию в игре и попросите "
                              "командира добавить вас в гильдейском чате.")
        return
    guild = Guild.get_guild(guild_id=guild_id)
    if guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена.")
        return
    if not guild.check_high_access(curr_player.id):
        bot.send_message(chat_id=mes.chat_id, text="Только замы и гм могут использовать эту команду.")
        return
    union_id = 1
    union = TradeUnion.get_union(union_id=union_id)
    players_in_unions = {}
    while union is not None:
        union_players_list = []
        players_in_unions.update({union.name: union_players_list})
        for player_id in guild.members:
            player = Player.get_player(player_id, notify_on_error=False)
            if player is None:
                continue
            if player_id in union.players:
                union_players_list.append(player)
        union_id += 1
        union = TradeUnion.get_union(union_id=union_id)
    response = "Список игроков в гильдии <b>{}</b> в профсоюзах\n".format(guild.tag)
    for player_id in guild.members:
        player = Player.get_player(player_id, notify_on_error=False)
        if player is None:
            continue
        found = False
        for un, lst in list(players_in_unions.items()):
            if player in lst:
                response += "<b>{}</b> — @{} — <b>{}</b>\n".format(player.nickname, player.username, un)
                found = True
                break
        if not found:
            response += "<b>{}</b> — @{} — НЕТ ПРОФСОЮЗА\n".format(player.nickname, player.username)
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
