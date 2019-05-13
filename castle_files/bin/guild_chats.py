from castle_files.work_materials.globals import cursor
from castle_files.bin.service_functions import get_time_remaining_to_battle, check_access, get_admin_ids

from castle_files.libs.guild import Guild
from castle_files.libs.player import Player

import datetime

ping_by_chat_id = {}


def notify_guild_attack(bot, update):
    mes = update.message
    remaining_time = get_time_remaining_to_battle()
    if mes.forward_date - datetime.datetime.now() > datetime.timedelta(minutes=2):
        return 0
    if remaining_time > datetime.timedelta(minutes=30):
        pass
        return 0
    ready_to_battle = mes.text.count("[⚔]") + mes.text.count("[🛡]")
    sleeping = mes.text.count("[🛌]")
    response = "<b>{0}</b>\nГотово к битве: <b>{1}</b>\nНе готово к битве, но занято <b>{2}</b>\n" \
               "Спит: <b>{3}</b>\n\nВремя до битвы: {4}\n".format(mes.text.splitlines()[0], ready_to_battle,
                                                                mes.text.count("\n") - ready_to_battle - sleeping,
                                                                sleeping, ":".join(str(remaining_time).partition(".")[0].split(":")[0:3]))
    request = "select guild_id from guilds where chat_id = %s"
    cursor.execute(request, (mes.chat_id,))
    row = cursor.fetchone()
    if row is None:
        return
    guild = Guild.get_guild(guild_id=row[0])
    if guild is None:
        return
    if mes.chat_id != guild.chat_id:
        return
    if mes.from_user.id not in get_admin_ids(bot, chat_id=mes.chat_id) and not check_access(mes.from_user.id):
        bot.send_message(chat_id=mes.chat_id, text="Доступ только у админов", parse_mode='HTML',
                         reply_to_message_id=mes.message_id)
        return
    do_not_ready = []
    sleeping = []
    for string in mes.text.splitlines()[1:]:
        if not ("[⚔]" in string or "[🛡]" in string):
            nickname = string.partition("]")[2][1:]
            do_not_ready.append(nickname)
            if "[🛌]" in string:
                sleeping.append(nickname)

    in_dict_do_not_ready = []
    in_dict_sleeping = []
    ping_dict = {"do not ready" : in_dict_do_not_ready, "sleeping" : in_dict_sleeping}
    for player_id in guild.members:
        player = Player.get_player(player_id, notify_on_error=False)
        if player is None:
            continue
        db_nickname = player.nickname.partition("]")[2]
        if db_nickname in do_not_ready:
            in_dict_do_not_ready.append(player.username)
            if db_nickname in sleeping:
                in_dict_sleeping.append(player.username)

    ping_by_chat_id.update({mes.chat_id : ping_dict})
    response += "Пингануть тех, кто спит: /notify_guild_sleeping\n" \
                "Пингануть всех, кто не готов: /notify_guild_not_ready"
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode = 'HTML')


def notify_guild_to_battle(bot, update):
    mes = update.message
    chat_dict = ping_by_chat_id.get(mes.chat_id)
    if chat_dict is None:
        return
    if mes.from_user.id not in get_admin_ids(bot, chat_id=mes.chat_id) and not check_access(mes.from_user.id):
        bot.send_message(chat_id=mes.chat_id, text="Доступ только у админов", parse_mode='HTML')
        return
    if mes.text.partition("@")[0].split("_")[2] == "sleeping":
        target_list = chat_dict.get("sleeping")
    else:
        target_list = chat_dict.get("do not ready")
    i = 0
    response = ""
    for username in target_list:
        if i >= 4:
            response += "\n БИТВА!"
            bot.send_message(chat_id=mes.chat_id, text = response)
            response = ""
            i = 0
        response += "@{0} ".format(username)
        i += 1
    response += "\n БИТВА!"
    bot.send_message(chat_id=mes.chat_id, text=response)
