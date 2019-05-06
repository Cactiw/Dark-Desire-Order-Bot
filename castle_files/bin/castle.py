"""
В этом модуле находятся функции, связанные с "игровым" замком - виртуальным замком Скалы в боте
"""
from castle_files.bin.buttons import send_general_buttons, get_general_buttons
from castle_files.libs.castle.location import Location
from castle_files.libs.player import Player
from castle_files.libs.guild import Guild

from castle_files.work_materials.globals import high_access_list, DEFAULT_CASTLE_STATUS

from telegram import ReplyKeyboardMarkup

import re


def change_rp(bot, update, user_data):
    if update.message.from_user.id != update.message.chat_id:
        return
    rp_off = user_data.get("rp_off")
    if rp_off:
        user_data.pop("rp_off")
        user_data.update({"status": DEFAULT_CASTLE_STATUS})
        send_general_buttons(update.message.from_user.id, user_data, bot=bot)
        return
    user_data.update({"status": "rp_off", "rp_off": True})
    bot.send_message(chat_id=update.message.chat_id, text="Режим РП отключён. Если Вы захотите снова использовать "
                                                          "все функции, нажмите /change_rp ещё раз.")
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def back(bot, update, user_data):
    statuses_back = {
        "barracks": "central_square",
        "central_square": "central_square",
        "castle_gates": "central_square",
        "throne_room": "central_square",
        "mid_feedback": "throne_room",
        "duty_feedback": "castle_gates",
        "king_cabinet": "throne_room"

    }
    status = user_data.get("status")
    if status is None:
        send_general_buttons(update.message.from_user.id, user_data, bot=bot)
        return
    new_status = statuses_back.get(status)
    new_location = Location.get_id_by_status(new_status)
    user_data.update({"status": new_status, "location_id": new_location})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def guide_signs(bot, update):  # TODO: сделать нормально
    bot.send_message(chat_id=update.message.from_user.id,
                     text="🗺Указатели гласят:\n"
                          "🎪<b>Казарма</b>- штаб-квартира твоей гильдии. "
                          "Здесь ты всегда найдешь своих согильдейцев, узнаешь свои достижения и достижения "
                          "своих соратников, узнаешь о ратных подвигах и не только.\n\n"
                          "⛩<b>Городские Врата</b> - тут всегда можно перекинуться парочкой слов с местными стражами, "
                          "им все равно скучно на посту.\n\n"
                          "🏛<b>Тронный Зал</b> - место, где можно узнать новости, задать вопрос полководцам и даже "
                          "попросить аудиенцию Короля."
                          "\n\n❓\n\n❓\n\n❓\n\n❓\n\n❓\n\n❓\n\n<em>На указателях ещё много места, возможно, в будущем, "
                          "там появятся новые строки</em>", parse_mode='HTML')


def not_constructed(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Свободное место под возведение жизненно важных городских построек и сооружений.\n"
                          "Сейчас в замке нет активного строительства. Следите за новостями.")


def welcome(bot, update, user_data):
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def central_square(bot, update, user_data):
    user_data.update({"status": "central_square", "location_id": 0})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def barracks(bot, update, user_data):
    user_data.update({"status": "barracks", "location_id": 1})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def throne_room(bot, update, user_data):
    user_data.update({"status": "throne_room", "location_id": 2})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def castle_gates(bot, update, user_data):
    location_id = 3
    user_data.update({"status": "castle_gates", "location_id": 3})
    response = Location.get_location_enter_text_by_id(location_id)
    player = Player.get_player(update.message.from_user.id)
    buttons = get_general_buttons(user_data, only_buttons=True, player=player)
    if player is not None and player.game_class == "Sentinel":  # Только для стражей, захардкожено
        response += "\nКак страж, ты имеешь возможность заступить на вахту\n"
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML', reply_markup=reply_markup)


# Заполнение списка мида, запускать при старте бота и при обновлении состава
def fill_mid_players():
    high_access_list.clear()
    throne = Location.get_location(2)
    mid_players = throne.special_info.get("mid_players")
    for player_id in mid_players:
        high_access_list.append(player_id)


# Посмотреть состав мида
def watch_portraits(bot, update):
    response = "Стены замка увешаны портретами текущих генералов Скалы:\n"
    for user_id in high_access_list:
        player = Player.get_player(user_id, notify_on_error=False)
        if player is None:
            continue
        response += "@{} - <b>{}</b>\n".format(player.username, player.nickname)
    bot.send_message(chat_id=update.message.from_user.id, text=response, parse_mode='HTML')


def headquarters(bot, update, user_data):
    user_data.update({"status": "headquarters", "location_id": 4})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def request_guild_message_notify(bot, update, user_data):
    user_data.update({"status": "sending_guild_message"})
    bot.send_message(chat_id=update.message.from_user.id, text="Следующее сообщение будет разослано во все гильдии")


def send_guild_message_notify(bot, update, user_data):
    user_data.update({"status": "headquarters"})
    for guild_id in Guild.guild_ids:
        guild = Guild.get_guild(guild_id=guild_id)
        bot.send_message(chat_id=guild.chat_id, text=update.message.text, parse_mode='HTML')
    bot.send_message(update.message.from_user.id, text="Успешно отправлено!")


def king_cabinet(bot, update, user_data):
    response = "Вы входите в свой кабинет. Память услужливо подсказывает вам текущий список генералов:\n"
    for user_id in high_access_list:
        player = Player.get_player(user_id, notify_on_error=False)
        if player is None:
            continue
        response += "@{} - <b>{}</b>\nОтправить в ссылку: /remove_general_{}\n" \
                    "\n".format(player.username, player.nickname, player.id)
    user_data.update({"status": "king_cabinet"})
    buttons = get_general_buttons(user_data)
    bot.send_message(chat_id=update.message.from_user.id, text=response, reply_markup=buttons, parse_mode='HTML')


def request_change_castle_message(bot, update, user_data):
    central = Location.get_location(0)
    current_message = central.special_info.get("enter_text_format_values")
    user_data.update({"status": "changing_castle_message"})
    bot.send_message(chat_id=update.message.from_user.id,
                     text="Текущее сообщение:\n<em>{}</em>\nВведите новое сообщение. Не делайте его слишком большим."
                          "".format(current_message), parse_mode='HTML')


def change_castle_message(bot, update, user_data):
    central = Location.get_location(0)
    central.special_info.update({"enter_text_format_values": update.message.text})
    central.update_location_to_database()
    user_data.update({"status": "king_cabinet"})
    bot.send_message(chat_id=update.message.from_user.id,
                     text="Новое сообщение:\n<em>{}</em>".format(update.message.text), parse_mode='HTML')


def add_general(bot, update, user_data):
    user_data.update({"status": "adding_general"})
    bot.send_message(chat_id=update.message.from_user.id, text="Введите id нового генерала, или нажмите \"Назад\"")


def adding_general(bot, update, user_data):
    mes = update.message
    try:
        player_id = int(mes.text)
    except ValueError:
        bot.send_message(chat_id=update.message.from_user.id, text="Неверный синтаксис.")
        return
    if player_id in high_access_list:
        bot.send_message(chat_id=update.message.from_user.id, text="Этот человек уже являетсяс генералом.")
        return
    player = Player.get_player(player_id, notify_on_error=False)
    if player is None:
        bot.send_message(chat_id=update.message.from_user.id, text="Невозможно найти этого холопа. "
                                                                   "Убедитесь, что он зарегистрирован в боте")
        return
    throne = Location.get_location(2)
    mid_players = throne.special_info.get("mid_players")
    mid_players.append(player_id)
    throne.update_location_to_database()
    fill_mid_players()
    bot.send_message(chat_id=update.message.from_user.id, text="@{} теперь генерал!".format(player.username))
    user_data.update({"status": "king_cabinet"})


def remove_general(bot, update):
    mes = update.message
    player_id = re.search("_(\\d+)", mes.text)
    if player_id is None:
        bot.send_message(chat_id=update.message.from_user.id, text="Неверный синтаксис.")
        return
    player_id = int(player_id.group(1))
    if player_id not in high_access_list:
        bot.send_message(chat_id=update.message.from_user.id, text="Так он, это, вроде и не генерал вовсе. "
                                                                   "Может, помилуем?")
        return
    player = Player.get_player(player_id, notify_on_error=False)
    throne = Location.get_location(2)
    mid_players = throne.special_info.get("mid_players")
    mid_players.remove(player_id)
    throne.update_location_to_database()
    fill_mid_players()
    bot.send_message(chat_id=update.message.from_user.id,
                     text="@{} сослан в тортугу и больше не генерал".format(player.username))
