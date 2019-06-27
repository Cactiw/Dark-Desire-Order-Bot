"""
В данном модуле находятся все необходимые callback-функции для работы с api CW3 (которые вызываются непосредственно
командами в бота, остальные же функции находятся прямо в библиотеке)
"""

from castle_files.libs.api import CW3API
from castle_files.libs.player import Player

from castle_files.bin.stock import get_item_name_by_code

from castle_files.work_materials.globals import conn, SUPER_ADMIN_ID

from config import cwuser, cwpass

import time
import logging
import traceback
import threading

import re


cwapi = CW3API(cwuser, cwpass)


def start_api():
    cwapi.start()


def auth(bot, update):
    cwapi.request_auth_token(update.message.from_user.id)
    bot.send_message(chat_id=update.message.chat_id, text="Пришлите форвард сообщения, полученного от @ChatWarsBot.\n"
                                                          "Если ничего не пришло, то попробуйте ещё раз позже.")


def grant_auth_token(bot, update):
    mes = update.message
    code = re.match("Code (\\d+) to authorize", mes.text)
    if code is None:
        bot.send_message(chat_id=mes.chat_id, text="Произошла ошибка.")
        return
    code = int(code.group(1))
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    request_id = player.api_info.get("requestId")
    if request_id is not None:
        cwapi.grant_additional_operation(mes.from_user.id, request_id, code, player=player)
    else:
        cwapi.grant_token(mes.from_user.id, code)


def update(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    try:
        cwapi.update_player(mes.from_user.id, player=player)
        try:
            gear_access = "gear" in player.api_info.get("access")
        except (TypeError, IndexError):
            gear_access = False
        if gear_access is False:
            cwapi.auth_additional_operation(mes.from_user.id, "GetGearInfo", player=player)
            bot.send_message(chat_id=mes.chat_id,
                             text="Для возможности обновления информации о снаряжении, пожалуйста, "
                                  "Пришлите форвард сообщения, полученного от @ChatWarsBot.")
        else:
            cwapi.update_gear(mes.from_user.id, player=player)
    except RuntimeError:
        bot.send_message(chat_id=mes.chat_id, text="Ошика. Проверьте наличие доступа у бота. "
                                                   "Возможно, стоит сделать /auth ещё раз.")
        return
    bot.send_message(chat_id=mes.chat_id, text="Запрошено обновление профиля. В скором времени данные будут обновлены.")


def update_stock(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    token = player.api_info.get("token") if player.api_info is not None else None
    if token is None:
        auth(bot, update)
        return
    cwapi.update_stock(player.id, player=player)
    bot.send_message(chat_id=mes.chat_id, text="Запрошено обновление стока. В скором времени данные будут обновлены.")


def update_guild(bot, update):
    mes = update.message
    try:
        cwapi.update_guild_info(mes.from_user.id)
    except RuntimeError:
        bot.send_message(chat_id=mes.chat_id, text="Ошика. Проверьте наличие доступа у бота. "
                                                   "Возможно, стоит сделать /auth ещё раз.")
        return
    bot.send_message(chat_id=mes.chat_id, text="Запрошено обновление гильдии. В скором времени данные будут обновлены.")


def repair_comparator(shop, castle):
    shop_castle = shop.get("ownerCastle")
    gold = shop.get("maintenanceCost")
    if shop_castle == castle:
        return -1000 + gold
    return gold


def repair(bot, update):
    mes = update.message
    shops = cwapi.api_info.get("shops")
    if shops is None or not shops:
        bot.send_message(chat_id=mes.chat_id, text="Нет данных о магазинах. Ожидайте обновления.")
        return
    player = Player.get_player(mes.from_user.id)
    player_castle = player.castle if player is not None else '🖤'
    sh = []
    for shop in shops:
        if shop.get("maintenanceEnabled"):
            sh.append(shop)
    sh.sort(key=lambda x: repair_comparator(x, player_castle), reverse=True)

    response = "Доступные магазины для обслуживания:\n"
    castle_stage = sh[0].get("ownerCastle") if sh else '🖤'
    for shop in sh:
        castle, link, gold, mana, discount, name = shop.get("ownerCastle"), shop.get("link"), shop.get("maintenanceCost"), \
                                             shop.get("mana"), shop.get("castleDiscount"), shop.get("name")
        if castle_stage != castle == player_castle:
            castle_stage = player_castle
            response += "\n"
        response += "{} <a href=\"https://t.me/share/url?url={}\">{}</a> 💰{} 💧{} {}" \
                    "\n".format(castle, "/ws_" + link, "/ws_" + link, gold, mana,
                                "🏰: -{}%".format(discount) if discount is not None else "")
    bot.send_message(chat_id=mes.from_user.id, text=response, parse_mode='HTML')


def stock(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if player is None:
        return
    if not player.stock:
        bot.send_message(chat_id=mes.chat_id,
                         text="Отсутствует информация о стоке. Для обновления нажмите /update_stock. "
                              "Требуется доступ к API.")
        return
    response = "<b>📦Склад:\nРесурсы:</b>\n"
    stages = {0: {"name": "Ресурсы:", "to_achieve": lambda code: True},
              1: {"name": "Травы", "to_achieve": lambda code: not code.isdigit() or int(code) >= 39},
              2: {"name": "Корм:", "to_achieve": lambda code: not code.isdigit() or int(code) >= 618},
              3: {"name": "Экипировка и крафт:", "to_achieve": lambda code: not code.isdigit()},
              4: {"name": "Зелья:", "to_achieve": lambda code: not code.isdigit() and code[0] not in ["k", "r", "w"]},
              5: {"name": "Другое:", "to_achieve": lambda code: not code.isdigit() and code[0] != "p"},
              6: {"name": "КОНЕЦ", "to_achieve": lambda code: False}
              }
    stage_num = 0
    next_stage = stages.get(stage_num + 1)
    total_gold = 0
    prices = cwapi.api_info.get("prices") or {}
    for code, count in list(player.stock.items()):
        stage_changed = False
        while next_stage.get("to_achieve")(code):
            stage_changed = True
            stage_num += 1
            next_stage = stages.get(stage_num + 1)
        if stage_changed:
            response += "\n<b>{}</b>\n".format(stages.get(stage_num).get("name"))
        price = prices.get(code) or "❔"
        if len(code) > 4:
            name = code
        else:
            name = get_item_name_by_code(code)
        response += "{} x {} ≈ {}" \
                    "\n".format("{} | {}".format(code, name) if code != name else name, count,
                                "<b>{}</b>💰({}💰x{})".format(price * count, price, count) if isinstance(price, int) else
                                price)
        total_gold += price * count if isinstance(price, int) else 0
    response += "\n\n<b>Всего: {}💰</b>".format(total_gold)
    bot.send_message(chat_id=mes.chat_id, text=response, parse_mode='HTML')


def grassroots_update_players(bot, job):
    cursor = conn.cursor()
    request = "select id, api_info from players where api_info ->> 'token' is not null"
    cursor.execute(request)
    row = cursor.fetchone()
    count = 0
    while row is not None:
        cwapi.update_player(row[0])
        gear_access = "gear" in row[1].get("access") or False
        if gear_access:
            cwapi.update_gear(row[0])
        count += 1
        row = cursor.fetchone()
    bot.send_message(chat_id=SUPER_ADMIN_ID, text="Запрошено обновление профилей <b>{}</b> игроков".format(count),
                     parse_mode='HTML')




"""
def on_conn_open(connection):
    print("conn opened")
    connection.channel(on_open_callback=on_channel_open)


def on_channel_open(new_channel):
    global channel
    channel = new_channel
    print("channel_opened")
    # print(channel.basic_publish(exchange="{}_ex".format(cwuser), routing_key="{}_o".format(cwuser),
                                # body=json.dumps({"action": "getInfo"})))
    tag = channel.basic_consume("{}_i".format(cwuser), receive_callback)
    print("consuming, tag =", tag)
    time.sleep(1)
    channel.basic_cancel(tag)


def receive_callback(channel, method, header, body):

    print(method, header, body)
    print(json.loads(body))
    channel.basic_ack(method.delivery_tag)
    tag = channel.basic_consume("{}_i".format(cwuser), receive_callback)
    print("consuming, tag =", tag)


credentials = pika.PlainCredentials(cwuser, cwpass)
url = f'amqps://{cwuser}:{cwpass}@api.chtwrs.com:5673/?socket_timeout=5'
parameters = pika.URLParameters(url)

# connection = pika.BlockingConnection(parameters)
connection = pika.SelectConnection(parameters, on_open_callback=on_conn_open)
try:
    connection.ioloop.start()
except KeyboardInterrupt:
    print("closing connection")
    # channel.basic_cancel(on_cancel, tag)
    channel.close()
    connection.close()
    # Loop until we're fully closed, will stop on its own
    connection.ioloop.start()

# channel = connection.channel()
getInfo = json.dumps({'action': 'getInfo'})
create_auth_code = json.dumps({
    "action": "createAuthCode",
    "payload": {
        "userId": 231900398
        }
    })
"""
"""success = channel.basic_publish(exchange=f"{cwuser}_ex",
                                routing_key=f"{cwuser}_o",
                                body=create_auth_code)

print(success)
if success or True:
    method_frame, header_frame, body = channel.basic_get(f"{cwuser}_i")
    print(method_frame, header_frame, body)
    if method_frame:
        print(json.loads(body))
        channel.basic_ack(method_frame.delivery_tag)
else:
    print('Failed to publish message')
"""
"""
# method_frame, header_frame, body = channel.basic_get(f"{cwuser}_i")


def consumer(channel):
    print("consuming")
    method_frame, header_frame, body = channel.consume(f"{cwuser}_i")
    print(method_frame, header_frame, body)
    if method_frame:
        print(json.loads(body))
        channel.basic_ack(method_frame.delivery_tag)
    return
"""

"""
threading.Thread(target=consumer, args=[channel]).start()
print("waiting")
time.sleep(10)
print("publish")
channel.basic_publish(exchange=f"{cwuser}_ex",
                      routing_key=f"{cwuser}_o",
                      body=getInfo)
"""
