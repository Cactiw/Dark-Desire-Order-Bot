"""
Здесь функции покупки наград, которые можно купить за жетоны
"""

from castle_files.libs.player import Player
from castle_files.libs.castle.location import Location

from castle_files.bin.mid import do_mailing

from castle_files.work_materials.globals import STATUSES_MODERATION_CHAT_ID, dispatcher, moscow_tz

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

import logging
import traceback
import datetime
import re


def reward_edit_castle_message(player, reward):
    central_square = Location.get_location(0)
    format_values = central_square.special_info.get("enter_text_format_values")
    format_values[0] = reward
    central_square.update_location_to_database()
    pass


def reward_mailing(player, reward):
    do_mailing(dispatcher.bot, reward)


def reward_global_trigger(player, reward):
    pass


def reward_remove_global_trigger(player, reward):
    pass


rewards = {"castle_message_change": {
    "price": 5000, "moderation": True, "text": "Введите новое замковое сообщение:", "get": reward_edit_castle_message
    },
    "castle_mailing": {
        "price": 10000, "moderation": True, "text": "Введите текст рассылки по замку", "get": reward_mailing
    },
    "global_trigger": {
        "price": 5000, "moderation": True, "text": "Введите текст глобального триггера", "get": reward_global_trigger
    }
}


def smuggler(bot, update):
    mes = update.message
    bot.send_message(chat_id=mes.chat_id,
                     text="Вы подходите к контробандисту. *Место для охуенного описания от Джеди.*\n\n"
                          "1)\"Услуги Шменкси\"- инвестиция в нелегальную уличную живопись.\n<em>Возможность делать " \
                          "объявление как обращение короля. Нужна модерация.</em>\n/castle_message_change\n\n"
                          "2)\"Королевская голубятня\"- подкупить стражу у королевской голубятни.\n"
                          "<em>Возможность сделать рассылку раз в день. Нужна модерация.</em>\n/castle_mailing\n\n",
                     parse_mode='HTML')


def request_get_reward(bot, update, user_data):
    mes = update.message
    reward = rewards.get(mes.text[1:])
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    if reward is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис.")
        return
    if player.reputation < reward["price"]:
        bot.send_message(chat_id=mes.chat_id, text="Недостаточно 🔘 жетонов")
        return
    user_data.update({"status": "requested_reward", "reward": mes.text[1:]})
    bot.send_message(chat_id=mes.chat_id, text=reward["text"])


def get_reward(bot, update, user_data):
    mes = update.message
    reward_text = mes.text
    reward = rewards.get(user_data.get("reward"))
    if reward is None:
        bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка. Попробуйте начать сначала.")
        return
    user_data.update({"status": "tea_party", "reward_text": reward_text})
    buttons = InlineKeyboardMarkup([[
        InlineKeyboardButton(text="✅Да", callback_data="p_reward yes"),
        InlineKeyboardButton(text="❌Нет", callback_data="p_reward no")]])
    bot.send_message(chat_id=mes.chat_id, text="Подтвердите:\n{}\n<em>{}</em>".format(reward["text"], reward_text),
                     parse_mode='HTML', reply_markup=buttons)


def answer_reward(bot, update, user_data):
    mes = update.callback_query.message
    player = Player.get_player(update.callback_query.from_user.id)
    if "yes" in update.callback_query.data:
        reward = rewards.get(user_data.get("reward"))
        if reward is None:
            bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                                    text="Произошла ошибка. Попробуйте начать сначала.", show_alert=True)
            return
        if player.reputation < reward["price"]:
            bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                                    text="Недостаточно 🔘 жетонов", show_alert=True)
            return
        player.reputation -= reward["price"]
        player.update()
        if reward.get("moderation"):
            if user_data.get("reward_moderation") is not None:
                bot.answerCallbackQuery(callback_query_id=update.callback_query.id,
                                        text="Одна из наград уже проходит модерацию. Пожалуйста, подождите окончания",
                                        show_alert=True)
                return
            bot.send_message(chat_id=STATUSES_MODERATION_CHAT_ID, parse_mode='HTML',
                             text="<b>{}</b>(@{}) Хочет получить награду <b>{}</b>.\n<em>{}</em>\n"
                                  "Разрешить?".format(player.nickname, player.username, user_data["reward"],
                                                      user_data["reward_text"]),
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
                reward["get"](player=player, reward=reward)
            except Exception:
                logging.error(traceback.format_exc())
    else:
        text = "Получение награды отменено."
        user_data.pop("reward")
        user_data.pop("reward_text")
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
            reward["get"](player=player, reward=user_data["reward_text"])
        except Exception:
            logging.error(traceback.format_exc())
        bot.send_message(chat_id=player.id, text="Награда выдана.")
    else:
        player.reputation += reward["price"]
        player.update()
        bot.send_message(chat_id=player.id, text="Награда не прошла модерацию.\n🔘Жетоны возвращены.")
    user_data.pop("reward_moderation")
