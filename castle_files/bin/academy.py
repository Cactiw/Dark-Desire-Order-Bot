"""
Здесь находятся функции для работы с гильдией АКАДЕМИЯ
"""

from castle_files.libs.guild import Guild
from castle_files.libs.player import Player


def change_headmaster(bot, update, player, guild, user_data):
    """
    Функция изменения ректора Академии
    """
    guild.commander_id = player.id
    guild.update_to_database()
    if "status" in user_data:
        user_data.pop("status")
    if "edit_guild_id" in user_data:
        user_data.pop("edit_guild_id")
    bot.send_message(chat_id=update.message.chat_id, text="Командиром гильдии <b>{}</b> назначен <b>{}</b> "
                                                          "{}".format(guild.tag, player.nickname,
                                                                      "(@{})".format(player.username)
                                                                      if player.username is not None else ""),
                     parse_mode='HTML')


def add_teacher(bot, update):
    """
    Фукнция добавления учителя
    """
    mes = update.message
    academy = Guild.get_guild(guild_tag="АКАДЕМИЯ")
    if academy is None:
        bot.send_message(chat_id=mes.chat_id, text="Академия не найдена. Обратитесь к @Cactiw")
        return
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    if player.id != academy.commander_id:
        bot.send_message(chat_id=update.message.chat_id, text="Только глава академии может добавлять учителей.")
        return
    if mes.reply_to_message is None:
        bot.send_message(chat_id=update.message.chat_id, text="Сообщение должно являться ответом на сообщение игрока, "
                                                              "которого необходимо сделать учителем.")
        return
    player_to_add = Player.get_player(update.message.reply_to_message.from_user.id)
    if player_to_add is None:
        bot.send_message(chat_id=update.message.chat_id, text="Игрок для добавления не найден.")
        return
    if academy.check_high_access(player_to_add.id):
        bot.send_message(chat_id=update.message.chat_id, text="Игрок уже имеет необходимые права.")
        return
    academy.assistants.append(player_to_add.id)
    academy.update_to_database()
    bot.send_message(chat_id=update.message.chat_id,
                     text="<b>{}</b> теперь учитель!".format(player_to_add.nickname),
                     parse_mode='HTML', reply_to_message_id=update.message.message_id)


def del_teacher(bot, update):
    """
    Функция удаления учителя
    """
    mes = update.message
    academy = Guild.get_guild(guild_tag="АКАДЕМИЯ")
    if academy is None:
        bot.send_message(chat_id=mes.chat_id, text="Академия не найдена. Обратитесь к @Cactiw")
        return
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    if player.id != academy.commander_id:
        bot.send_message(chat_id=update.message.chat_id, text="Только глава академии может удалять учителей.")
        return
    if mes.reply_to_message is None:
        bot.send_message(chat_id=update.message.chat_id, text="Сообщение должно являться ответом на сообщение игрока, "
                                                              "которого необходимо снять с должности учителя.")
        return
    player_to_add = Player.get_player(update.message.reply_to_message.from_user.id)
    if player_to_add is None:
        bot.send_message(chat_id=update.message.chat_id, text="Игрок для удаления не найден.")
        return
    if academy.commander_id == player_to_add.id:
        bot.send_message(chat_id=update.message.chat_id, text="Нельзя снять главу академии.")
        return
    if not academy.check_high_access(player_to_add.id):
        bot.send_message(chat_id=update.message.chat_id, text="Игрок и так не учитель.")
        return
    academy.assistants.remove(player_to_add.id)
    academy.update_to_database()
    bot.send_message(chat_id=update.message.chat_id,
                     text="<b>{}</b> больше не учитель!".format(player_to_add.nickname),
                     parse_mode='HTML', reply_to_message_id=update.message.message_id)
