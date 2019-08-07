"""
Здесь все функции, связанные со стройкой, в том числе добыча ресурсов, учёт репутации (в контексте стройки, она ведь
наверняка как-то ещё будет набираться), и сама стройка.
"""
from castle_files.bin.buttons import get_general_buttons, send_general_buttons

from castle_files.libs.player import Player
from castle_files.libs.castle.location import Location, locations
from castle_files.libs.my_job import MyJob

from castle_files.work_materials.globals import job, dispatcher, cursor, moscow_tz, construction_jobs, conn
from castle_files.work_materials.quest_texts import quest_texts

import time
import pickle
import logging
import traceback
import json
import datetime
import random
import re

import threading

MINING_QUEST_DURATION_SECONDS = 3 * 60
CONSTRUCTION_DURATION_SECONDS = 5 * 60

CONSTRUCTION_REPUTATION = 5


def sawmill(bot, update, user_data):
    user_data.update({"status": "sawmill"})
    buttons = get_general_buttons(user_data)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Вы отправились добывать дерево. Это займёт примерно 3 минуты.\n\nВы можете вернуться "
                          "мгновенно. В этом случае вся добыча будет утеряна.", reply_markup=buttons)
    context = [update.message.from_user.id, user_data]
    j = job.run_once(callback=resource_return, when=MINING_QUEST_DURATION_SECONDS, context=context)
    old_j = construction_jobs.get(update.message.from_user.id)
    if old_j is not None:
        old_j.job.schedule_removal()
    construction_jobs.update({update.message.from_user.id: MyJob(j, MINING_QUEST_DURATION_SECONDS)})


def quarry(bot, update, user_data):
    user_data.update({"status": "quarry"})
    buttons = get_general_buttons(user_data)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Вы отправились добывать камень. Это займёт примерно 3 минуты", reply_markup=buttons)
    context = [update.message.from_user.id, user_data]
    j = job.run_once(callback=resource_return, when=MINING_QUEST_DURATION_SECONDS, context=context)
    old_j = construction_jobs.get(update.message.from_user.id)
    if old_j is not None:
        old_j.job.schedule_removal()
    construction_jobs.update({update.message.from_user.id: MyJob(j, MINING_QUEST_DURATION_SECONDS)})


def treasury(bot, update, user_data):
    user_data.update({"status": "treasury", "location_id": 6})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def resource_return(bot, job):
    cursor = conn.cursor()
    if job.context[1].get("status") not in ["sawmill", "quarry"]:
        return
    statuses_to_res = {"sawmill": "wood", "quarry": "stone"}
    res = statuses_to_res.get(job.context[1].get("status"))
    count = 1
    throne = Location.get_location(2)
    throne.treasury.change_resource(res, count)
    player = Player.get_player(job.context[0])
    player.reputation += 3
    player.update_to_database()
    job.context[1].update({"status": "castle_gates"})
    buttons = get_general_buttons(job.context[1], player)
    request = "insert into castle_logs(player_id, action, result, additional_info, date) values (%s, %s, %s, %s, %s)"
    cursor.execute(request, (player.id, "collect_resources", 1, json.dumps({"resource": res, "count": count}),
                             datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)))
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
    treasury = Location.get_location(6)
    response += "\n----------------------\nСостояние казны: 🌲Дерево: <b>{}</b>, " \
                "⛰Камень: <b>{}</b>".format(treasury.wood, treasury.stone)
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
    treasury = Location.get_location(6)
    need_wood = location.need_res_to_construct.get("wood") or 0
    need_stone = location.need_res_to_construct.get("stone") or 0
    if treasury.wood < need_wood or treasury.stone < need_stone:
        bot.send_message(chat_id=mes.chat_id, text="Не хватает ресурсов для начала строительства. "
                                                   "Вам следует быть жестче с подчинёнными!")
        return
    treasury.wood -= need_wood
    treasury.stone -= need_stone
    treasury.update_location_to_database()
    ctrl = Location.get_location(0)
    old = ctrl.special_info.get("enter_text_format_values")
    old[1] = treasury.wood
    old[2] = treasury.stone
    location.building_process = 0
    location.update_location_to_database()
    bot.send_message(chat_id=mes.chat_id, text="Стройка <b>{}</b> началась!".format(location.name), parse_mode='HTML')


def construction_plate(bot, update, user_data):
    user_data.update({"status": "construction_plate", "location_id": 7})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


def construct(bot, update, user_data):
    mes = update.message
    location_id = None
    for loc in list(locations.values()):
        if loc.name == mes.text:
            location_id = loc.id
            break
    if location_id is None:
        send_general_buttons(mes.from_user.id, user_data=user_data, bot=bot)
        return
    location = Location.get_location(location_id)
    if location is None:
        bot.send_message(chat_id=mes.chat_id, text="Локация не найдена.")
        return
    if location.state is True or location.building_process < 0:
        bot.send_message(chat_id=mes.chat_id, text="Локация уже построена или стройка не начиналась.")
        return

    context = [update.message.from_user.id, user_data]
    j = job.run_once(callback=construction_return, when=CONSTRUCTION_DURATION_SECONDS, context=context)
    old_j = construction_jobs.get(update.message.from_user.id)
    if old_j is not None:
        old_j.job.schedule_removal()
    construction_jobs.update({update.message.from_user.id: MyJob(j, CONSTRUCTION_DURATION_SECONDS)})
    user_data.update({"status": "construction", "construction_id": location.id})
    buttons = get_general_buttons(user_data)
    bot.send_message(chat_id=update.message.chat_id, text="Вы отправились на стройку. Это займёт 5 минут.",
                     reply_markup=buttons)


def construction_return(bot, job):
    cursor = conn.cursor()
    player_id = job.context[0]
    user_data = job.context[1]
    if user_data.get("status") not in ["construction"]:
        return
    location_id = user_data.get("construction_id")
    if location_id is None:
        bot.send_message(chat_id=player_id, text="Ошибка поиска локации.")
        return
    location = Location.get_location(location_id)
    if location is None:
        bot.send_message(chat_id=player_id, text="Ошибка поиска локации.")
        return
    print(location.name, location.state, location.building_process)
    if location.state is True or location.building_process < 0:
        bot.send_message(chat_id=player_id, text="Локация уже построена или стройка не начиналась. Возможно, локацию "
                                                 "построили в то время, пока вы добирались до стройки.")
        return
    location.building_process += 1
    player = Player.get_player(job.context[0])
    if location.building_process >= location.need_clicks_to_construct:
        location.state = True
        bot.send_message(chat_id=player_id, text="Локация успешно построена! Вы положили последний камень!")
        player.reputation += 50 - CONSTRUCTION_REPUTATION
    player.reputation += CONSTRUCTION_REPUTATION
    player.update_to_database()
    location.update_location_to_database()
    user_data.update({"status": "central_square"})
    if "construction_id" in user_data:
        user_data.pop("construction_id")
    if job.context[0] in construction_jobs:
        try:
            construction_jobs.pop(job.context[0])
        except Exception:
            logging.error(traceback.format_exc())
    buttons = get_general_buttons(job.context[1], player)
    request = "insert into castle_logs(player_id, action, result, additional_info, date) values (%s, %s, %s, %s, %s)"
    cursor.execute(request, (player.id, "construction", 1, json.dumps({"location_id": location_id}),
                             datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)))
    bot.send_message(chat_id=job.context[0],
                     text="Вы вернулись со стройки. Получено <code>{}</code> 🔘".format(CONSTRUCTION_REPUTATION),
                     reply_markup=buttons, parse_mode='HTML')


def tea_party(bot, update, user_data):
    user_data.update({"status": "tea_party", "location_id": 9})
    send_general_buttons(update.message.from_user.id, user_data, bot=bot)


# Создаёт работу через when секунд (на запуск callback функции), добавляет в construction_jobs для сохранения на диске и
# автоматического поднятия при перезапуске бота.
def safe_job_create(callback, when, player_id, context=None, cancel_old=True):
    j = job.run_once(callback=callback, when=when, context=context)
    if cancel_old:
        old_j = construction_jobs.get(player_id)
        if old_j is not None:
            old_j.job.schedule_removal()
    construction_jobs.update({player_id: MyJob(j, when)})


quest_lock = threading.Lock()
quest_players = {"exploration": [], "pit": []}


def tea_party_quest(bot, update, user_data):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    quests = {"разведка": "exploration",
              "котлован": "pit"}
    quest = None
    for key, v in list(quests.items()):
        if key.lower() in mes.text.lower():
            quest = v
            break
    if quest is None:
        logging.error("Quest is None")
        return

    user_data.update({"status": quest})
    with quest_lock:
        lst: [int] = quest_players.get(quest)
        # lst.append(player.id)
    buttons = get_general_buttons(user_data)
    bot.send_message(chat_id=mes.chat_id, text="Ты куда-то отправился. Вернуться невозможно. /f", reply_markup=buttons)
    safe_job_create(two_go_action, 30, player.id, {"quest": quest, "player_id": player.id})
    # job.run_once(two_go_action, random.random() * 180 + 120, {"quest": quest, "player_id": player.id})


def two_go_action(bot, cur_job):
    quest, player_id = cur_job.context.get("quest"), cur_job.context.get("player_id")
    player = Player.get_player(player_id)
    user_data = dispatcher.user_data.get(player_id)

    status = user_data.get("status")
    if status != quest:
        return

    with quest_lock:
        player_list = quest_players.get(quest)
        if player_list is None:
            logging.error("No quest configured for {}".format(quest))
            return
        if not player_list:
            player_list.append(player_id)
            safe_job_create(player_awaiting_timeout, 60 * 3, player.id,
                            context={"quest": quest, "player_id": player.id})
            user_data.update({"status": "waiting_second_player_for_quest"})
            return
        else:
            pair_player_id = player_list.pop()
    pair_player = Player.get_player(pair_player_id)
    pair_user_data = dispatcher.user_data.get(pair_player_id)
    user_data.update({"status": "two_quest"})
    pair_user_data.update({"status": "two_quest"})
    bot.send_message(chat_id=player_id,
                     text="Ты встретил <b>{}</b> (@{}). У вас 3 минуты, чтобы нажать /go с промежутком менее 30 "
                          "секунд".format(pair_player.nickname, pair_player.username), parse_mode='HTML')
    bot.send_message(chat_id=pair_player_id,
                     text="Ты встретил <b>{}</b> (@{}). У вас 3 минуты, чтобы нажать /go с промежутком менее 30 "
                          "секунд".format(player.nickname, player.username), parse_mode='HTML')
    safe_job_create(two_action_timeout, 30, player.id, {"ids": [player_id, pair_player_id]})


GO_SUCCESS_REPUTATION = 10
GO_NOT_SUCCESS_REPUTATION = 3


# Таймаут подбора второго игрока
def player_awaiting_timeout(bot, cur_job):
    quest, player_id = cur_job.context.get("quest"), cur_job.context.get("player_id")
    player = Player.get_player(player_id)
    user_data = dispatcher.user_data.get(player_id)

    status = user_data.get("status")
    if status != "waiting_second_player_for_quest":
        return

    user_data.update({"status": "tea_party"})
    buttons = get_general_buttons(user_data, player)
    player.reputation += GO_NOT_SUCCESS_REPUTATION
    player.update()
    bot.send_message(chat_id=player_id, text=random.choice(quest_texts[quest]["one_player"]) +
                                             "\nПолучено {}🔘".format(GO_NOT_SUCCESS_REPUTATION), reply_markup=buttons)


def two_action_timeout(bot, cur_job):
    player_id, pair_player_id = cur_job.context.get("ids")
    player, pair_player = Player.get_player(player_id), Player.get_player(pair_player_id)
    user_data, pair_user_data = dispatcher.user_data.get(player_id), dispatcher.user_data.get(pair_player_id)

    status = user_data.get("status")
    if status != "two_quest":
        return

    user_data.update({"status": "tea_party"})
    pair_user_data.update({"status": "tea_party"})
    player.reputation += GO_NOT_SUCCESS_REPUTATION
    pair_player.reputation += GO_NOT_SUCCESS_REPUTATION
    player.update()
    pair_player.update()
    buttons = get_general_buttons(user_data, player)
    bot.send_message(chat_id=player_id, text="Вы не смогли скоординироваться. Получено {}🔘"
                                             "".format(GO_NOT_SUCCESS_REPUTATION), reply_markup=buttons)
    bot.send_message(chat_id=pair_player_id, text="Вы не смогли скоординироваться. Получено {}🔘"
                                                  "".format(GO_NOT_SUCCESS_REPUTATION), reply_markup=buttons)


statuses_to_callbacks = {"sawmill": resource_return, "quarry": resource_return, "construction": construction_return,
                         "exploration": two_go_action, "pit": two_go_action, "two_quest": two_action_timeout,
                         "waiting_second_player_for_quest": player_awaiting_timeout}


def load_construction_jobs():
    try:
        f = open('castle_files/backup/construction_jobs', 'rb')
        up = pickle.load(f)
        print(up)
        for k, v in list(up.items()):
            now = time.time()
            remaining_time = v[1] - now
            print("remaining", remaining_time)
            callback = statuses_to_callbacks.get(v[0])
            if callback is None:
                logging.warning("Callback is None for status {}".format(v[0]))
                continue
            if v[2] is None:
                context = [k, dispatcher.user_data.get(k)]
            else:
                context = v[2]
            if remaining_time < 0:
                try:
                    job.run_once(callback, 0.1, context=context)
                except Exception:
                    logging.error(traceback.format_exc())
                    pass
                continue
            try:
                construction_jobs.update({k: MyJob(job.run_once(callback, remaining_time,
                                                                context=context),
                                                   remaining_time)})
            except Exception:
                logging.error(traceback.format_exc())
        f.close()
    except FileNotFoundError:
        return
    except Exception:
        logging.error(traceback.format_exc())

