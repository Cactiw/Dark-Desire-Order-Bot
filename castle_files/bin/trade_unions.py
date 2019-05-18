from castle_files.work_materials.globals import cursor, castles, CASTLE_BOT_ID

from castle_files.libs.player import Player
from castle_files.libs.trade_union import TradeUnion

from telegram.error import TelegramError
import re

union_chats = {}


def add_union(bot, update):
    mes = update.message
    name = re.search(" (.*)", mes.text)
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
    union = TradeUnion.get_union(creator_id=update.message.from_user.id)
    if union is None:
        bot.send_message(chat_id=update.message.chat_id, text="Только создатель профсоюза может вносить его состав.")
        return
    for string in update.message.text.splitlines():
        if string[0] in castles:
            request = "select id from players where nickname = %s"
            cursor.execute(request, (string[1:],))
            row = cursor.fetchone()
            if row is None:
                continue
            if row[0] not in union.players:
                union.players.append(row[0])
    union.update_to_database()
    bot.send_message(chat_id=mes.chat_id, text="Список <b>{}</b> успешно обновлён!".format(union.name),
                     parse_mode='HTML')


def add_union_chat_id(bot, update):
    mes = update.message
    union = TradeUnion.get_union(creator_id=update.message.from_user.id)
    if union is None:
        bot.send_message(chat_id=update.message.chat_id, text="Только создатель профсоюза может изменять чат профсоюза")
        return
    union.chat_id = mes.chat_id
    union.update_to_database()
    bot.send_message(chat_id=mes.chat_id, text="Этот чат теперь официальный чат профсоюза <b>{}</b>".format(union.name),
                     parse_mode='HTML')


def fill_union_chats():
    request = "select name, chat_id from trade_unions where chat_id is not null"
    cursor.execute(request)
    row = cursor.fetchone()
    union_chats.clear()
    while row is not None:
        union_chats.update({row[0]: row[1]})
        row = cursor.fetchone()


def check_and_kick(bot, update):
    mes = update.message
    union = TradeUnion.get_union(chat_id=update.message.chat_id)
    if union is None:
        return
    if mes.from_user.id not in union.players and mes.from_user.user_id != CASTLE_BOT_ID:
        try:
            bot.kickChatMember(chat_id=mes.chat_id, user_id=update.message.from_user.id)
            bot.send_message(chat_id=mes.chat_id,
                             text="Только членам <b>{}</b> разрешено находиться в этом чате."
                                  "Возможно, стоит обновить состав".format(union.name),
                             parse_mode='HTML')
        except TelegramError:
            return
