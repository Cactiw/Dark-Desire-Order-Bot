"""
В этом модуле находятся функции для работы с экипировкой, в том числе и со стоком ги
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, TelegramError

from castle_files.libs.player import Player
from castle_files.libs.guild import Guild
from castle_files.libs.equipment import Equipment

from castle_files.bin.service_functions import pop_from_user_data_if_presented, build_inline_buttons_menu

import logging
import traceback
import re


TIERS = ['Т0', 'T1', 'T2', 'T3', 'T4', 'T5']
PLACES = ['main_hand', 'second_hand', 'head', 'gloves', 'armor', 'boots', 'cloaks']


def guild_equipment(bot, update, user_data):
    mes = update.callback_query.message
    data = update.callback_query.data
    pop_from_user_data_if_presented(user_data, ["guild_equipment_selected_place", "guild_equipment_selected_tier"])
    requested_player_id = update.callback_query.from_user.id
    guild_id = re.search("_(\\d+)", data)
    if guild_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка. Начните сначала.")
        return
    guild_id = int(guild_id.group(1))
    guild = Guild.get_guild(guild_id)
    bot.send_message(chat_id=mes.chat_id, text=get_guild_equipment_text(guild, None, None),
                     reply_markup=get_guild_equipment_buttons(guild, None, None), parse_mode='HTML')
    bot.answerCallbackQuery(update.callback_query.id)


def change_guild_equipment_param(bot, update, user_data):
    mes = update.callback_query.message
    data = update.callback_query.data
    parse = re.search("guild_equipment_(\\w+)_(\\d+)_(\\d+)", data)
    if parse is None:
        bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка. Начните сначала.")
        return
    param, guild_id, value = parse.group(1), int(parse.group(2)), int(parse.group(3))
    guild = Guild.get_guild(guild_id)
    if guild is None:
        bot.send_message(chat_id=mes.chat_id, text="Гильдия не найдена. Начните сначала.")
        return
    param_string = "guild_equipment_selected_{}".format(param)
    cur_value = user_data.get(param_string)
    if value == cur_value:
        pop_from_user_data_if_presented(user_data, param_string)
    else:
        user_data.update({param_string: value})
    place, tier = user_data.get("guild_equipment_selected_place"), user_data.get("guild_equipment_selected_tier")
    try:
        bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id,
                            text=get_guild_equipment_text(guild, place, tier),
                            reply_markup=get_guild_equipment_buttons(guild, place, tier), parse_mode='HTML')
    # except Exception:
        # logging.error(traceback.format_exc())
    except BadRequest:
        logging.error(traceback.format_exc())
    except TelegramError:
        pass
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)


def get_guild_equipment_buttons(guild, selected_place, selected_tier) -> [[InlineKeyboardButton]]:
    buttons = build_inline_buttons_menu(PLACES, "guild_equipment_place_{}_".format(guild.id), 3,
                                        None if selected_place is None else lambda data, num: num == selected_place)
    buttons += build_inline_buttons_menu(TIERS, "guild_equipment_tier_{}_".format(guild.id), 3,
                                         None if selected_tier is None else lambda data, num: num == selected_tier)
    return InlineKeyboardMarkup(buttons)


def get_guild_equipment_text(guild: Guild, selected_place: int, selected_tier: int) -> str:
    if selected_place is None and selected_tier is None:
        return "Выберите тир и слот экипировки."
    res = "🏷Гильдейская экипировка:\n"
    equipment: [Equipment] = guild.get_equipment()
    place = PLACES[selected_place] if selected_place is not None else None
    tier = int(TIERS[selected_tier][1:]) if selected_tier is not None else None
    for eq in equipment:
        if (place is None or place == eq.place) and (tier is None or tier == eq.tier):
            res += eq.format(mode="guild")
    return res

