from castle_files.work_materials.globals import cursor, moscow_tz, SUPER_ADMIN_ID
from castle_files.bin.service_functions import get_admin_ids, check_access

from castle_files.work_materials.filters.general_filters import filter_is_pm

from castle_files.libs.bot_async_messaging import MAX_MESSAGE_LENGTH

import datetime
import logging

triggers_in = {}
global_triggers_in = []

types = {0: "text", 1: "video", 2: "audio", 3: "photo", 4: "document", 5: "sticker", 6: "voice", 7: "Кружок"}


def get_message_type_and_data(message):
    trigger_type, data = None, None
    if message.text:
        trigger_type = 0
        data = message.text
    elif message.video:
        trigger_type = 1
        data = message.video.file_id
    elif message.audio:
        trigger_type = 2
        data = message.audio.file_id
    elif message.photo:
        trigger_type = 3
        data = message.photo[-1].file_id
    elif message.document:
        trigger_type = 4
        data = message.document.file_id
    elif message.sticker:
        trigger_type = 5
        data = message.sticker.file_id
    elif message.voice:
        trigger_type = 6
        data = message.voice.file_id
    elif message.video_note:
        trigger_type = 7
        data = message.video_note.file_id
    return [trigger_type, data]


def send_trigger_with_type_and_data(bot, update, trigger_type, data):
    action = [bot.send_message, bot.send_video, bot.send_audio, bot.send_photo, bot.send_document, bot.send_sticker,
              bot.send_voice, bot.sendVideoNote]
    if trigger_type >= len(action):
        # Неверный тип триггера
        logging.warning("Incorrect trigger_type: {}".format(trigger_type))
        return -1
    action[trigger_type](update.message.chat_id, data, parse_mode='HTML')


def add_trigger(bot, update):
    mes = update.message
    if filter_is_pm(mes):
        return
    if mes.from_user.id not in get_admin_ids(bot=bot, chat_id=mes.chat_id):
        bot.send_message(chat_id=mes.chat_id, text="Доступ только у админов.", reply_to_message_id=mes.message_id)
        return
    trigger_in = mes.text.partition(" ")[2].lower()
    if not mes.text.startswith("/create_global_trigger"):
        chat_id = mes.chat_id
        trigger_list = triggers_in.get(mes.chat_id)
        if trigger_list is None:
            trigger_list = []
            triggers_in.update({mes.chat_id: trigger_list})
    else:
        if mes.from_user.id != SUPER_ADMIN_ID:
            return

        chat_id = 0
        trigger_list = global_triggers_in
    list_triggers = triggers_in.get(chat_id) if chat_id else global_triggers_in
    if trigger_in in list_triggers:
        bot.send_message(chat_id=mes.chat_id, text="Триггер уже существует!", reply_to_message_id=mes.message_id)
        return
    if mes.reply_to_message is None:
        bot.send_message(chat_id=mes.chat_id, text="Сообщение должно быть ответом на другое сообщение.",
                         reply_to_message_id=mes.message_id)
        return
    trigger_type, data = get_message_type_and_data(mes.reply_to_message)
    request = "insert into triggers(text_in, type, data_out, chat_id, creator, date_created) VALUES (%s, %s, %s, %s, " \
              "%s, %s)"
    cursor.execute(request, (trigger_in, trigger_type, data, chat_id, mes.from_user.username or mes.from_user.id,
                             datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)))
    trigger_list.append(trigger_in)
    bot.send_message(chat_id=mes.chat_id, text="Триггер успешно создан!", reply_to_message_id=mes.message_id)


def send_trigger(bot, update):
    mes = update.message
    if filter_is_pm(mes):
        return
    chat_id = mes.chat_id
    trigger_list = triggers_in.get(mes.chat_id)
    if trigger_list is None:
        trigger_list = []
        triggers_in.update({mes.chat_id: trigger_list})
    if mes.text.lower() not in trigger_list:
        chat_id = 0
    request = "select type, data_out from triggers where text_in = %s and chat_id = %s limit 1"
    cursor.execute(request, (mes.text.lower(), chat_id))
    row = cursor.fetchone()
    trigger_type, data = row
    send_trigger_with_type_and_data(bot, update, trigger_type, data)


def remove_trigger(bot, update):
    mes = update.message
    if filter_is_pm(mes):
        return
    if mes.from_user.id not in get_admin_ids(bot=bot, chat_id=mes.chat_id):
        bot.send_message(chat_id=mes.chat_id, text="Доступ только у админов.", reply_to_message_id=mes.message_id)
        return
    text = mes.text.partition(" ")[2].lower()
    chat_id = mes.chat_id
    trigger_list = triggers_in.get(mes.chat_id)
    if trigger_list is None or text not in trigger_list:
        chat_id = 0
        if text in global_triggers_in:
            if not check_access(mes.from_user.id):
                bot.send_message(chat_id=mes.chat_id, text="Недостаточно прав для удаления глобального триггера",
                                 reply_to_message_id=mes.message_id)
                return
        else:
            bot.send_message(chat_id=mes.chat_id, text="Триггер не найден", reply_to_message_id=mes.message_id)
            return
        trigger_list = global_triggers_in
    trigger_list.remove(text)
    request = "delete from triggers where text_in = %s and chat_id = %s"
    cursor.execute(request, (text, chat_id))
    bot.send_message(chat_id=mes.chat_id, text="Триггер успешно удалён!", reply_to_message_id=mes.message_id)


def triggers(bot, update):
    mes = update.message
    if filter_is_pm(mes):
        return
    if mes.from_user.id not in get_admin_ids(bot=bot, chat_id=mes.chat_id):
        bot.send_message(chat_id=mes.chat_id, text="Доступ только у админов.", reply_to_message_id=mes.message_id)
        return
    request = "select text_in, creator, date_created from triggers where chat_id = %s"
    cursor.execute(request, (mes.chat_id,))
    row = cursor.fetchone()
    response = "<b>Список триггеров</b>:\n<b>Локальные триггеры</b>:\n"
    while row is not None:
        response_new = "<code>{}</code> — создал <code>{}</code> {}\n".format(row[0], row[1],
                                                                           row[2].strftime("%d/%m/%y %H:%M:%S"))
        if len(response + response_new) > MAX_MESSAGE_LENGTH:
            bot.send_message(chat_id=mes.chat_id, text=response, parse_mode = 'HTML')
            response = ""
        response += response_new
        row = cursor.fetchone()
    # TODO избавиться от дублирования кода
    request = "select text_in, creator, date_created from triggers where chat_id = 0"
    cursor.execute(request)
    row = cursor.fetchone()
    response += "\n\n<b>Глобальные триггеры</b>:\n"
    while row is not None:
        response_new = "<code>{}</code> — создал <code>{}</code> {}\n".format(row[0], row[1],
                                                                           row[2].strftime("%d/%m/%y %H:%M:%S"))
        if len(response + response_new) > MAX_MESSAGE_LENGTH:
            bot.send_message(chat_id=mes.chat_id, text=response, parse_mode = 'HTML')
            response = ""
        response += response_new
        row = cursor.fetchone()
    # TODO избавиться от дублирования кода
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


def fill_triggers_lists():
    request = "select text_in, chat_id from triggers"
    cursor.execute(request)
    row = cursor.fetchone()
    while row is not None:
        text, chat_id = row
        if chat_id == 0:
            global_triggers_in.append(text)
        else:
            triggers_list = triggers_in.get(chat_id)
            if triggers_list is None:
                triggers_list = []
                triggers_in.update({chat_id: triggers_list})
            triggers_list.append(text)
        row = cursor.fetchone()


def info_trigger(bot, update):
    mes = update.message
    if filter_is_pm(mes):
        return
    if mes.from_user.id not in get_admin_ids(bot=bot, chat_id=mes.chat_id):
        bot.send_message(chat_id=mes.chat_id, text="Доступ только у админов.", reply_to_message_id=mes.message_id)
        return
    text = mes.text.partition(" ")[2].lower()
    list_triggers = triggers_in.get(mes.chat_id)
    chat_id = mes.chat_id
    if list_triggers is None:
        list_triggers = []
        triggers_in.update({mes.chat_id: list_triggers})
    if text not in list_triggers:
        if text not in global_triggers_in:
            bot.send_message(chat_id=mes.chat_id, text="Триггер не найден", reply_to_message_id=mes.message_id)
            return
        chat_id = 0
    request = "select creator, date_created from triggers where text_in = %s and chat_id = %s"
    cursor.execute(request, (text, chat_id))
    row = cursor.fetchone()
    response = "<code>{}</code> — создал <code>{}</code> {}".format(text, row[0], row[1].strftime("%d/%m/%y %H:%M:%S"))
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML', reply_to_message_id=mes.message_id)


def replace_trigger(bot, update):
    mes = update.message
    if filter_is_pm(mes):
        return
    if mes.from_user.id not in get_admin_ids(bot=bot, chat_id=mes.chat_id):
        bot.send_message(chat_id=mes.chat_id, text="Доступ только у админов.", reply_to_message_id=mes.message_id)
        return
    text = mes.text.partition(" ")[2].lower()
    list_triggers = triggers_in.get(mes.chat_id)
    if list_triggers is None or text not in list_triggers:
        bot.send_message(chat_id=mes.chat_id, text="Триггер не найден", reply_to_message_id=mes.message_id)
        return
    request = "update triggers set type = %s, data_out = %s, creator = %s, date_created = %s where chat_id = %s and " \
              "text_in = %s"
    trigger_type, data = get_message_type_and_data(mes.reply_to_message)
    cursor.execute(request, (trigger_type, data, mes.from_user.username or mes.from_user.id,
                             datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None), mes.chat_id, text))
    bot.send_message(chat_id=mes.chat_id, text="Триггер успешно заменён!", reply_to_message_id=mes.message_id)
    return
