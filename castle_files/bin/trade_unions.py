from castle_files.work_materials.globals import cursor, castles, CASTLE_BOT_ID, SUPER_ADMIN_ID
from castle_files.libs.bot_async_messaging import MAX_MESSAGE_LENGTH

from castle_files.libs.player import Player
from castle_files.libs.guild import Guild
from castle_files.libs.trade_union import TradeUnion

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
    creator_nick = re.search("🏅Owner:['🍆🍁☘🌹🐢🦇🖤](.*)", mes.text)
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


def union_list(bot, update):
    mes = update.message
    if mes.from_user.id == SUPER_ADMIN_ID:
        union = TradeUnion.get_union(union_id=1)
    else:
        union = TradeUnion.get_union(creator_id=update.message.from_user.id)
    if union is None:
        bot.send_message(chat_id=update.message.chat_id, text="Только создатель профсоюза может вносить его состав.")
        return
    for string in update.message.text.splitlines():
        if string[0] in castles:
            request = "select id from players where nickname = %s"
            cursor.execute(request, (string[1:].partition("/")[0],))
            row = cursor.fetchone()
            if row is None:
                continue
            if row[0] not in union.players:
                union.players.append(row[0])
    union.update_to_database()
    bot.send_message(chat_id=mes.chat_id, text="Список <b>{}</b> успешно обновлён!".format(union.name),
                     parse_mode='HTML')


def add_to_union_user_id(bot, update):
    mes = update.message
    if mes.from_user.id == SUPER_ADMIN_ID:
        union = TradeUnion.get_union(union_id=1)
    else:
        union = TradeUnion.get_union(creator_id=update.message.from_user.id)
    if union is None:
        bot.send_message(chat_id=update.message.chat_id, text="Только создатель профсоюза может вносить его состав.")
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
        bot.send_message(chat_id=update.message.chat_id, text="Только создатель профсоюза может удалять состав.")
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
        bot.send_message(chat_id=update.message.chat_id, text="Только создатель профсоюза может просматривать состав.")
        return
    response = "Участники <b>{}</b>:\n"
    for player_id in union.players:
        player = Player.get_player(player_id, notify_on_error=False)
        if player is None:
            continue
        response_new = "{}<b>{}</b> — @{}\n".format(player.castle, player.nickname, player.username)
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
        bot.send_message(chat_id=update.message.chat_id, text="Только создатель профсоюза может изменять чат профсоюза")
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
