"""
В этом модуле находятся все функции для работы с гильдиями как с сущностями: создание, изменение и любые другие
операции с гильдиями, и игроками в них
"""
from castle_files.libs.guild import Guild
from castle_files.libs.player import Player
from castle_files.libs.bot_async_messaging import MAX_MESSAGE_LENGTH

from castle_files.bin.buttons import get_edit_guild_buttons, get_general_buttons, get_view_guild_buttons

from telegram.error import TelegramError

from castle_files.work_materials.globals import dispatcher, cursor, conn
from telegram.ext.dispatcher import run_async

import logging
import re


# Создание новой гильдии
def create_guild(bot, update):
    guild_tag = update.message.text.partition(' ')[2]
    if len(guild_tag) <= 0 or len(guild_tag) > 3:
        bot.send_message(chat_id=update.message.chat_id, text="Неверный синтаксис. Укажите тэг новой гильдии.")
        return
    if any(c in guild_tag for c in ['\f', '\n', '\r', '\t', '\v', ' ']):
        bot.send_message(chat_id=update.message.chat_id, text="Неверный синтаксис. "
                                                              "Тэг не должен содержать пробелы или иные разделители.")
        return
    guild = Guild.get_guild(guild_tag=guild_tag)
    if guild is not None:
        bot.send_message(chat_id=update.message.chat_id, text="Гильдия с этим тэгом уже существует!")
        return
    guild = Guild(None, guild_tag, None, None, None, None, None, None, None, None, None, None, None)
    guild.create_guild()
    bot.send_message(chat_id=update.message.chat_id, text="Гильдия успешно создана! Отредактируйте её: "
                                                          "/edit_guild_{}".format(guild.id))
    return


# ДОРОГАЯ ОПЕРАЦИЯ - получение (и вывод в сообщении) списка ги
# @run_async
def list_guilds(bot, update):
    response = "Список зарегистрированных в боте гильдий:\n\n"
    for guild_id in Guild.guild_ids:
        guild = Guild.get_guild(guild_id=guild_id)
        if guild is None:
            logging.warning("Guild is None for the id {}".format(guild_id))
            continue
        response_new = "<b>{}</b>{}\nДивизион: {}\nРедактировать: /edit_guild_{}\n" \
                       "\n".format(guild.tag, " --- " + guild.name if guild.name is not None else "",
                                   guild.division or "Не задан", guild.id)
        response_new += "⚔: <b>{}</b>, 🛡: <b>{}</b>\n\n----------------------------------" \
                        "\n".format(guild.get_attack(), guild.get_defense())
        if len(response + response_new) > MAX_MESSAGE_LENGTH:
            bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML')
            response = ""
        response += response_new
    response += "Добавить гильдию: /create_guild {TAG}"
    bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML')


# @dispatcher.run_async # Не работает
def guild_info(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        bot.send_message(chat_id=mes.chat_id, text="Игрок не найден. Отправьте /hero из @ChatWarsBot.")
        return
    if player.guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Вы не состоите в гильдии. Вступите в гильдию в игре и попросите "
                                                   "командира добавить вас в гильдейском чате.")
        return
    guild = Guild.get_guild(guild_id=player.guild)
    if guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена.")
        return
    commander = Player.get_player(guild.commander_id)
    response = "<b>{}</b>  {}\n".format(guild.tag, guild.name or "")
    response += "Командир: {}\n".format("@" + commander.username if commander is not None else "Не задан")
    response += "Чат отряда: {}, id: {}" \
                "\n{}\n".format(guild.chat_name or "Не задан",
                                "<code>{}</code>".format(guild.chat_id) if guild.chat_id is not None else "Не задан",
                                "<a href=\"{}\">Вступить</a>".format("https://t.me/joinchat/" + guild.invite_link)
                                if guild.invite_link is not None else "")

    response += "\nИгроков в гильдии: <b>{}</b>\n".format(guild.members_count)
    response += "⚔: <b>{}</b>, 🛡: <b>{}</b>\n".format(guild.get_attack(), guild.get_defense())
    buttons = get_view_guild_buttons(guild)
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML', reply_markup=buttons)


def list_players(bot, update, guild_id=None):
    mes = update.callback_query.message
    if guild_id is None:
        player = Player.get_player(update.callback_query.from_user.id)
        if player is None:
            bot.send_message(chat_id=mes.chat_id, text="Игрок не найден. Отправьте /hero из @ChatWarsBot.")
            return
        guild_id = player.guild
        if guild_id is None:
            bot.send_message(chat_id=mes.chat_id,
                             text="Вы не состоите в гильдии. Вступите в гильдию в игре и попросите "
                                  "командира добавить вас в гильдейском чате.")
            return
    guild = Guild.get_guild(guild_id=guild_id)
    if guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена.")
        return
    response = "Список игроков в гильдии <b>{}</b>\n".format(guild.tag)
    guild.sort_players_by_exp()
    for player_id in guild.members:
        player = Player.get_player(player_id)
        if player is None:
            logging.warning("Player in guild is None, guild = {}, player_id = {}".format(guild.tag, player_id))
            continue
        response_new = "<b>{}</b>\n🏅: <code>{}</code>, ⚔: <code>{}</code>, 🛡: <code>{}</code>" \
                       "\nПоказать профиль: /view_profile_{}" \
                       "\nУдалить из гильдии: /remove_player_{}" \
                       "\n\n".format(player.nickname, player.lvl, player.attack, player.defense, player.id, player.id)
        if len(response + response_new) > MAX_MESSAGE_LENGTH:
            bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
            response = ""
        response += response_new
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


# Функция для принудительного удаления игрока из гильдии
def remove_player(bot, update):
    mes = update.message
    player_id = re.search("_(\\d+)", mes.text)
    if player_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return
    player_id = int(player_id.group(1))
    if player_id == mes.from_user.id:
        bot.send_message(chat_id=mes.chat_id, text="Почему бы не выйти как нормальный человек? /leave_guild")
        return
    current_player = Player.get_player(mes.from_user.id)
    if current_player is None:
        return
    guild = Guild.get_guild(guild_id=current_player.guild)
    if guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Вы не состоите в гильдии.")
        return
    if not guild.check_high_access(current_player.id):
        bot.send_message(chat_id=mes.chat_id, text="Право распоряжаться людьми необходимо заслужить.")
        return
    player_to_remove = Player.get_player(player_id)
    if player_to_remove is None or player_to_remove.id not in guild.members:
        bot.send_message(chat_id=mes.chat_id, text="Вы можете удалять игроков только в своей гильдии.")
        return
    guild.delete_player(player_to_remove)
    bot.send_message(chat_id=update.message.chat_id, text="<b>{}</b> успешно удалён из гильдии "
                                                          "<b>{}</b>".format(player_to_remove.nickname, guild.tag),
                     parse_mode='HTML')
    bot.send_message(chat_id=player_to_remove.id,
                     text="Появившийся из-за угла стражник окликнул вас:\n"
                          "<em>Твой командир просил передать, что ты больше не в гильдии, воин!</em>",
                     parse_mode='HTML')


def leave_guild(bot, update):
    if update.message is not None:
        mes = update.message
        user_id = mes.from_user.id
    else:
        mes = update.callback_query.message
        user_id = update.callback_query.from_user.id
    player = Player.get_player(user_id)
    if player is None:
        bot.send_message(chat_id=mes.chat_id, text="Игрок не найден. Пожалуйста, отправьте форвард /hero.")
        return
    if player.guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Вы не состоите в гильдии.")
        return
    guild = Guild.get_guild(guild_id=player.guild)
    if guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена.")
        return
    if guild.commander_id == player.id:
        bot.send_message(chat_id=mes.chat_id, text="Командир не может покинуть гильдию")
        return
    guild.delete_player(player)
    bot.send_message(chat_id=mes.chat_id, text="Вы успешно покинули гильдию")
    if update.callback_query is not None:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


# Добавление игрока в гильдию
def add(bot, update):
    player = Player.get_player(update.message.from_user.id)
    if player is None:
        bot.send_message(chat_id=update.message.chat_id, text="Игрок не найден. Пожалуйста, отправьте форвард /hero.")
        return
    guild = Guild.get_guild(guild_id=player.guild)
    if guild is None:
        bot.send_message(chat_id=update.message.chat_id, text="Гильдия не найдена.")
        return
    if player.guild != guild.id:
        bot.send_message(chat_id=update.message.chat_id, text="Можно добавлять игроков только в свою гильдию")
        return
    if update.message.chat_id != guild.chat_id:
        bot.send_message(chat_id=update.message.chat_id, text="Добавлять игроков в гильдию можно только в официальном "
                                                              "чате гильдии")
        return
    if player.id != guild.commander_id and player.id not in guild.assistants:
        bot.send_message(chat_id=update.message.chat_id, text="Только командир и его замы могут добавлять бойцов.")
        return
    if update.message.reply_to_message is None:
        bot.send_message(chat_id=update.message.chat_id, text="Сообщение должно являться ответом на сообщение игрока, "
                                                              "которого необходимо добавить в гильдию.")
        return
    player_to_add = Player.get_player(update.message.reply_to_message.from_user.id)
    if player_to_add is None:
        bot.send_message(chat_id=update.message.chat_id, text="Игрок для добавления не найден.")
        return
    if player_to_add.guild is not None:
        bot.send_message(chat_id=update.message.chat_id, text="Игрок уже находится в гильдии.")
        return
    guild.add_player(player_to_add)

    bot.send_message(chat_id=update.message.chat_id, text="<b>{}</b> успешно добавлен в гильдию "
                                                          "<b>{}</b>".format(player_to_add.nickname, guild.tag),
                     parse_mode='HTML')


# Генерирует корректный и обновлённый текст в ответе на изменение гильдии. Генерируется каждый раз при изменении ги
def get_edit_guild_text(guild):

    if guild.commander_id is not None:
        commander = Player.get_player(guild.commander_id)
    else:
        commander = None

    response = "Командир: {}\n".format("@" + commander.username if commander is not None else "Не задан")
    response += "Чат отряда: <code>{}</code>, id: {}" \
                "\n{}".format(guild.chat_name or "Не задан",
                              "<code>{}</code>".format(guild.chat_id) if guild.chat_id is not None else "Не задан",
                              "<a href=\"{}\">Вступить</a>".format("https://t.me/joinchat/" + guild.invite_link)
                              if guild.invite_link is not None else "")
    response += "\n\n⚔: <b>{}</b>, 🛡: <b>{}</b>\n".format(guild.get_attack(), guild.get_defense())
    response += "Дивизион: <b>{}</b>\n".format(guild.division or "не задан")
    response += "Приказы <b>{}</b>\n".format("включены" if guild.orders_enabled else "оключены")
    response += "Сообщения <b>{}</b>\n".format("пинятся" if guild.pin_enabled else "не пинятся")
    response += "Пины <b>{}</b>\n".format("громкие" if not guild.disable_notification else "тихие")
    return response


# Команда /edit_guild
def edit_guild(bot, update):
    mes = update.message
    if mes.chat_id != mes.from_user.id:
        bot.send_message(chat_id=mes.chat_id, text="Команда разрешена только в лс.")
        return
    try:
        guild_id = int(mes.text.partition("@")[0].split("_")[2])
    except ValueError:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис")
        return
    guild = Guild.get_guild(guild_id=guild_id)
    if guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена")
        return
    response = "Гильдия <b>{}</b>\n".format(guild.tag)
    response += get_edit_guild_text(guild)
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML', reply_markup=get_edit_guild_buttons(guild))
    return


# Нажатие инлайн-кнопки "Изменить командира"
def edit_guild_commander(bot, update, user_data):
    try:
        user_data.update({"status": "edit_guild_commander",
                          "edit_guild_id": int(update.callback_query.data.split("_")[1])})
    except ValueError:
        bot.send_message(chat_id=update.callback_query.message.chat_id, text="Произошла ошибка")
    else:
        bot.send_message(chat_id=update.callback_query.message.chat_id, text="Введите id нового командира гильдии, "
                                                                             "или наберите /cancel для отмены")
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


# Ввод id командира
def change_guild_commander(bot, update, user_data):
    mes = update.message
    try:
        player_id = int(mes.text)
    except ValueError:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return
    player = Player.get_player(player_id)
    if player is None:
        bot.send_message(chat_id=mes.chat_id, text="Игрок не найден. Проверьте правильность ввода id.")
        return
    guild_id = user_data.get("edit_guild_id")
    guild = None
    if guild_id is not None:
        guild = Guild.get_guild(guild_id=guild_id)
    if guild_id is None or guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена. Начните сначала.")
        return
    print(player.guild_tag, player.guild_tag, guild.tag)
    if player.guild_tag is not None and player.guild_tag != guild.tag:
        bot.send_message(chat_id=mes.chat_id, text="Командир может командовать только своей гильдией")
        return
    if player.guild_tag is None or player.guild is None:
        guild.add_player(player)
    guild.commander_id = player_id
    if guild.members is None:
        guild.members = []
    if player.id not in guild.members:
        guild.members.append(player.id)
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


# Нажатие инлайн-кнопки "Изменить чат гильдии"
def edit_guild_chat(bot, update, user_data):
    try:
        user_data.update(
            {"status": "edit_guild_chat", "edit_guild_id": int(update.callback_query.data.split("_")[1])})
    except ValueError:
        bot.send_message(chat_id=update.callback_query.message.chat_id, text="Произошла ошибка")
    else:
        bot.send_message(chat_id=update.callback_query.message.chat_id, text="Введите id нового чата гильдии, "
                                                                             "или наберите /cancel для отмены")
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


# Ввод айди нового чата ги
def change_guild_chat(bot, update, user_data):
    mes = update.message
    try:
        chat_id = int(mes.text)
    except ValueError:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return
    guild_id = user_data.get("edit_guild_id")
    guild = None
    if guild_id is not None:
        guild = Guild.get_guild(guild_id=guild_id)
    if guild_id is None or guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена. Начните сначала.")
        return
    try:
        message = bot.sync_send_message(chat_id=chat_id, text="Это теперь официальный чат гильдии "
                                                              "<b>{}</b>".format(guild.tag), parse_mode='HTML')
        chat = bot.getChat(message.chat_id)
        if chat is None:
            bot.send_message(chat_id=update.message.chat_id, text="Произошла ошибка. Проверьте id "
                                                                  "и присутствие бота в этом чате")
            return
    except TelegramError:
        bot.send_message(chat_id=update.message.chat_id, text="Произошла ошибка. Проверьте id "
                                                              "и присутствие бота в этом чате")
        return
    guild.chat_id = chat.id
    guild.chat_name = chat.title
    try:
        guild.invite_link = bot.exportChatInviteLink(chat_id)
        if guild.invite_link is not None:
            guild.invite_link = guild.invite_link[22:]  # Обрезаю https://t.me/joinchat/
    except TelegramError:
        pass
    guild.update_to_database()
    bot.send_message(chat_id=mes.chat_id, text="Чат гильдии <b>{}</b> успешно изменён "
                                               "на <b>{}</b>".format(guild.tag, guild.chat_name or guild.chat_id),
                     parse_mode='HTML')
    if "status" in user_data:
        user_data.pop("status")
    if "edit_guild_id" in user_data:
        user_data.pop("edit_guild_id")


def edit_guild_division(bot, update, user_data):
    try:
        user_data.update(
            {"status": "edit_guild_division", "edit_guild_id": int(update.callback_query.data.split("_")[1])})
    except ValueError:
        bot.send_message(chat_id=update.callback_query.message.chat_id, text="Произошла ошибка")
    else:
        bot.send_message(chat_id=update.callback_query.message.chat_id,
                         text="Введите название нового дивизиона гильдии, или наберите /cancel для отмены")
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


def change_guild_division(bot, update, user_data):
    mes = update.message
    guild_id = user_data.get("edit_guild_id")
    guild = None
    if guild_id is not None:
        guild = Guild.get_guild(guild_id=guild_id)
    if guild_id is None or guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена. Начните сначала.")
        return
    guild.division = mes.text
    guild.update_to_database()
    bot.send_message(chat_id=mes.chat_id, text="Дивизион <b>{}</b> изменён на "
                                               "<b>{}</b>".format(guild.tag, guild.division),
                     parse_mode='HTML')
    if "status" in user_data:
        user_data.pop("status")
    if "edit_guild_id" in user_data:
        user_data.pop("edit_guild_id")


def change_guild_bool_state(bot, update):
    try:
        guild_id = int(update.callback_query.data.split("_")[1])
    except ValueError:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                                text="Произошла ошибка. Попробуйте ещё раз")
        return
    guild = Guild.get_guild(guild_id)
    if guild is None:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                                text="Гильдия не найдена. Попробуйте ещё раз")
        return
    edit_type = update.callback_query.data[2]
    if edit_type == 'o':
        guild.orders_enabled = not guild.orders_enabled
    elif edit_type == 'p':
        guild.pin_enabled = not guild.pin_enabled
    elif edit_type == 'n':
        guild.disable_notification = not guild.disable_notification
    guild.update_to_database()
    mes = update.callback_query.message
    reply_markup = get_edit_guild_buttons(guild)
    new_text = get_edit_guild_text(guild)
    try:
        bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=new_text, reply_markup=reply_markup,
                            parse_mode='HTML')
    except TelegramError:
        pass
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                            text="Успешно изменено.")


# Информация о чате в лс
def chat_info(bot, update):
    response = "<b>{}</b>, id: <code>{}</code>".format(update.message.chat.title, update.message.chat_id)
    bot.send_message(chat_id=update.message.from_user.id, text=response, parse_mode='HTML')
