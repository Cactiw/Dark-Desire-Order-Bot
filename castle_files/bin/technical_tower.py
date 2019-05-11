from castle_files.bin.buttons import send_general_buttons, get_general_buttons, get_update_history_buttons

from castle_files.libs.castle.location import Location
from castle_files.libs.guild import Guild

from castle_files.work_materials.globals import cursor, moscow_tz

import re
import datetime


def technical_tower(bot, update, user_data):
    user_data.update({"status": "technical_tower", "location_id": 5})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def my_cabinet(bot, update, user_data):
    user_data.update({"status": "my_cabinet"})
    response = "Вы входите в свой кабинет. Добро пожаловать. Снова."
    buttons = get_general_buttons(user_data)
    bot.send_message(chat_id=update.message.from_user.id, text=response, reply_markup=buttons, parse_mode='HTML')


def request_change_update_message(bot, update, user_data):
    user_data.update({"status": "editing_update_message"})
    buttons = get_general_buttons(user_data)
    bot.send_message(chat_id=update.message.from_user.id,
                     text="Следующее сообщение будет отображено в башне. Оно должен влезть в это сообщение:\n\n"
                          "{}".format(Location.get_location_enter_text_by_id(5, without_format=True).format(
                                "")), reply_markup=buttons)


def change_update_message(bot, update, user_data):
    user_data.update({"status": "technical_tower", "location_id": 5})
    tower = Location.get_location(5)
    format_values = tower.special_info.get("enter_text_format_values")
    format_values[0] = update.message.text
    tower.special_info.update({"enter_text_format_values": format_values})

    tower.update_location_to_database()
    last_update_id = tower.special_info.get("last_update_id")
    last_update_id += 1
    tower.special_info.update({"last_update_id": last_update_id})
    tower.update_location_to_database()

    request = "insert into bot_updates (text, date_created) VALUES (%s, %s)"
    cursor.execute(request, (update.message.text, datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)))
    bot.send_message(chat_id=update.message.from_user.id,
                     text="Обновление успешно опубликовано. Вы спускаетесь, чтобы проверить, что всё выглядит "
                          "хорошо.\n\n<em>В случае, если после этого не последует сообщение с обновлением, "
                          "измените его</em>", parse_mode='HTML')
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def request_bot_guild_message_notify(bot, update, user_data):
    user_data.update({"status": "sending_bot_guild_message"})
    buttons = get_general_buttons(user_data)
    bot.send_message(chat_id=update.message.from_user.id, text="Следующее сообщение будет разослано во все гильдии",
                     reply_markup=buttons)


def send_bot_guild_message_notify(bot, update, user_data):
    user_data.update({"status": "my_cabinet"})
    for guild_id in Guild.guild_ids:
        guild = Guild.get_guild(guild_id=guild_id)
        bot.send_message(chat_id=guild.chat_id, text=update.message.text, parse_mode='HTML', )
    bot.send_message(update.message.from_user.id, text="Успешно отправлено!",
                     reply_markup=get_general_buttons(user_data))


def get_update_text_and_date(update_id):
    request = "select text, date_created from bot_updates where update_id = %s"
    cursor.execute(request, (update_id,))
    row = cursor.fetchone()
    return row


def update_history(bot, update):
    tower = Location.get_location(5)
    last_update_id = tower.special_info.get("last_update_id")
    text, date = get_update_text_and_date(last_update_id)
    response = "Вы берёте из стопки верхний листок (№ {} — {})\n📜\n".format(last_update_id,
                                                                             date.strftime("%d/%m/%y %H:%M:%S"))
    response += text
    bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML',
                     reply_markup=get_update_history_buttons(last_update_id, last_update_id))


def change_update_history(bot, update):
    mes = update.callback_query.message
    tower = Location.get_location(5)
    last_update_id = tower.special_info.get("last_update_id")
    new_update_id = re.search("_(\\d+)", update.callback_query.data)
    new_update_id = int(new_update_id.group(1))
    if "uhl" in update.callback_query.data:
        new_update_id -= 1
    else:
        new_update_id += 1
    text, date = get_update_text_and_date(new_update_id)
    response = "Вы берёте из стопки листок (№ {} — {})\n📜\n".format(new_update_id,
                                                                     date.strftime("%d/%m/%y %H:%M:%S"))
    buttons = get_update_history_buttons(new_update_id, last_update_id)
    bot.editMessageText(chat_id=mes.chat_id, message_id=mes.message_id, text=response + text, reply_markup=buttons,
                        parse_mode='HTML')
    bot.answerCallbackQuery(callback_query_id=update.callback_query.id)
