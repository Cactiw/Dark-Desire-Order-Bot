"""
В этом модуле находятся функции, связанные с "игровым" замком - виртуальным замком Скалы в боте
"""
from castle_files.bin.buttons import send_general_buttons, get_general_buttons, get_tops_buttons
from castle_files.bin.service_functions import dict_invert
from castle_files.bin.common_functions import unknown_input
from castle_files.bin.mid import do_mailing, fill_mid_players
from castle_files.bin.quests import return_from_quest
from castle_files.libs.castle.location import Location
from castle_files.libs.player import Player
from castle_files.libs.guild import Guild

from castle_files.work_materials.globals import high_access_list, DEFAULT_CASTLE_STATUS, cursor, conn, SUPER_ADMIN_ID, \
    classes_to_emoji, CENTRAL_SQUARE_CHAT_ID, job, moscow_tz
from globals import update_request_queue

from telegram import ReplyKeyboardMarkup
from telegram.error import BadRequest, TelegramError

import re
import logging
import traceback
import random
import time
import datetime

TOP_NUM_PLAYERS = 20

emoji_to_class = dict_invert(classes_to_emoji)


def change_rp(bot, update, user_data):
    if update.message.from_user.id != update.message.chat_id:
        return
    user_data.update({"status": DEFAULT_CASTLE_STATUS})
    rp_off = user_data.get("rp_off")
    if rp_off:
        user_data.pop("rp_off")
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

        "king_cabinet": "throne_room",
        "headquarters": "throne_room",
        "changing_castle_message": "king_cabinet",
        "sending_guild_message": "headquarters",
        "editing_debrief": "headquarters",

        "technical_tower": "central_square",
        "my_cabinet": "technical_tower",
        "sending_bot_guild_message": "technical_tower",
        "editing_update_message": "technical_tower",

        "sawmill": "castle_gates",
        "quarry": "castle_gates",
        "construction": "construction_plate",
        "construction_plate": "central_square",

        "treasury": "throne_room",

        "hall_of_fame": "central_square",
        # "tops": "hall_of_fame",

        "tops": "central_square",

        "manuscript": "technical_tower",
        "guides": "manuscript",

        "tea_party": "central_square",
        "exploration": "tea_party",
        "pit": "tea_party",

        "roulette": "tea_party",
        "awaiting_roulette_bet": "roulette",

    }

    statuses_rp_off = {
        "tops": DEFAULT_CASTLE_STATUS,
        "mid_feedback": DEFAULT_CASTLE_STATUS,


        "manuscript": DEFAULT_CASTLE_STATUS,
    }

    status = user_data.get("status")
    if status is None:
        send_general_buttons(update.message.from_user.id, user_data, bot=bot)
        return
    if status in ["sawmill", "quarry", "construction", "exploration", "pit", "waiting_second_player_for_quest",
                  "two_quest"]:
        if "quest_name" in user_data:
            return_from_quest(update.message.from_user.id, user_data)
        bot.send_message(chat_id=update.message.from_user.id, text="Операция отменена.")
    rp_off = user_data.get("rp_off") or False
    new_status = None
    if rp_off:
        new_status = statuses_rp_off.get(status)
    if new_status is None:
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
                          "попросить аудиенцию Короля.\n\n"
                          "🔭<b>Башня Техно-Магических наук</b> - основа ордена Темного Желания. Здесь по крупицам "
                          "собираются вести и отзывы о работе техно-магических артефактов, "
                          "публикуются новости о работе ордена над усовершенствованием техно-магических "
                          "приспособлений Скалы."
                          "\n\n🏤<b>Мандапа Славы</b> -  почетное место, где увековечены герои Скалы, их подвиги и "
                          "заслуги перед замком. Вечная слава и почет!\n\n❓\n\n❓\n\n"
                          "<em>На указателях ещё много места, возможно, в будущем, "
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


def request_change_debrief(bot, update, user_data):
    user_data.update({"status": "editing_debrief"})
    buttons = get_general_buttons(user_data)
    bot.send_message(chat_id=update.message.from_user.id,
                     text="Следующее сообщение будет новым дебрифом. Он должен влезть в это сообщение:\n\n"
                          "{}".format(Location.get_location_enter_text_by_id(2, without_format=True).format(
                                "DjedyBreaM", "")), reply_markup=buttons)


def change_debrief(bot, update, user_data):
    user_data.update({"status": "throne_room", "location_id": 2})
    throne = Location.get_location(2)
    format_values = throne.special_info.get("enter_text_format_values")
    format_values[1] = update.message.text
    throne.special_info.update({"enter_text_format_values": format_values})
    throne.update_location_to_database()
    bot.send_message(chat_id=update.message.from_user.id,
                     text="Дебриф успешно изменён. Вы выходите в тронный зал, чтобы проверить, что всё выглядит "
                          "хорошо.\n\n<em>В случае, если после этого не последует сообщение с дебрифом, "
                          "измените его</em>", parse_mode='HTML')
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def request_guild_message_notify(bot, update, user_data):
    user_data.update({"status": "sending_guild_message"})
    buttons = get_general_buttons(user_data)
    bot.send_message(chat_id=update.message.from_user.id, text="Следующее сообщение будет разослано во все гильдии",
                     reply_markup=buttons)


def send_guild_message_notify(bot, update, user_data):
    user_data.update({"status": "headquarters"})
    do_mailing(bot, update.message.text)
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
    buttons = get_general_buttons(user_data)
    bot.send_message(chat_id=update.message.from_user.id,
                     text="Текущее сообщение:\n<em>{}</em>\nВведите новое сообщение. Не делайте его слишком большим."
                          "".format(current_message), parse_mode='HTML', reply_markup=buttons)


def change_castle_message(bot, update, user_data):
    central = Location.get_location(0)
    old_format = central.special_info.get("enter_text_format_values")
    old_format[0] = update.message.text
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
    # update_request_queue.put(["update_mid"])


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
    # update_request_queue.put(["update_mid"])


def hall_of_fame(bot, update, user_data):
    hall = Location.get_location(8)
    if not hall.is_constructed() and update.message.from_user.id != SUPER_ADMIN_ID:
        unknown_input(bot, update, user_data)
        return
    tops(bot, update, user_data, response="Вы входите в Мандапу Славы - почетное место, где увековечены герои Скалы, "
                                          "их подвиги и заслуги перед замком. На стене развешены лучшие из лучших.\n\n")
    """
    user_data.update({"status": "hall_of_fame", "location_id": 8})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)
    """


def tops(bot, update, user_data, response=""):
    user_data.update({"status": "tops"})
    buttons = get_general_buttons(user_data)
    response += "Выберите категорию:"
    bot.send_message(chat_id=update.message.chat_id, text=response, reply_markup=buttons)


def get_tops_text(player, stat, stat_text, game_class=None):
    response = "Топ {} по замку:\n".format(stat_text)
    found = False
    if player is None:
        found = True
    if stat in ["wood", "stone", "construction"]:
        if stat == "construction":
            request = "select nickname, count(1) as construction_count, game_class, lvl, player_id from castle_logs " \
                      "left join players on castle_logs.player_id = players.id where action = 'construction' {}" \
                      "group by nickname, game_class, lvl, player_id order by construction_count desc;" \
                      "".format("and game_class = '{}' ".format(game_class) if game_class is not None else "")
        else:
            request = "select nickname, count(1) as res_count, game_class, lvl, player_id from castle_logs " \
                      "left join players on castle_logs.player_id = players.id where action = 'collect_resources' and "\
                      "additional_info ->> 'resource' = '{}' {}group by nickname, game_class, lvl, player_id order by "\
                      "res_count desc;".format(stat, "and game_class = '{}'"
                                                     "".format(game_class) if game_class is not None else "")
    else:
        request = "select nickname, {}, game_class, lvl, id from players where castle = '🖤' and {} is not null " \
                  "and api_info -> 'token' is not null {}" \
                  "order by {} desc".format(stat, stat, "and game_class = '{}' ".format(game_class) if
                                            game_class is not None else "", stat)
        response += "<em>Обратите внимание, в топе отображаются только игроки, подключившие API (команда /auth).</em>" \
                    "\n\n"
    cursor.execute(request)
    row = cursor.fetchone()
    num = 0
    response_old = ""
    while row is not None:
        num += 1
        class_icon = classes_to_emoji.get(row[2]) or '❔'
        if row[4] == player.id:
            response_new = "<b>{}) {}</b><code>{:<3}</code><b> 🏅: {} {}{}</b> 🔻" \
                           "\n".format(num, stat_text, row[1] or "???", row[3], class_icon, row[0])
            found = True
            if num <= TOP_NUM_PLAYERS:
                response += response_new
                row = cursor.fetchone()
                continue
            response += "\n...\n" + response_old + response_new
        else:
            response_old = "<code>{}</code>) {}<code>{:<3}</code> 🏅: <code>{}</code> {}{}" \
                           "\n".format(num, stat_text, row[1] or "???", row[3], class_icon, row[0])
            if num <= TOP_NUM_PLAYERS:
                response += response_old
            else:
                if found:
                    if num == TOP_NUM_PLAYERS + 1:
                        break
                    response += response_old
                    break
        row = cursor.fetchone()
    return response


def top_stat(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    text_to_stats = {"⚔️Атака": "attack", "⚔️Attack": "attack", "🛡Защита": "defense", "🛡Defence": "defense",
                     "🔥Опыт": "exp", "🔥Experience": "exp", "🌲Дерево": "wood", "🌲Wood": "wood", "⛰Камень": "stone",
                     "⛰Stone": "stone", "🏚Стройка": "construction", "🏚Construction": "construction"}
    stat = text_to_stats.get(mes.text)
    response = get_tops_text(player, stat, mes.text[0])
    buttons = get_tops_buttons(stat)
    bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML', reply_markup=buttons)


def send_new_top(bot, update):
    stat_to_text = {"attack": "⚔️", "defense": "🛡", "exp": "🔥", "wood": "🌲", "stone": "⛰", "construction": "🏚"}
    mes = update.callback_query.message
    data = update.callback_query.data
    parse = re.search("top_([^_]+)_(.*)", data)
    if parse is None:
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                                text="Произошла ошибка. Попробуйте вызвать топы заного.")
        return
    stat = parse.group(1)
    class_emoji = parse.group(2)
    game_class = emoji_to_class.get(class_emoji)
    player = Player.get_player(update.callback_query.from_user.id)
    if player is None:
        return
    response = get_tops_text(player, stat, stat_to_text.get(stat), game_class=game_class)
    buttons = get_tops_buttons(stat, curr=class_emoji)
    """bot.send_message(chat_id=update.callback_query.message.chat_id, text=response, parse_mode='HTML',
                     reply_markup=buttons)"""
    try:
        bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=response,
                            reply_markup=buttons, parse_mode='HTML')
    # except Exception:
        # logging.error(traceback.format_exc())
    except BadRequest:
        pass
    except TelegramError:
        pass
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


def roulette_main(bot, update, user_data):
    user_data.update({"status": "roulette", "location_id": 10})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def request_roulette_bet(bot, update, user_data):
    mes = update.message
    user_data.update({"status": "awaiting_roulette_bet"})
    roulette = Location.get_location(10)
    placed = roulette.special_info["placed"].get(str(mes.from_user.id))
    if placed is None:
        placed = 0
    buttons = get_general_buttons(user_data)
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    bot.send_message(chat_id=update.message.from_user.id,
                     text="Введите количество 🔘жетонов для ставки:\nМинимальная ставка: 10🔘\n\n"
                          "Ваша ставка: <b>{}</b>🔘.\n"
                          "Доступно: <b>{}</b>🔘.\n\n<em>Обратите внимание, отменить ставку невозможно.</em>"
                          "".format(placed, player.reputation),
                     reply_markup=buttons, parse_mode='HTML')


def place_roulette_bet(bot, update, user_data):
    mes = update.message
    bet = re.search("(\\d+)", mes.text)
    if bet is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис. Пожалуйста, пришлите в ответ целое число "
                                                   "не меньше 10")
        return
    bet = int(bet.group(1))
    if bet < 10:
        bot.send_message(chat_id=mes.chat_id, text="Минимальная ставка: 10🔘.")
        return
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    if bet > player.reputation:
        bot.send_message(chat_id=mes.chat_id, text="У вас не хватает 🔘жетонов!")
        return
    player.reputation -= bet
    player.update()
    roulette = Location.get_location(10)
    if roulette.special_info.get("game_running"):
        bot.send_message(chat_id=mes.chat_id, text="Игра началась. Ставки закрыты!")
        return
    placed = roulette.special_info["placed"].get(str(mes.from_user.id))
    if placed is None:
        placed = 0
    placed += bet
    roulette.special_info["placed"].update({str(mes.from_user.id): placed})
    total_placed = roulette.special_info["total_placed"]
    if total_placed is None:
        total_placed = 0
    total_placed += bet
    roulette.special_info["total_placed"] = total_placed
    roulette.special_info["enter_text_format_values"] = [total_placed]  # Если изменится вид сообщения, поменять
    roulette.update_location_to_database()
    user_data.update({"status": "roulette"})
    buttons = get_general_buttons(user_data, player=player)
    bot.send_message(chat_id=mes.from_user.id, text="Ставка успешно сделана. Удачи на игре!", reply_markup=buttons)


def roulette_game(bot, job):
    # CENTRAL_SQUARE_CHAT_ID = -1001346136061  # тест
    response = "🎰РУЛЕТКА🎰\n\n"
    roulette = Location.get_location(10)
    total_placed = roulette.special_info["total_placed"] or 0
    print(total_placed, roulette.special_info["placed"])
    if total_placed == 0:
        bot.send_message(chat_id=CENTRAL_SQUARE_CHAT_ID, text=response + "Никто не сделал ставок. Игра не состоялась.")
        return
    players, position = {}, 1
    for player_id, placed in list(roulette.special_info["placed"].items()):
        players.update({int(player_id): range(position, position + placed)})
        position += placed
    response += "Игра начинается!"
    mes = bot.sync_send_message(chat_id=CENTRAL_SQUARE_CHAT_ID, text=response)
    intervals = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.01]
    progress = ["\\_", "|", "/_", "-"]
    i = 0
    r, player = None, None
    for interval in intervals:
        r = random.randint(1, position)
        for player_id, rng in list(players.items()):
            if r in rng:
                player = Player.get_player(player_id)
                response = "🎰РУЛЕТКА🎰\nРозыгрыш {}🔘\n\nБилет №{} (<b>{}</b>)\n\nИдёт игра {}" \
                           "".format(total_placed, r, player.nickname, progress[i])
                i += 1
                if i % 4 == 0:
                    i = 0
                break
        bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=response, parse_mode='HTML')
        time.sleep(interval)
    player.reputation += total_placed
    player.update()
    response = "🎰РУЛЕТКА🎰\n\nБилет №{} (<b>{}</b>)!\n\nПобедитель - @{}, и он забирает себе " \
               "<b>{}</b>🔘!\nПоздравляем!".format(r, player.nickname, player.username, total_placed)
    bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=response, parse_mode='HTML')

    roulette.special_info.update({"enter_text_format_values": [0], "placed": {}, "total_placed": 0})
    won = roulette.special_info.get("won")
    player_won = won.get(str(player.id)) or 0
    roulette.special_info["won"].update({str(player.id): player_won + total_placed})
    roulette.update_location_to_database()
    time.sleep(1)
    plan_roulette_games()


def plan_roulette_games():
    now = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
    roulette_time = now.replace(hour=9, minute=0, second=0)
    limit_time = now.replace(hour=21, minute=0, second=0)
    while roulette_time < now and roulette_time <= limit_time:
        roulette_time += datetime.timedelta(hours=0, minutes=30)
    if roulette_time > limit_time:
        roulette_time = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time(hour=9))
    tea_party = Location.get_location(9)
    if tea_party.is_constructed():
        job.run_once(roulette_game, when=roulette_time)
    # print(roulette_time)

    # job.run_once(roulette_game, 60)  # тест


def count_reputation_sum(bot, update):
    request = "select action, player_id from castle_logs"
    cursor.execute(request)
    rep = {}
    action_to_rep = {"collect_resources": 3, "construction": 5}
    row = cursor.fetchone()
    while row is not None:
        action, player_id = row
        cur_rep = rep.get(player_id) or 0
        cur_rep += action_to_rep.get(action)
        rep.update({player_id: cur_rep})
        row = cursor.fetchone()
    lst = list(rep.items())
    lst.sort(key=lambda x: Player.get_player(x[0]).reputation - x[1], reverse=True)
    response = "Статистика по жетонам:\n"
    for obj in lst:
        id, reputation = obj
        player = Player.get_player(id)
        new_response = "<code>{:<20}</code> 🔘: <code>{:4<}</code>, всего 🔘: <code>{:<4}</code>, <code>{}</code>\n" \
                       "".format(player.username, reputation, player.reputation, player.reputation - reputation)
        if len(response + new_response) > 4000:
            bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML')
            response = ""
        response += new_response
    bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML')


