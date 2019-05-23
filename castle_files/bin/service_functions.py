from castle_files.work_materials.globals import SUPER_ADMIN_ID, high_access_list, allowed_list, cursor, moscow_tz
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


def dict_invert(d):
    return dict(zip(d.values(), d.keys()))


@MWT(timeout=15*60)
def get_admin_ids(bot, chat_id):
    """Returns a list of admin IDs for a given chat. Results are cached for 15 minutes."""
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]
