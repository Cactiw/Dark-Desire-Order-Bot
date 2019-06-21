"""
В данном модуле находятся все необходимые callback-функции для работы с api CW3 (которые вызываются непосредственно
командами в бота, остальные же функции находятся прямо в библиотеке)
"""

from castle_files.libs.api import CW3API
from castle_files.libs.player import Player

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
        cwapi.update_player(mes.from_user.id)
        try:
            gear_access = "gear" in player.api_info.get("access")
        except (TypeError, IndexError):
            gear_access = False
        if gear_access is False:
            cwapi.auth_additional_operation(mes.from_user.id, "GetGearInfo")
            bot.send_message(chat_id=mes.chat_id,
                             text="Для возможности обновления информации о снаряжении, пожалуйста, "
                                  "Пришлите форвард сообщения, полученного от @ChatWarsBot.")
        else:
            cwapi.update_gear(mes.from_user.id)
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
    cwapi.up



def update_guild(bot, update):
    mes = update.message
    try:
        cwapi.update_guild_info(mes.from_user.id)
    except RuntimeError:
        bot.send_message(chat_id=mes.chat_id, text="Ошика. Проверьте наличие доступа у бота. "
                                                   "Возможно, стоит сделать /auth ещё раз.")
        return
    bot.send_message(chat_id=mes.chat_id, text="Запрошено обновление гильдии. В скором времени данные будут обновлены.")


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
