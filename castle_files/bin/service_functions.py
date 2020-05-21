from castle_files.work_materials.globals import SUPER_ADMIN_ID, high_access_list, allowed_list, cursor, moscow_tz, \
    local_tz, job, utc, dispatcher
from mwt import MWT

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import datetime
import re


def cancel(bot, update, user_data):
    if "status" in user_data:
        user_data.pop("status")
    if "edit_guild_id" in user_data:
        user_data.pop("edit_guild_id")
    bot.send_message(chat_id=update.message.chat_id, text="Операция отменена.")
    return


def pop_from_user_data_if_presented(user_data, key):
    if isinstance(key, list):
        for k in key:
            try:
                user_data.pop(k)
            except KeyError:
                pass
    else:
        try:
            user_data.pop(key)
        except KeyError:
            pass


def pop_from_user_data(bot, update):
    mes = update.message
    if mes.from_user.id != SUPER_ADMIN_ID:
        return
    parse = re.search("/pop_from_user_data (\\d+) (.+)", mes.text)
    if parse is None:
        bot.send_message(chat_id=update.message.chat_id, text="Неверный синтаксис.")
        return
    user_id, pop_value = int(parse.group(1)), parse.group(2)
    user_data = dispatcher.user_data.get(user_id)
    if user_data is None or pop_value not in user_data:
        bot.send_message(chat_id=update.message.chat_id, text="Не найдено")
        return
    user_data.pop(pop_value)
    bot.send_message(chat_id=mes.chat_id, text="Успешно")


def increase_or_add_value_to_dict(d: dict, key, value) -> dict:
    if value <= 0:
        return d
    d.update({key: d.get(key, 0) + value})
    return d


def decrease_or_pop_value_from_dict(d: dict, key, value) -> dict:
    new_value = d.get(key, 0) - value
    if new_value <= 0:
        pop_from_user_data_if_presented(d, key)
    else:
        d.update({key: new_value})
    return d


def merge_int_dictionaries(d1: dict, d2: dict) -> dict:
    """
    Function that add to first dictionary values of the second (d1[value] = d1[value] + d2[value]) IN-PLACE!
    :param d1:
    :param d2:
    :return:
    """
    for k, v in list(d2.items()):
        d1.update({k: d1.get(k, 0) + v})
    return d1


# Функция, планирующая работу на конкретное время сегодня, или завтра, если это время сегодня уже прошло
def plan_work(callback, hour, minute, second, context={}):
    time_to_send = datetime.time(hour=hour, minute=minute, second=second)
    time_now = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None).time()
    day_to_send = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None).date()
    date_to_send = datetime.datetime.combine(day_to_send, datetime.time(hour=0))
    if time_to_send < time_now:
        date_to_send += datetime.timedelta(days=1)
    date_to_send = date_to_send.date()
    send_time = datetime.datetime.combine(date_to_send, time_to_send)  # Время в мск
    send_time = moscow_tz.localize(send_time).astimezone(tz=local_tz).replace(tzinfo=None)  # Локальное время
    job.run_once(callback, when=send_time, context=context)


def great_format_time(dt: datetime.datetime) -> str:
    return dt.strftime("%d/%m/%y %H:%M:%S")


def get_message_forward_time(message):
    try:
        forward_message_date = utc.localize(message.forward_date).astimezone(tz=moscow_tz).replace(tzinfo=None)
    except ValueError:
        try:
            forward_message_date = message.forward_date
        except AttributeError:
            forward_message_date = local_tz.localize(message.date).astimezone(tz=moscow_tz).replace(tzinfo=None)
    return forward_message_date


def check_access(user_id):
    return user_id == SUPER_ADMIN_ID or user_id in high_access_list


def fill_allowed_list():
    request = "select id from players"
    cursor.execute(request)
    row = cursor.fetchone()
    allowed_list.clear()
    while row is not None:
        allowed_list.append(row[0])
        row = cursor.fetchone()


def get_forward_message_time(mes):
    return utc.localize(mes.forward_date).astimezone(tz=moscow_tz).replace(tzinfo=None)


def get_message_and_player_id(update):
    message = update.message if update.message is not None else update.callback_query.message
    player_id = update.message.from_user.id if update.message is not None else update.callback_query.from_user.id
    return message, player_id


def get_time_remaining_to_battle():
    now = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None) - datetime.datetime.combine(
        datetime.datetime.now().date(), datetime.time(hour=0))
    if now < datetime.timedelta(hours=1):

        return datetime.timedelta(hours=1) - now
    time_from_first_battle = now - datetime.timedelta(hours=1)
    while time_from_first_battle > datetime.timedelta(hours=8):
        time_from_first_battle -= datetime.timedelta(hours=8)
    time_remaining = datetime.timedelta(hours=8) - time_from_first_battle
    return time_remaining


def count_week_by_battle_id(battle_id):
    week = 0
    battle_id -= 1
    while battle_id > 0:
        week += 1
        battle_id -= 21
    return week


def count_battles_in_this_week():
    battle_id = count_battle_id(None)
    battle_id -= 1
    while battle_id > 0:
        battle_id -= 21
    return 21 + battle_id


# Функция, которая считает id битвы по сообщению, крайне желательно переписать нормально, похоже на костыль
# Если message = None, то считает battle_id последней ПРОШЕДШЕЙ битвы.
def count_battle_id(message=None):
    first_battle = datetime.datetime(2018, 5, 27, 9, 0, 0, 0)
    interval = datetime.timedelta(hours=8)
    if message is None:
        forward_message_date = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
    else:
        if message.forward_date is not None:
            try:
                forward_message_date = utc.localize(message.forward_date).astimezone(tz=moscow_tz).replace(tzinfo=None)
            except ValueError:
                forward_message_date = message.forward_date
        else:
            forward_message_date = utc.localize(message.date).astimezone(tz=moscow_tz).replace(tzinfo=None)
    time_from_first_battle = forward_message_date - first_battle
    battle_id = 0
    while time_from_first_battle > interval:
        time_from_first_battle -= interval
        battle_id = battle_id + 1
    return battle_id


def dict_invert(d):
    return dict(zip(d.values(), d.keys()))


def build_inline_buttons_menu(texts: [str], callback_data_prefix: str, n_cols: int, enabled_func=None,
                              skip_first: int = None):
    cur_list = []
    buttons = [cur_list]
    for i, text in enumerate(texts):
        if skip_first is not None and i < skip_first:
            continue
        if len(cur_list) == n_cols:
            cur_list = []
            buttons.append(cur_list)
        cur_list.append(InlineKeyboardButton("{}{}".format(
            "✅" if enabled_func is not None and enabled_func(text, i) else "", text),
            callback_data="{}{}".format(callback_data_prefix, i)))
    return buttons


@MWT(timeout=15*60)
def get_admin_ids(bot, chat_id):
    """Returns a list of admin IDs for a given chat. Results are cached for 15 minutes."""
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]
