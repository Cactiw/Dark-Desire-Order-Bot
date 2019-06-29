"""
Библиотека для работы с АПИ ЧВ3
"""

from castle_files.work_materials.globals import dispatcher, classes_to_emoji_inverted, moscow_tz
from castle_files.libs.player import Player
from castle_files.libs.guild import Guild
from castle_files.bin.stock import get_equipment_by_name, get_item_code_by_name, stock_sort_comparator, \
    get_item_name_by_code

import threading
import logging
import traceback
import time
import datetime
import json
import pika

from multiprocessing import Queue

logger = logging.getLogger("API")
logger.setLevel(logging.INFO)


class CW3API:
    MAX_REQUESTS_PER_SECOND = 30
    api_info = {}

    def __init__(self, cwuser, cwpass, workers=1):
        # TODO Разобраться с несколькими работниками (нельзя использовать 1 канал на всех)
        self.__lock = threading.Lock()
        self.lock = threading.Condition(self.__lock)
        self.cwuser = cwuser
        self.cwpass = cwpass
        self.url = f'amqps://{cwuser}:{cwpass}@api.chtwrs.com:5673/?socket_timeout=5'
        self.parameters = pika.URLParameters(self.url)
        self.connected = False  # Соединение активно в данный момент
        self.connecting = False  # True, если соединение не установлено, но пытается установиться в данный момент
        self.active = True  # True при запуске, и False в самом конце, если self.active == True и
        #                   # self.connected == False, то это значит, что соединение оборвалось само.
        self.connection = None
        self.channel = None
        self.in_channel = None
        self.bot = dispatcher.bot
        self.consumer_tags = []
        self.num_workers = workers  # Число работников, работающих над отправкой запросов
        self.workers = []  # Сами работники
        self.requests_queue = Queue()  # Очередь с запросами (Dict)
        self.__requests_per_second = 0  # Счётчик запросов в секунду

        self.EXCHANGE = "{}_ex".format(cwuser)
        self.ROUTING_KEY = "{}_o".format(cwuser)
        self.INBOUND = "{}_i".format(self.cwuser)
        self.SEX_DIGEST = "{}_sex_digest".format(self.cwuser)
        self.YELLOW_PAGES = "{}_yellow_pages".format(self.cwuser)
        self.DEALS = "{}_deals".format(self.cwuser)

        self.sent = 0
        self.got_responses = 0

        self.callbacks = {
            "createAuthCode": self.on_create_auth_code, "grantToken": self.on_grant_token,
            "requestProfile": self.on_request_profile, "guildInfo": self.on_guild_info,
            "requestGearInfo": self.on_gear_info, "authAdditionalOperation": self.on_request_additional_operation,
            "grantAdditionalOperation": self.on_grant_additional_operational, "requestStock": self.on_stock_info
        }

    def connect(self):
        self.connecting = True
        self.connection = pika.SelectConnection(self.parameters, on_open_callback=self.__on_conn_open)

    def __on_conn_open(self, connection):
        logger.warning("Connection opened")
        self.connection = connection
        self.connection.channel(on_open_callback=self.__on_channel_open)
        self.connection.channel(on_open_callback=self.__on_channel_open)
        self.connection.add_on_close_callback(self.on_conn_close)

    def __on_channel_open(self, channel):
        self.connected = True
        self.connecting = False
        logger.warning("Channel opened")
        if self.channel is None:
            self.channel = channel
        else:
            self.in_channel = channel
            tag = self.in_channel.basic_consume(self.INBOUND, on_message_callback=self.__on_message)
            self.consumer_tags.append(tag)
            tag = self.in_channel.basic_consume(self.SEX_DIGEST, on_message_callback=self.on_sex_digest)
            self.consumer_tags.append(tag)
            tag = self.in_channel.basic_consume(self.DEALS, on_message_callback=self.on_deals)
            self.consumer_tags.append(tag)
            tag = self.in_channel.basic_consume(self.YELLOW_PAGES, on_message_callback=self.on_yellow_pages)
            self.consumer_tags.append(tag)
        logger.warning("Consuming")
        # tag = self.channel.basic_consume(self.SEX_DIGEST, self.on_sex_digest)
        # self.consumer_tags.append(tag)
        # tag = self.channel.basic_consume(self.YELLOW_PAGES, self.on_yellow_pages)
        # self.consumer_tags.append(tag)

        # channel.basic_get(self.SEX_DIGEST, callback=self.on_sex_digest)
        # channel.basic_get(self.YELLOW_PAGES, callback=self.on_yellow_pages)
        # channel.basic_get(self.DEALS, callback=self.on_deals)
        # self.channel.basic_consume(self.DEALS, self.on_deals)

    def __on_cancel(self, obj=None):
        print(obj)
        logger.warning("Consumer cancelled")

    def on_sex_digest(self, channel, method, header, body):
        try:
            channel.basic_ack(method.delivery_tag)
            prices = {}
            body = json.loads(body)
            print(json.dumps(body, sort_keys=1, indent=4, ensure_ascii=False))
            for item in body:
                name = item.get("name")
                try:
                    price = item.get("prices")[0]
                except IndexError:
                    continue
                code = get_item_code_by_name(name)
                if code is None:
                    logging.error("Item code is None for {}".format(name))
                    continue
                prices.update({code: price})
            self.api_info.update({"prices": prices})
            print(json.dumps(self.api_info, sort_keys=1, indent=4, ensure_ascii=False))
        except Exception:
            logging.error(traceback.format_exc())

    def on_yellow_pages(self, channel, method, header, body):
        try:
            channel.basic_ack(method.delivery_tag)
            body = json.loads(body)
            shops = body
            self.api_info.update({"shops": shops})
            print(json.dumps(body, sort_keys=1, indent=4, ensure_ascii=False))
        except Exception:
            logging.error(traceback.format_exc())

    def on_deals(self, channel, method, header, body):
        try:
            channel.basic_ack(method.delivery_tag)
            body = json.loads(body)
            print(json.dumps(body, sort_keys=1, indent=4, ensure_ascii=False))
            seller_id = body.get("sellerId")
            # seller_id = '251066f65507439b9c6838462423f998'  Test
            player = Player.get_player(player_in_game_id=seller_id, notify_on_error=False, new_cursor=True)
            if player is None:
                return
            print(player.id, player.nickname)
            print("player is not None")
            item, price, qty, b_castle, b_name = body.get("item"), body.get("price"), body.get("qty"), \
                                                 body.get("buyerCastle"), body.get("buyerName"),
            response = "🛒Вы продали <b>{}</b> <b>{}</b>.\nПолучено <b>{}</b>💰 ({} x {}💰).\n" \
                       "Покупатель: {}<b>{}</b>".format(qty, item, price * qty, qty, price, b_castle, b_name)
            self.bot.send_message(chat_id=player.id, text=response, parse_mode='HTML')
            # cursor = conn.cursor()
        except Exception:
            logging.error(traceback.format_exc())

    def __on_message(self, channel, method, header, body):
        # print(json.dumps(json.loads(body), sort_keys=1, indent=4, ensure_ascii=False))
        self.got_responses += 1
        print(method, header, body)
        print(json.loads(body))
        print(method.consumer_tag, method.delivery_tag)
        print(header.timestamp)
        channel.basic_ack(method.delivery_tag)
        # method, header, body = json.loads(method), json.loads(header), json.loads(body)
        body = json.loads(body)
        callback = self.callbacks.get(body.get("action"))
        if callback is None:
            logging.warning("Callback is None for {}, {}, {}".format(method, header, body))
            return
        callback(channel, method, header, body)

    def on_create_auth_code(self, channel, method, header, body):
        print("in callback", body)
        if body.get("result") is not "Ok":
            logging.error("error while creating auth code, {}".format(body))
            return

    def on_grant_token(self, channel, method, header, body):
        print("in callback", body)
        if body.get("result") != "Ok":
            logging.error("error while creating auth code, {}".format(body))
            return
        payload = body.get("payload")
        player_id = payload.get("userId")
        token = payload.get("token")
        in_game_id = payload.get("id")
        player = Player.get_player(player_id, notify_on_error=False, new_cursor=True)
        if not all([player, token, player_id]):
            logging.error("Value is None: {} {} {}".format(player, token, player_id))
            return
        if player.api_info is None:
            player.api_info = {}
        player.api_info.update({"token": token, "in_game_id": in_game_id})
        player.update()
        self.bot.send_message(chat_id=player_id,
                              text="API успешно подключено.\nДля возможности обновления информации о снаряжении, "
                                   "пожалуйста, Пришлите форвард сообщения, полученного от @ChatWarsBot.")
        self.auth_additional_operation(player_id, "GetGearInfo")

    def on_request_additional_operation(self, channel, method, header, body):
        if body.get("result") != "Ok":
            logging.error("error while requesting additional operation, {}".format(body))
            return
        try:
            player_id = body.get("payload").get("userId")
            player = Player.get_player(player_id, notify_on_error=False, new_cursor=True)
            if player is None:
                return
            player.api_info.update({"requestId": body.get("uuid")})
            player.update()
        except Exception:
            logging.error(traceback.format_exc())

    def on_grant_additional_operational(self, channel, method, header, body):
        try:
            payload = body.get("payload")
            player_id = payload.get("userId")
            request_id = payload.get("requestId")
            player = Player.get_player(player_id, notify_on_error=False, new_cursor=True)
            if "requestId" in player.api_info and player.api_info.get("requestId") == request_id:
                player.api_info.pop("requestId")
                player.update()
            if body.get("result") != "Ok":
                logging.error("error while granting additional operation, {}".format(body))
                return
            access = player.api_info.get("access")
            if access is None:
                access = []
                player.api_info.update({"access": access})
            if "gear" not in access:
                access.append("gear")  # TODO Если будет больше 1 операции, то сделать отслеживание доступа.
            player.update()
            self.bot.send_message(chat_id=player_id, text="Действие API успешно разрешено.")
        except Exception:
            logging.error(traceback.format_exc())




    def on_request_profile(self, channel, method, header, body):
        if body.get("result") != "Ok":
            logging.error("error while requesting profile, {}".format(body))
            return
        print(json.dumps(body, sort_keys=1, indent=4, ensure_ascii=False))
        try:
            payload = body.get("payload")
            user_id = payload.get("userId")
            player = Player.get_player(user_id, notify_on_error=False, new_cursor=True)
            if player is None:
                return
            profile = payload.get("profile")
            player.attack = profile.get("atk")
            player.castle = profile.get("castle")
            try:
                player.game_class = classes_to_emoji_inverted.get(profile.get("class"))
            except Exception:
                logging.error(traceback.format_exc())
            player.defense = profile.get("def")
            player.exp = profile.get("exp")
            player.guild_tag = profile.get("guild_tag")
            player.nickname = ("[{}]".format(player.guild_tag) if player.guild_tag is not None else
                               "") + profile.get("userName")
            player.last_updated = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)

            player.update_to_database()
            print("Profile updated throug the API for {}".format(player.nickname))
        except Exception:
            logging.error(traceback.format_exc())

    def on_gear_info(self, channel, method, header, body):
        if body.get("result") != "Ok":
            logging.error("error while requesting guild info, {}".format(body))
            return
        try:
            print(json.dumps(body, sort_keys=1, indent=4, ensure_ascii=False))
            payload = body.get("payload")
            player_id = payload.get("userId")
            player = Player.get_player(player_id, notify_on_error=False, new_cursor=True)
            if player is None:
                return
            gear_info = payload.get("gearInfo")
            player_equipment = {
                "main_hand": None,
                "second_hand": None,
                "head": None,
                "gloves": None,
                "armor": None,
                "boots": None,
                "cloaks": None
            }
            for item in list(gear_info.values()):
                name = item.get("name")
                if name is None:
                    continue
                eq = get_equipment_by_name(name)
                if eq is None:
                    logging.warning("Equipment with name {} is None".format(name))
                    continue
                attack = item.get("atk") or 0
                defense = item.get("def") or 0
                eq.name, eq.attack, eq.defense = name, attack, defense
                player_equipment.update({eq.place: eq})
            player.equipment = player_equipment
            player.update()
        except Exception:
            logging.error(traceback.format_exc())

    def on_stock_info(self, channel, method, header, body):
        try:
            if body.get("result") != "Ok":
                logging.error("error while requesting guild info, {}".format(body))
                return
            print(json.dumps(body, sort_keys=1, indent=4, ensure_ascii=False))
            payload = body.get("payload")
            player_id = payload.get("userId")
            player = Player.get_player(player_id, notify_on_error=False, new_cursor=True)
            if player is None:
                return
            old_stock = player.stock
            player_stock = {}
            stock = payload.get("stock")
            for name, count in list(stock.items()):
                code = get_item_code_by_name(name)
                player_stock.update({code or name: count})
            player_stock = {k: player_stock[k] for k in sorted(player_stock, key=stock_sort_comparator)}
            player.stock = player_stock
            player.update()
            if player.api_info.get("change_stock_send"):
                # Уведомление игрока о изменении в стоке
                response = "Изменения в стоке:\n"
                prices = self.api_info.get("prices") or {}
                changes = {}
                for code, count in list(old_stock.items()):
                    new_count = player.stock.get(code) or 0
                    change = new_count - count
                    if change != 0:
                        changes.update({code: change})
                for code, count in list(player.stock.items()):
                    if code in changes:
                        continue
                    old_count = old_stock.get(code)
                    change = count - old_count
                    if change != 0:
                        changes.update({code: change})
                response_added, response_lost = "\n<b>➕Приобретено:</b>\n", "\n<b>➖Потеряно:</b>\n"
                gold_added, gold_lost = 0, 0
                changes_sorted = {k: v for k, v in sorted(list(changes.items()),
                                                          key=lambda x: (prices.get(x[0]) or 10000) * x[1])}
                for code, change in list(changes_sorted.items()):
                    price = prices.get(code) or 0
                    if change > 0:
                        response_added += "+{} {} ≈ {}\n".format(change, get_item_name_by_code(code),
                                                                 "{}💰".format(price * change) if price != 0 else "❔")
                        gold_added += change * price
                    else:
                        response_lost += "{} {} ≈ {}\n".format(change, get_item_name_by_code(code),
                                                               "{}💰".format(price * change) if price != 0 else "❔")
                        gold_lost += change * price
                response_added += "<b>В сумме</b>: <code>{}</code>💰\n".format(gold_added) if gold_added > 0 else ""
                response_lost += "<b>В сумме</b>: <code>{}</code>💰\n".format(gold_lost) if gold_lost < 0 else ""
                response += response_added + response_lost
                response += "\n<b>Всего:</b> <code>{}</code>💰".format(gold_added + gold_lost)
                self.bot.send_message(chat_id=player.id, text=response, parse_mode='HTML')
                player.api_info.pop("change_stock_send")
                player.update()

            print(player.stock)
        except Exception:
            logging.error(traceback.format_exc())

    def on_guild_info(self, channel, method, header, body):
        if body.get("result") != "Ok":
            logging.error("error while requesting guild info, {}".format(body))
            return
        print(body)
        print(json.dumps(body, sort_keys=1, indent=4, ensure_ascii=False))

    #

    # Запрос доступа к апи
    def request_auth_token(self, user_id):
        self.publish_message({
              "action": "createAuthCode",
              "payload": {"userId": user_id}
        })

    # Предоставление кода для получения токена к апи
    def grant_token(self, user_id, auth_code):
        payload = {
                "userId": user_id,
                "authCode": "{}".format(auth_code)
            }
        self.publish_message({
            "action": "grantToken",
            "payload": payload
        })

    def auth_additional_operation(self, user_id, operation, player=None):
        if player is None:
            player = Player.get_player(user_id, notify_on_error=False)
            if player is None:
                raise RuntimeError
        if player is None:
            raise RuntimeError
        token = player.api_info.get("token")
        if token is None:
            raise RuntimeError
        self.publish_message({
            "token": token,
            "action": "authAdditionalOperation",
            "payload": {"operation": operation}
        })

    def grant_additional_operation(self, user_id, request_id, auth_code, player=None):
        if player is None:
            player = Player.get_player(user_id, notify_on_error=False)
        if player is None:
            raise RuntimeError
        token = player.api_info.get("token")
        if token is None:
            raise RuntimeError

        payload = {
            "requestId": request_id,
            "authCode": "{}".format(auth_code)
        }
        self.publish_message({
            "token": token,
            "action": "grantAdditionalOperation",
            "payload": payload
        })

    # Обновление одного игрока через API, кидает RuntimeError, если не найден игрок или его токен
    def update_player(self, player_id, player=None):
        if player is None:
            player = Player.get_player(player_id, notify_on_error=False)
            if player is None:
                raise RuntimeError
        if player is None:
            raise RuntimeError
        token = player.api_info.get("token")
        if token is None:
            raise RuntimeError
        self.publish_message({
            "token": token,
            "action": "requestProfile"
        })

    def update_gear(self, player_id, player=None):
        if player is None:
            player = Player.get_player(player_id, notify_on_error=False)
            if player is None:
                raise RuntimeError
        if player is None:
            raise RuntimeError
        token = player.api_info.get("token")
        if token is None:
            raise RuntimeError
        self.publish_message({
            "token": token,
            "action": "requestGearInfo"
        })

    def update_stock(self, player_id, player=None):
        if player is None:
            player = Player.get_player(player_id, notify_on_error=False)
            if player is None:
                raise RuntimeError
        token = player.api_info.get("token")
        if token is None:
            raise RuntimeError
        self.publish_message({
            "token": token,
            "action": "requestStock"
        })
        print("published")

    # Обновление одного игрока через API, кидает RuntimeError, если не найден игрок или его токен
    def update_guild_info(self, player_id, player=None):
        if player is None:
            player = Player.get_player(player_id, notify_on_error=False)
            if player is None:
                raise RuntimeError
        if player is None:
            raise RuntimeError
        token = player.api_info.get("token")
        if token is None:
            raise RuntimeError
        self.publish_message({
            "token": token,
            "action": "guildInfo"
        })

    def get_message(self):
        self.channel.basic_get(self.INBOUND, self.__on_message)

    # Запрос кладётся в очередь запросов
    def publish_message(self, message):
        self.requests_queue.put(message)

    # Голая отправка запроса, без ограничений
    def __publish_message(self, message):
        print("sending request", message)
        print(json.dumps(message))
        # properties = pika.BasicProperties(app_id='cactiw_castle_skalen', content_type='application/json')
        try:
            print("SENDING PID = ", threading.current_thread().ident)
            self.sent += 1
            return self.channel.basic_publish(exchange=self.EXCHANGE, routing_key=self.ROUTING_KEY,
                                              body=json.dumps(message), properties=None)
        except AttributeError:
            logging.warning(traceback.format_exc())
            self.sent -= 1
            self.publish_message(message)

    # Функция для отправки запроса с учётом всех ограничений
    def actually_publish_message(self, message):
        try:
            self.lock.acquire()
            print(self.connected, self.channel)
            if self.active is False:
                return
            if not self.connected or self.channel is None:
                for i in range(10):
                    time.sleep(1)
                    if self.connected:
                        break
                if not self.connected:
                    raise RuntimeError
            while True:
                if self.__requests_per_second < CW3API.MAX_REQUESTS_PER_SECOND:
                    self.__requests_per_second += 1
                    self.lock.release()
                    threading.Timer(function=self.__release_resource, interval=1, args=[]).start()
                    break
                else:
                    self.lock.wait()
        except Exception:
            logging.error(traceback.format_exc())
        finally:
            try:
                pass
                # self.lock.release()
            except Exception:
                logging.error(traceback.format_exc())
        return self.__publish_message(message)
        pass

    def __release_resource(self):
        with self.lock:
            self.__requests_per_second -= 1
            self.lock.notify_all()

    def __work(self):
        request = self.requests_queue.get()
        while self.active is True and request is not None:
            try:
                self.actually_publish_message(message=request)
            except Exception:
                logging.error(traceback.format_exc())
            request = self.requests_queue.get()

    # Метод, который будет вызван обрыве соединения, если оно оборвалось
    def on_conn_close(self, *args):  # connection, reply_code, reply_text):
        print("in on_conn_close")
        if self.active is False:
            return
        self.channel = None
        self.in_channel = None
        self.connected = False
        # logging.warning("Connection closed, {}, {}, reconnection in 5 seconds".format(reply_code, reply_text))
        logging.warning("Connection closed, {}, reconnection in 5 seconds".format(args))
        time.sleep(5)
        self.reconnect()
        # self.connection.add_timeout(5, self.reconnect)

    def reconnect(self):
        self.connection.ioloop.stop()
        self.connect()
        self.connection.ioloop.start()

    def start(self):
        logger.warning("Starting the API")
        self.active = True
        self.connect()
        for i in range(self.num_workers):
            worker = threading.Thread(target=self.__work)
            worker.start()
            self.workers.append(worker)
        try:
            self.connection.ioloop.start()
        except KeyboardInterrupt:
            print("closing connection")
            if self.consumer_tags:
                for tag in self.consumer_tags:
                    self.in_channel.basic_cancel(self.__on_cancel, tag)
            self.channel.close()
            self.in_channel.close()
            self.connection.close()
            # Loop until we're fully closed, will stop on its own
            self.connection.ioloop.start()

    def stop(self):
        print("closing connection")
        print("Sent {} requests, got {} responses".format(self.sent, self.got_responses))
        self.active = False
        for i in range(self.num_workers):
            self.requests_queue.put(None)
        if self.consumer_tags:
            for tag in self.consumer_tags:
                self.in_channel.basic_cancel(tag, self.__on_cancel)
        self.channel.close()
        self.in_channel.close()
        self.connection.close()
        print("starting loop")
        self.connection.ioloop.stop()
        print("loop ended")
        for worker in self.workers:
            worker.join()
