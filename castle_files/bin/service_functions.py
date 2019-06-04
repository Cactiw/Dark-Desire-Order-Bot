from castle_files.work_materials.globals import SUPER_ADMIN_ID, high_access_list, allowed_list, cursor, moscow_tz, \
    local_tz
from mwt import MWT

import datetime


def cancel(bot, update, user_data):
    if "status" in user_data:
        user_data.pop("status")
    if "edit_guild_id" in user_data:
        user_data.pop("edit_guild_id")
    bot.send_message(chat_id=update.message.chat_id, text="Операция отменена.")
    return


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


# Функция, которая считает id битвы по сообщению, крайне желательно переписать нормально, похоже на костыль
# Если message = None, то считает текущее battle_id
def count_battle_id(message):
    first_battle = datetime.datetime(2018, 5, 27, 9, 0, 0, 0)
    interval = datetime.timedelta(hours=8)
    if message is None:
        forward_message_date = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
    else:
        try:
            forward_message_date = local_tz.localize(message.forward_date).astimezone(tz=moscow_tz).replace(tzinfo=None)
        except ValueError:
            try:
                forward_message_date = message.forward_date.astimezone(tz=moscow_tz).replace(tzinfo=None)
            except ValueError:
                forward_message_date = message.forward_date
        except AttributeError:
            forward_message_date = local_tz.localize(message.date).astimezone(tz=moscow_tz).replace(tzinfo=None)
    time_from_first_battle = forward_message_date - first_battle
    battle_id = 0
    while time_from_first_battle > interval:
        time_from_first_battle -= interval
        battle_id = battle_id + 1
    return battle_id


def dict_invert(d):
    return dict(zip(d.values(), d.keys()))


@MWT(timeout=15*60)
def get_admin_ids(bot, chat_id):
    """Returns a list of admin IDs for a given chat. Results are cached for 15 minutes."""
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]
