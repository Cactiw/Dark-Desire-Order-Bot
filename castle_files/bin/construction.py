"""
Здесь все функции, связанные со стройкой, в том числе добыча ресурсов, учёт репутации (в контексте стройки, она ведь
наверняка как-то ещё будет набираться), и сама стройка.
"""
from castle_files.bin.buttons import get_general_buttons, send_general_buttons

from castle_files.libs.player import Player
from castle_files.libs.castle.location import Location
from castle_files.libs.my_job import MyJob

from castle_files.work_materials.globals import job, dispatcher, cursor

import time
import pickle
import logging
import traceback
import re

MINING_QUEST_LENGTH_SECONDS = 3 * 60

construction_jobs = {}


def sawmill(bot, update, user_data):
    user_data.update({"status": "sawmill"})
    buttons = get_general_buttons(user_data)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Вы отправились добывать дерево. Это займёт примерно 3 минуты.\n\nВы можете вернуться "
                          "мгновенно. В этом случае вся добыча будет утеряна.", reply_markup=buttons)
    context = [update.message.from_user.id, user_data]
    j = job.run_once(callback=resource_return, when=MINING_QUEST_LENGTH_SECONDS, context=context)
    old_j = construction_jobs.get(update.message.from_user.id)
    if old_j is not None:
        old_j.job.schedule_removal()
    construction_jobs.update({update.message.from_user.id: MyJob(j, MINING_QUEST_LENGTH_SECONDS)})


def quarry(bot, update, user_data):
    user_data.update({"status": "quarry"})
    buttons = get_general_buttons(user_data)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Вы отправились добывать камень. Это займёт примерно 3 минуты", reply_markup=buttons)
    context = [update.message.from_user.id, user_data]
    j = job.run_once(callback=resource_return, when=MINING_QUEST_LENGTH_SECONDS, context=context)
    old_j = construction_jobs.get(update.message.from_user.id)
    if old_j is not None:
        old_j.job.schedule_removal()
    construction_jobs.update({update.message.from_user.id: MyJob(j, MINING_QUEST_LENGTH_SECONDS)})


def treasury(bot, update, user_data):
    user_data.update({"status": "treasury", "location_id": 6})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def resource_return(bot, job):
    if job.context[1].get("status") not in ["sawmill", "quarry"]:
        return
    statuses_to_res = {"sawmill": "wood", "quarry": "stone"}
    res = statuses_to_res.get(job.context[1].get("status"))
    throne = Location.get_location(2)
    throne.treasury.change_resource(res, 1)
    player = Player.get_player(job.context[0])
    player.reputation += 3
    player.update_to_database()
    job.context[1].update({"status": "castle_gates"})
    buttons = get_general_buttons(job.context[1], player)
    bot.send_message(chat_id=job.context[0], text="Вы успешно добыли {}. Казна обновлена. Получено 3 🔘"
                                                  "".format("дерево" if res == "wood" else "камень"),
                     reply_markup=buttons)


def king_cabinet_construction(bot, update):
    request = "select location_id from locations where state is false and building_process = -1"
    cursor.execute(request)
    row = cursor.fetchone()
    response = "Здания, которые можно начать строить:\n"
    while row is not None:
        location = Location.get_location(row[0])
        if location is None:
            row = cursor.fetchone()
            continue
        response += "<b>{}</b>\nСтоимость: 🌲: <code>{}</code>, ⛰: <code>{}</code>\nНачать строительство: " \
                    "/begin_construction_{}\n".format(location.name, location.need_res_to_construct.get("wood") or 0,
                                                      location.need_res_to_construct.get("stone") or 0, location.id)
        row = cursor.fetchone()
    response += "\n----------------------\nСтройка в процессе:\n"
    request = "select location_id from locations where state is false and building_process >= 0"
    cursor.execute(request)
    row = cursor.fetchone()
    while row is not None:
        location = Location.get_location(row[0])
        if location is None:
            row = cursor.fetchone()
            continue
        response += "<b>{}</b>\nПрогресс: <code>{}</code> из <code>{}</code>\n" \
                    "\n".format(location.name, location.building_process, location.need_clicks_to_construct)
        row = cursor.fetchone()
    bot.send_message(chat_id=update.message.chat_id, text=response, parse_mode='HTML')


def begin_construction(bot, update):
    mes = update.message
    location_id = re.search("_(\\d+)", mes.text)
    if location_id is None:
        bot.send_message(chat_id=mes.chat_id, text="Неверный синтаксис")
        return
    location_id = int(location_id.group(1))
    location = Location.get_location(location_id)
    if location is None:
        bot.send_message(chat_id=mes.chat_id, text="Локация не найдена")
        return
    if location.state is True or location.building_process > 0:
        bot.send_message(chat_id=mes.chat_id, text="Локация уже построена или стройка в процессе")
        return
    location.building_process = 0
    location.update_location_to_database()
    bot.send_message(chat_id=mes.chat_id, text="Стройка <b>{}</b> началась!".format(location.name), parse_mode='HTML')


def construct(bot, update, user_data):

    pass


statuses_to_callbacks = {"sawmill": resource_return, "quarry": resource_return}


def load_construction_jobs():
    try:
        f = open('castle_files/backup/construction_jobs', 'rb')
        up = pickle.load(f)
        print(up)
        for k, v in list(up.items()):
            now = time.time()
            remaining_time = v[1] - now
            print(remaining_time)
            construction_jobs.update({k: MyJob(job.run_once(statuses_to_callbacks.get(v[0]), remaining_time,
                                                            context=[k, dispatcher.user_data.get(k)]), remaining_time)})
        f.close()
    except FileNotFoundError:
        return
    except Exception:
        logging.error(traceback.format_exc())

