from castle_files.work_materials.globals import SUPER_ADMIN_ID, high_access_list, allowed_list, cursor


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
