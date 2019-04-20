"""
В этом модуле находятся все функции для работы с гильдиями как с сущностями: создание, изменение и любые другие
операции с гильдиями, и игроками в них
"""
from castle_files.libs.guild import Guild
from castle_files.libs.player import Player

from castle_files.bin.buttons import get_edit_guild_buttons

from telegram.error import TelegramError


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
    guild = Guild(None, guild_tag, None, None, None, None, None, None, None, None, None)
    guild.create_guild()
    bot.send_message(chat_id=update.message.chat_id, text="Гильдия успешно создана! Отредактируйте её: "
                                                          "/edit_guild_{}".format(guild.id))
    return


# Команда /edit_guild
def edit_guild(bot, update):
    mes = update.message
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
    if guild.commander_id is not None:
        commander = Player.get_player(guild.commander_id)
    else:
        commander = None
    response += "Командир: {}\n".format("@" + commander.username if commander is not None else "Не задан")
    response += "Чат отряда: {}, id: {}" \
                "\n{}".format(guild.chat_name or "Не задан",
                              "<code>{}</code>".format(guild.chat_id) if guild.chat_id is not None else "Не задан",
                              "<a href=\"{}\">Вступить</a>".format("https://t.me/joinchat/" + guild.invite_link)
                              if guild.invite_link is not None else "")
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML', reply_markup=get_edit_guild_buttons(guild))
    return


# Нажатие инлайн-кнопки "Изменить командира"
def edit_guild_commander(bot, update, user_data):
    try:
        user_data.update({"status": "edit_guild_commander", "edit_guild_id": int(update.callback_query.data.split("_")[1])})
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
    if player.guild_tag is None:
        player.guild_tag = guild.tag
        player.guild = guild.id
    guild.commander_id = player_id
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


# Информация о чате в лс
def chat_info(bot, update):
    response = "<b>{}</b>, id: <code>{}</code>".format(update.message.chat.title, update.message.chat_id)
    bot.send_message(chat_id=update.message.from_user.id, text=response, parse_mode='HTML')
