"""
Здесь функции покупки наград, которые можно купить за жетоны
"""

from castle_files.libs.player import Player
from castle_files.libs.guild import Guild
from castle_files.libs.castle.location import Location

from castle_files.bin.mid import do_mailing
from castle_files.bin.trigger import global_triggers_in, get_message_type_and_data, fill_triggers_ignore, \
    check_global_triggers_ignore
from castle_files.bin.service_functions import check_access, get_time_remaining_to_battle, get_current_datetime

from castle_files.work_materials.globals import STATUSES_MODERATION_CHAT_ID, dispatcher, moscow_tz, cursor, job, \
    MID_CHAT_ID, CENTRAL_SQUARE_CHAT_ID, HOME_CASTLE

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, TelegramError

import logging
import traceback
import datetime
import re
import time
import json


REWARD_PRICE_RESET_WEEKS = 2
REWARD_PRICE_COEFF = 0.3


class RewardRollbackException(BaseException):
    pass


def reward_edit_castle_message(player, reward, *args, **kwargs):
    central_square = Location.get_location(0)
    format_values = central_square.special_info.get("enter_text_format_values")
    format_values[0] = reward
    central_square.update_location_to_database()
    pass


def reward_mailing(player, reward, *args, **kwargs):
    do_mailing(dispatcher.bot, reward)


def reward_global_trigger(player, reward, message, cost, *args, **kwargs):
    reward = reward.lower()
    if reward in global_triggers_in:
        dispatcher.bot.send_message(player.id, text="Такой глобальный триггер уже существует. Жетоны возвращены.")
        player.reputation += cost
        player.update()
        raise RewardRollbackException
    trigger_type, data = get_message_type_and_data(message.reply_to_message)
    request = "insert into triggers(text_in, type, data_out, chat_id, creator, date_created) VALUES (%s, %s, %s, %s, " \
              "%s, %s)"
    cursor.execute(request, (reward, trigger_type, data, 0, player.nickname,
                             datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)))
    global_triggers_in.append(reward.lower())
    dispatcher.bot.send_message(player.id, text="Глобальный триггер успешно создан!")
    pass


def reward_remove_global_trigger(player, reward, cost, *args, **kwargs):
    reward = reward.lower()
    if reward not in global_triggers_in:
        dispatcher.bot.send_message(player.id, text="Глобальный триггер не найден. Жетоны возвращены.")
        player.reputation += cost
        player.update()
        raise RewardRollbackException
    request = "delete from triggers where chat_id = 0 and text_in = %s"
    cursor.execute(request, (reward,))
    global_triggers_in.remove(reward)
    dispatcher.bot.send_message(player.id, text="Глобальный триггер успешно удалён!")
    pass


def reward_g_def(player, reward, cost, *args, **kwargs):
    guild = Guild.get_guild(player.guild)
    if guild is None or guild.castle != HOME_CASTLE:
        if guild is None:
            text = "Гильдия не найдена. Вы должны состоять в гильдии.\nЖетоны возвращены."
        else:
            text = "Функция доступна только для гильдий из Скалы.\nЖетоны возвращены."
        dispatcher.bot.send_message(player.id, text=text)
        player.reputation += cost
        player.update()
        raise RewardRollbackException
    do_mailing(dispatcher.bot, "📣📣📣Вы слышите звуки рога! Это {} зазывает сынов и дочерей Скалы на защиту!\n"
                               "/g_def {}".format(guild.tag, guild.tag))
    dispatcher.bot.send_message(chat_id=STATUSES_MODERATION_CHAT_ID,
                                text="Не забудьте снять жетоны тем, "
                                     "кого не будет в дефе <b>{}</b> в ближайшую битву!".format(guild.tag),
                                parse_mode='HTML')
    job.run_once(when=get_time_remaining_to_battle() + datetime.timedelta(minutes=5),
                 callback=g_def_remind_after_battle, context={"tag": guild.tag})


def g_def_remind_after_battle(bot, job):
    bot.send_message(chat_id=MID_CHAT_ID,
                     text="Не забудьте снять жетоны тем, "
                          "кто не был в дефе <b>{}</b> в прошедшую битву!".format(job.context.get("tag")),
                     parse_mode='HTML')


def reward_request_pin(player, reward, cost, *args, **kwargs):
    pass


def reward_change_castle_chat_picture(player, reward, *args, **kwargs):
    pass


def reward_disable_global_triggers(player, reward, cost, *args, **kwargs):
    try:
        reward = int(reward)
    except ValueError:
        dispatcher.bot.send_message(player.id, text="Неверный синтаксис. Введите корректное id чата "
                                                    "(не удаляя минус, если он присутствовал!)")
        player.reputation += cost
        player.update()
        raise RewardRollbackException
    if check_global_triggers_ignore(int(reward)):
        dispatcher.bot.send_message(player.id, text="В чате уже активна награда. Жетоны возвращены.")
        player.reputation += cost
        player.update()
        raise RewardRollbackException


def ignore_triggers_updated(player, reward_name, cost, reward_text, *args, **kwargs):
    fill_triggers_ignore()
    to_text = {
        "hour": "час",
        "day": "сутки",
        "weeks": "2 недели"
    }
    period_text = to_text.get(re.search("(hour|day|weeks)", reward_name).group(1), reward_name)
    dispatcher.bot.send_message(chat_id=reward_text, text="<b>{}</b> купил отключение глобальных триггеров на "
                                                          "{}".format(player.nickname, period_text),
                                parse_mode='HTML')


MUTED_MINUTES = 30
FORBID_MUTED_MINUTES = 30
muted_players = {}


def reward_read_only(player, reward, cost, *args, **kwargs):
    mute_player = Player.get_player(reward)
    if mute_player is None:
        player.reputation += cost
        player.update()
        dispatcher.bot.send_message(player.id, text="Игрок не найден. Жетоны возвращены.")
        return
    if check_access(mute_player.id):
        # Хотят забанить чела из мида
        muted_players.update({mute_player.id: time.time() + FORBID_MUTED_MINUTES * 60})
        dispatcher.bot.send_message(chat_id=mute_player.id,
                                    text="Ты протягиваешь кошель с жетонами стражнику, шепча на ухо имя бедолаги.\n"
                                         "-\"ШО, ПРЯМ СОВЕТНИКА КОРОЛЯ, ЗА ТАКИЕ-ТО ДЕНЬГИ?!\"\n"
                                         "Стражники скручивают тебя и кидают в темницу. Пять минуток "
                                         "посидишь - поумнеешь.")
    else:
        muted_players.update({mute_player.id: time.time() + MUTED_MINUTES * 60})
        dispatcher.bot.send_message(chat_id=mute_player.id,
                                    text="\"Стражу подкупили!\" - кричишь ты, пока тебя утаскивают в одиночку "
                                         "на ближайшие полчаса.\nОтличное время подумать, где и когда ты умудрился "
                                         "нажить себе врагов, что аж жетонов не пожалели, чтобы тебе насолить.\n"
                                         "<em>30 минут вы не можете ничего писать в чатах с ботом.</em>",
                                    parse_mode='HTML')


def delete_message(bot, update):
    try:
        bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
    except TelegramError:
        pass


rewards = {"castle_message_change": {
    "price": 2500, "moderation": True, "text": "Введите новое замковое сообщение:", "get": reward_edit_castle_message
    },
    "castle_mailing": {
        "price": 10000, "moderation": True, "text": "Введите текст рассылки по замку:", "get": reward_mailing
    },
    "castle_g_def": {
        "price": 5000, "moderation": False,
        "text": "Всем гильдиям замка будет отправлен запрос о защите вашей гильдии.",
        "get": reward_g_def, "skip_enter_text": True
    },
    "castle_request_pin": {
        "price": 5000, "moderation": True, "text": "Вы получите пин на следующую битву заранее.",
        "get": reward_request_pin, "skip_enter_text": True
    },
    "castle_global_trigger": {
        "price": 2500, "moderation": True, "text": "Введите текст, который будет вызывать новый глобальный триггер:",
        "next": "Отправьте сообщение с триггером.", "get": reward_global_trigger
    },
    "castle_delete_global_trigger": {
        "price": 2500, "moderation": False, "text": "Введите текст глобального триггера для удаления:",
        "get": reward_remove_global_trigger
    },
    "castle_disable_global_triggers_hour": {
        "price": 30, "moderation": False,
        "text": "Введите chat_id чата, в котором отключить триггеры:\n"
                "(/chat_info в нужном чате)\n"
                "Обратите внимание, id чата - длинное число, часто отрицательное, в этом случае его нужно прислать "
                "<b>вместе с минусом!</b>",
        "get": reward_disable_global_triggers, "after_reward_received": ignore_triggers_updated
    },
    "castle_disable_global_triggers_day": {
        "price": 600, "moderation": False,
        "text": "Введите chat_id чата, в котором отключить триггеры:\n"
                "(/chat_info в нужном чате)\n"
                "Обратите внимание, id чата - длинное число, часто отрицательное, в этом случае его нужно прислать "
                "<b>вместе с минусом!</b>",
        "get": reward_disable_global_triggers, "after_reward_received": ignore_triggers_updated
    },
    "castle_disable_global_triggers_weeks": {
        "price": 6000, "moderation": False,
        "text": "Введите chat_id чата, в котором отключить триггеры:\n"
                "(/chat_info в нужном чате)\n"
                "Обратите внимание, id чата - длинное число, часто отрицательное, в этом случае его нужно прислать "
                "<b>вместе с минусом!</b>",
        "get": reward_disable_global_triggers, "after_reward_received": ignore_triggers_updated
    },
    "castle_change_chat_picture": {
        "price": 2500, "moderation": True, "text": "Введите название чата (в произвольной форме):",
        "next": "Отправьте новую аватарку.", "get": reward_change_castle_chat_picture
    },
    "castle_ro": {
        "price": 5000, "moderation": False, "text": "Введите id человека, которому дать read only:",
        "get": reward_read_only
    },
}


def _empty(*args, **kwargs):
    pass


def receive_reward(player, reward_name, reward, reward_text, cost, *args, **kwargs):
    try:
        reward["get"](player=player, reward=reward_text, cost=cost, reward_name=reward_name, *args, **kwargs)
    except RewardRollbackException:
        pass
    else:
        create_reward_log(player, reward_name, cost, reward_text, *args, **kwargs)
        dispatcher.bot.send_message(
            chat_id=CENTRAL_SQUARE_CHAT_ID,
            text="<b>{}</b> получает награду <b>{}</b>.\nЦена на следующие 2 недели увеличена.\n"
                 "Эту награду в последние 2 недели получали <b>{}</b> раз.".format(
                    player.nickname, reward_name, get_reward_combo(reward_name)),
            parse_mode='HTML')
        reward.get("after_reward_received", _empty)(player, reward_name, cost, reward_text, *args, **kwargs)


period_hours = {
    "hour": 1,
    "day": 24,
    "weeks": 24 * 14
}


def create_reward_log(player, reward_name, cost, reward_text, *args, **kwargs):
    additional_info = {"cost": cost}
    if "disable_global_triggers" in reward_name:
        period = re.search("(hour|day|weeks)", reward_name).group(1)
        period = period_hours.get(period)
        additional_info.update({"chat_id": reward_text, "period": period})
    request = "insert into castle_logs(player_id, action, result, date, additional_info) values (%s, %s, %s, %s, %s)"
    cursor.execute(request, (player.id, "reward_{}".format(reward_name), 1, get_current_datetime(),
                             json.dumps(additional_info, ensure_ascii=False)))
    

def smuggler(bot, update):
    mes = update.message
    bot.send_message(chat_id=mes.chat_id,
                     text="В дальнем темном углу вы видете мужчину. Своеобразная эмблема Черного Рынка выдает в нем "
                          "связного с криминальными слоями Замка.\n"
                          "- \"Ну ты баклань, если че по делу есть, или вали отсюда на, пока маслину не словил. "
                          "На зырь, только быра-быра, кабанчиком.\"\n\n"
                          "1) \"Услуги Шменкси\"- инвестиция в нелегальную уличную живопись.\n<em>Возможность делать "
                          "объявление как обращение короля.\n(Будет модерация).</em>\n<b>{}</b>\n"
                          "/castle_message_change\n\n"
                          "2) \"Королевская голубятня\"- подкупить стражу у королевской голубятни.\n"
                          "<em>Возможность сделать рассылку раз в день.\n(Будет модерация).</em>\n<b>{}</b>\n"
                          "/castle_mailing\n\n"
                          "3) Рог Хельма Молоторукого - уникальный артефакт прошлого, дающий поистине необузданную "
                          "ярость защитникам родной крепости. Огромная мощь - это огромная ответственность!\n"
                          "<em>Запрос на массовый деф гильдии.</em>\n<b>{}</b>\n/castle_g_def\n\n"
                          "4) Орден Храма Лотоса - мощный артефакт с черного рынка древностей. "
                          "Обладатель ордена имеет поистине катастрофический прирост доверия Короля и его советников.\n"
                          "<b>Но помни, при малейшем намеке на предательство этого доверия в прошлом или настоящем - "
                          "кара будет суровой.</b>\n<em>Возможность получить пин заранее.</em>\n<b>{}</b>\n"
                          "/castle_request_pin\n\n"
                          "5) Операция \"Козел в огороде\" - найм банды отпетых отморозков и негодяев для "
                          "бессмысленного ограбления со взломом.\nПускай ограбление Королевской типографии не назвать"
                          "\"ограблением века\", но его точно запомнят по твоему личному глобальному триггеру!\n"
                          "<em>Личный глобальный тригер.\n(Будет модерация).</em>\n<b>{}</b>\n"
                          "/castle_global_trigger\n\n"
                          "6) Спецоперация \"Прачка в прачечной\". Лучшие спецы розыска займутся подчищением следов"
                          "почти \"ограбления века\".\nКто-то насрал в глобальные триггеры? Почистим!\n"
                          "<em>Возможность удалить глобальный тригер.</em>\n<b>{}</b>\n"
                          "/castle_delete_global_trigger\n\n"
                          "7) \"Волшебный туман\". Лучшие маги королевства призовут легендарный туман, который сокроет "
                          "выбранный чат от остальных. На некоторое время только внутренние правила остаются в силе.\n"
                          "<em>Временное отключение всех глобальных триггеров в выбранном чате.\n"
                          "Время не стакается.</em>\n<b>{} | {} | {}</b>\nЧас | Сутки | 2 недели\n"
                          "/dgt_hour /dgt_day /dgt_weeks\n\n"
                          "8) Порошок забвения.\nФея Виньета Камнемох любезно оставила на тумбочке свое самое "
                          "действенное средство. Забыл ее светящиеся крылья ты не сможешь никогда, а вот сменить"
                          " знамена на флагштоках на глазах у всех - вполне.\n"
                          "<em>Выбор аватарки любого чата замка, кроме общего.\n(Будет модерация).</em>\n"
                          "<b>{}</b>\n/castle_change_chat_picture\n\n"
                          "9) Доверительное письмо начальника Сыскной Службы Короны.\n"
                          "Корупированные чиновкники - бич любого государства. Но это и большие возможности. "
                          "Прикажите местной страже арестовать беднягу, ведь с этой грамотой у вас "
                          "неограниченные полномочия!\n"
                          "<em>Возможность впаять ридонли на 30 минут любому.</em>\n<b>{}</b>\n"
                          "/castle_ro\n\n".format(*list(map(lambda r: format_reward_price(r), list(rewards)))),
                     parse_mode='HTML')


def clear_reward_user_data(user_data):
    pop_list = ["reward_moderation", "reward_moderation_id", "reward", "reward_text", "reward_additional_id"]
    for pop_text in pop_list:
        if pop_text in user_data:
            user_data.pop(pop_text)


def request_reward_confirmation(bot, mes, reward, user_data):
    buttons = InlineKeyboardMarkup([[
        InlineKeyboardButton(text="✅Да", callback_data="p_reward yes"),
        InlineKeyboardButton(text="❌Нет", callback_data="p_reward no")]])
    bot.send_message(chat_id=mes.chat_id, text="Подтвердите:\n{}\n<em>{}</em>".format(reward["text"],
                                                                                      user_data["reward_text"]),
                     parse_mode='HTML', reply_markup=buttons)


def get_reward_price(reward_name: str, reward_combo: int = None) -> int:
    reward = rewards.get(reward_name)
    if reward_combo is None:
        reward_combo = get_reward_combo(reward_name)
    return int(reward["price"] * (reward_combo * REWARD_PRICE_COEFF + 1))


def get_reward_combo(reward_name: str) -> int:
    reward = rewards.get(reward_name)
    request = "select count(*) from castle_logs where action = %s and date > %s"
    cursor.execute(request, ("reward_{}".format(reward_name),
                             get_current_datetime() - datetime.timedelta(weeks=REWARD_PRICE_RESET_WEEKS)))
    count, *skip = cursor.fetchone()
    return count


def format_reward_price(reward_name: str) -> str:
    reward = rewards.get(reward_name)
    combo = get_reward_combo(reward_name)
    return "{}🔘 {}".format(
        get_reward_price(reward_name, combo),
        "( {}🔘 * (1 + {} * {}) )".format(reward["price"], combo, REWARD_PRICE_COEFF) if combo > 0 and False else ""
    )


def request_get_reward(bot, update, user_data):
    mes = update.message
    reward_name = mes.text[1:].replace("dgt_", "castle_disable_global_triggers_")
    reward = rewards.get(reward_name)
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    if reward is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return
    if player.reputation < get_reward_price(reward_name):
        bot.send_message(chat_id=mes.chat_id, text="Недостаточно 🔘 жетонов")
        return
    if reward.get("skip_enter_text"):
        # Ничего вводть не надо, сразу на подтверждение кидаю
        user_data.update({"status": "tea_party", "reward": reward_name, "reward_text": reward.get("text")})
        request_reward_confirmation(bot, mes, reward, user_data)
    else:
        # Запрос ввода текста для награды
        user_data.update({"status": "requested_reward", "reward": reward_name})
        bot.send_message(chat_id=mes.chat_id, text=reward["text"])


def get_reward(bot, update, user_data):
    mes = update.message
    reward_text = mes.text
    reward = rewards.get(user_data.get("reward"))
    if reward is None:
        bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка. Попробуйте начать сначала.")
        return
    next_text = reward.get("next")

    # Уже указана дополнительная информация
    if 'additional' in user_data.get("status"):
        user_data.update({"status": "tea_party", "reward_additional_id": mes.message_id})
    elif next_text:
        user_data.update({"status": "requested_additional_reward", "reward_text": reward_text})
        bot.send_message(chat_id=mes.chat_id, text=next_text)
        return
    else:
        user_data.update({"status": "tea_party", "reward_text": reward_text})
    request_reward_confirmation(bot, mes, reward, user_data)


def answer_reward(bot, update, user_data):
    mes = update.callback_query.message
    player = Player.get_player(update.callback_query.from_user.id)
    if "yes" in update.callback_query.data:
        reward_name = user_data.get("reward")
        reward = rewards.get(reward_name)
        if reward is None:
            bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                                    text="Произошла ошибка. Попробуйте начать сначала.", show_alert=True)
            return
        if player.reputation < get_reward_price(reward_name):
            bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                                    text="Недостаточно 🔘 жетонов", show_alert=True)
            return
        player.reputation -= get_reward_price(reward_name)
        player.update()
        if reward.get("moderation"):
            if user_data.get("reward_moderation") is not None:
                bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                                        text="Одна из наград уже проходит модерацию. Пожалуйста, подождите окончания",
                                        show_alert=True)
                player.reputation += get_reward_price(reward_name)
                player.update()
                return
            add_mes_id = None
            mes_to_forward_id = user_data.get("reward_additional_id")
            if mes_to_forward_id:
                # К награде предоставляется дополнительная информация
                add_mes = bot.forwardMessage(chat_id=STATUSES_MODERATION_CHAT_ID, from_chat_id=player.id,
                                             message_id=mes_to_forward_id)
                add_mes_id = add_mes.message_id
            bot.send_message(chat_id=STATUSES_MODERATION_CHAT_ID, parse_mode='HTML',
                             text="<b>{}</b>(@{}) Хочет получить награду <b>{}</b>.\n<em>{}</em>\n"
                                  "Разрешить?".format(player.nickname, player.username, user_data["reward"],
                                                      user_data["reward_text"]),
                             reply_to_message_id=add_mes_id,
                             reply_markup=InlineKeyboardMarkup([[
                                 InlineKeyboardButton(text="✅Да",
                                                      callback_data="p_moderate_reward_{} yes".format(player.id)),
                                 InlineKeyboardButton(text="❌Нет",
                                                      callback_data="p_moderate_reward_{} no".format(player.id))]]))
            text = "Отправлено на модерацию"
            user_data.update({"reward_moderation": True})
        else:
            text = "Награда получается"
            try:
                receive_reward(player=player, reward_name=reward_name, reward=reward,
                               reward_text=user_data.get("reward_text"), cost=get_reward_price(reward_name))
            except Exception:
                logging.error(traceback.format_exc())
            clear_reward_user_data(user_data)
    else:
        text = "Получение награды отменено."
        clear_reward_user_data(user_data)
    try:
        bot.answerCallbackQuery(update.callback_query.id)
        bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=text)
    except BadRequest:
        bot.send_message(chat_id=mes.chat_id, text=text)


def moderate_reward(bot, update):
    mes = update.callback_query.message
    player_id = re.search("_(\\d+)", update.callback_query.data)
    if player_id is None:
        bot.answer_callback_query(callback_query_id=update.callback_query.id,
                                  text="Ошибка. Неверные данные в ответе",
                                  show_alert=True)
        return
    player_id = int(player_id.group(1))
    user_data = dispatcher.user_data.get(player_id)
    player = Player.get_player(player_id)
    if player is None:
        return
    yes = 'yes' in update.callback_query.data
    reward = user_data.get("reward")
    if reward is None:
        bot.answer_callback_query(callback_query_id=update.callback_query.id,
                                  text="Странная ошибка.",
                                  show_alert=True)
        return
    reward_name = reward
    reward = rewards.get(reward)
    answer_text = "{} @<b>{}</b> в <code>{}</code>" \
                  "".format("Одобрено" if yes else "Отклонено", update.callback_query.from_user.username,
                            datetime.datetime.now(tz=moscow_tz).strftime("%d/%m/%y %H:%M:%S"))
    try:
        bot.answerCallbackQuery(update.callback_query.id)
        bot.edit_message_text(chat_id=mes.chat_id, message_id=mes.message_id, text=mes.text + "\n" + answer_text,
                              parse_mode='HTML')
    except BadRequest:
        bot.send_message(chat_id=mes.chat_id, text=mes.text + "\n" + answer_text)

    if yes:
        try:
            receive_reward(player=player, reward_name=reward_name, reward=reward, message=mes,
                           reward_text=user_data.get("reward_text"), cost=get_reward_price(reward_name))
        except Exception:
            logging.error(traceback.format_exc())
        bot.send_message(chat_id=player.id, text="Награда выдана.")
    else:
        player.reputation += get_reward_price(reward_name)
        player.update()
        bot.send_message(chat_id=player.id, text="Награда не прошла модерацию.\n🔘Жетоны возвращены.")
    clear_reward_user_data(user_data)

