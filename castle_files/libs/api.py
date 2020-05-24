"""
Библиотека для работы с АПИ ЧВ3
"""

from castle_files.work_materials.globals import dispatcher, classes_to_emoji_inverted, moscow_tz, Conn, psql_creditals,\
    MID_CHAT_ID
from castle_files.libs.player import Player
from castle_files.libs.guild import Guild
from castle_files.libs.equipment import Equipment
from castle_files.bin.stock import get_equipment_by_name, get_item_code_by_name, stock_sort_comparator, \
    get_item_name_by_code

import threading
import logging
import traceback
import time
import datetime
import json
import pika
import re
import copy

from multiprocessing import Queue

logger = logging.getLogger("API")
logger.setLevel(logging.INFO)

print(threading.current_thread().ident)


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

        self.guild_changes = {}
        self.guild_changes_work = None

        self.conn = None
        self.cursor = None
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

    def __on_cancel(self, obj=None):
        print(obj)
        logger.warning("Consumer cancelled")

    def on_sex_digest(self, channel, method, header, body):
        try:
            channel.basic_ack(method.delivery_tag)
            prices = {}
            body = json.loads(body)
            # print(json.dumps(body, sort_keys=1, indent=4, ensure_ascii=False))
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
            # print(json.dumps(self.api_info, sort_keys=1, indent=4, ensure_ascii=False))
        except Exception:
            logging.error(traceback.format_exc())

    def on_yellow_pages(self, channel, method, header, body):
        try:
            channel.basic_ack(method.delivery_tag)
            body = json.loads(body)
            shops = body
            self.api_info.update({"shops": shops})
            # print(json.dumps(body, sort_keys=1, indent=4, ensure_ascii=False))
        except Exception:
            logging.error(traceback.format_exc())

    def on_deals(self, channel, method, header, body):
        try:
            channel.basic_ack(method.delivery_tag)
            body = json.loads(body)
            # print(json.dumps(body, sort_keys=1, indent=4, ensure_ascii=False))
            seller_id = body.get("sellerId")
            item, qty, castle = body.get("item"), body.get("qty"), body.get("buyerCastle")
            match = re.match("((vial)|(potion)|(bottle)) of ((rage)|(peace)|(morph))", item.lower())
            if match is not None:
                # Это зелье ярости, мира или морфа.
                type = match.group(1)
                category = match.group(5)
                potions_info = self.api_info.get("potions_info")
                if potions_info is None:
                    potions_info = {}
                    self.api_info.update({"potions_info": potions_info})
                cat = potions_info.get(category)
                if cat is None:
                    cat = {}
                    potions_info.update({category: cat})
                count_by_castles = cat.get(type)
                if count_by_castles is None:
                    count_by_castles = {}
                    cat.update({type: count_by_castles})
                count = count_by_castles.get(castle) or 0
                count_by_castles.update({castle: count + qty})

            # seller_id = '251066f65507439b9c6838462423f998'  Test
            player = Player.get_player(player_in_game_id=seller_id, notify_on_error=False, new_cursor=self.cursor)
            if player is None or (player.settings is not None and player.settings.get("sold_notify") is False):
                return
            print(player.id, player.nickname)
            print("player is not None")
            item, price, qty, b_castle, b_name = item, body.get("price"), qty, castle, body.get("buyerName")
            response = "🛒Вы продали <b>{}</b> <b>{}</b>.\nПолучено <b>{}</b>💰 ({} x {}💰).\n" \
                       "Покупатель: {}<b>{}</b>".format(qty, item, price * qty, qty, price, b_castle, b_name)
            self.bot.send_message(chat_id=player.id, text=response, parse_mode='HTML')
            # cursor = conn.cursor()
        except Exception:
            logging.error(traceback.format_exc())

    def __on_message(self, channel, method, header, body):
        # print(json.dumps(json.loads(body), sort_keys=1, indent=4, ensure_ascii=False))
        self.got_responses += 1
        # print(method, header, body)
        # print(json.loads(body))
        # print(method.consumer_tag, method.delivery_tag)
        # print(header.timestamp)
        channel.basic_ack(method.delivery_tag)
        # method, header, body = json.loads(method), json.loads(header), json.loads(body)
        body = json.loads(body)
        result = body.get("result")
        if result == 'InvalidToken':
            cursor = self.conn.cursor()
            request = "select id from players where (api_info ->> 'token')::text = %s::text"
            cursor.execute(request, (body.get("payload").get("token"),))
            player_id = cursor.fetchone()
            if player_id is not None:
                player_id = player_id[0]
                player = Player.get_player(player_id)
                try:
                    player.api_info.pop("token")
                    player.api_info.pop("access")
                except KeyError:
                    pass
                player.update()

        callback = self.callbacks.get(body.get("action"))
        if callback is None:
            logging.warning("Callback is None for {}, {}, {}".format(method, header, body))
            return
        callback(channel, method, header, body)

    def on_create_auth_code(self, channel, method, header, body):
        print("in callback", body)
        if body.get("result") != "Ok":
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
        player = Player.get_player(player_id, notify_on_error=False, new_cursor=self.cursor)
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
            player = Player.get_player(player_id, notify_on_error=False, new_cursor=self.cursor)
            if player is None:
                return
            player.api_info.update({"requestId": body.get("uuid")})
            player.update()
        except Exception:
            logging.error(traceback.format_exc())

    def on_grant_additional_operational(self, channel, method, header, body):
        accesses = {"GetGearInfo": "gear", "TradeTerminal": "wtb"}
        try:
            payload = body.get("payload")
            player_id = payload.get("userId")
            request_id = payload.get("requestId")
            player = Player.get_player(player_id, notify_on_error=False, new_cursor=self.cursor)
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
            operation = accesses.get(player.api_info.get("operation"))
            if operation not in access:
                access.append(operation)
            player.api_info.pop("operation")
            player.update()
            self.bot.send_message(chat_id=player_id, text="Действие API успешно разрешено.")
        except Exception:
            logging.error(traceback.format_exc())




    def on_request_profile(self, channel, method, header, body):
        if body.get("result") != "Ok":
            logging.error("error while requesting profile, {}".format(body))
            return
        # print(json.dumps(body, sort_keys=1, indent=4, ensure_ascii=False))
        try:
            payload = body.get("payload")
            user_id = payload.get("userId")
            player = Player.get_player(user_id, notify_on_error=False, new_cursor=self.cursor)
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
            player.lvl = profile.get("lvl")
            player.exp = profile.get("exp")
            player.guild_tag = profile.get("guild_tag")
            player.hp = profile.get("hp")
            player.max_hp = profile.get("maxHp")
            if "🎗" in player.nickname:  # Отключено в связи с эмодзи в никах
                pass
            else:
                guild_emoji = profile.get("guild_emoji")
                if guild_emoji is None:
                    guild_emoji = ""
                if player.nickname in ("{}[{}]".format(guild_emoji, player.guild_tag) if player.guild_tag is not None
                                       else "") + profile.get("userName"):
                    pass
                else:
                    new_nickname = ("{}[{}]".format(guild_emoji, player.guild_tag) if player.guild_tag is not None
                                       else "") + profile.get("userName")
                    if new_nickname in player.nickname:
                        pass
                    else:
                        player.nickname = new_nickname
                    # player.nickname = ("[{}]".format(player.guild_tag) if player.guild_tag is not None else
                    #                    "") + profile.get("userName")
            player.last_updated = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)

            player.update_to_database()

            mobs_link = player.api_info.get("mobs_link")
            if mobs_link is not None:
                logging.info("Updating mobs message...")
                from castle_files.bin.mobs import update_mobs_messages_by_link
                update_mobs_messages_by_link(mobs_link, force_update=True)
                player.api_info.pop("mobs_link")
                player.update()
                # Обновление сообщения с мобами
                pass
        except Exception:
            logging.error(traceback.format_exc())

    def on_gear_info(self, channel, method, header, body):
        payload = body.get("payload")
        player_id = payload.get("userId")
        player = Player.get_player(player_id, notify_on_error=False, new_cursor=self.cursor)
        if body.get("result") != "Ok":
            logging.error("error while requesting gear info, {}".format(body))
            if body.get("result") == "Forbidden":
                try:
                    player.api_info.get("access", []).remove("gear")
                    player.update()
                except ValueError:
                    pass
                except Exception:
                    logging.error("Can not retrieve gear access for Forbidden result: {}".format(traceback.format_exc()))
            return
        try:
            # print(json.dumps(body, sort_keys=1, indent=4, ensure_ascii=False))
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
                    # logging.warning("Equipment with name {} is None".format(name))
                    continue
                attack = item.get("atk") or 0
                defense = item.get("def") or 0
                quality = Equipment.quality.get(item.get("quality"))
                condition = item.get("condition")
                eq.name, eq.attack, eq.defense, eq.quality, eq.condition = name, attack, defense, quality, condition
                player_equipment.update({eq.place: eq})
            player.equipment = player_equipment
            player.update()
        except Exception:
            logging.error(traceback.format_exc())


    def get_stock_change_text(self, old_stock, new_stock):
        response = "📦Изменения в стоке:\n"
        prices = self.api_info.get("prices") or {}
        changes = {}
        for code, count in list(old_stock.items()):
            new_count = new_stock.get(code) or 0
            change = new_count - count
            if change != 0:
                changes.update({code: change})
        for code, count in list(new_stock.items()):
            if code in changes:
                continue
            old_count = old_stock.get(code) or 0
            change = count - old_count
            if change != 0:
                changes.update({code: change})
        response_added, response_lost = "<b>➕Приобретено:</b>\n", "\n<b>➖Потеряно:</b>\n"
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
        response_added += "<b>В сумме:</b> <code>{}</code>💰\n\n".format(gold_added)
        response_lost += "<b>В сумме:</b> <code>{}</code>💰\n\n".format(gold_lost)
        response += (response_added if gold_added > 0 else "") + (response_lost if gold_lost < 0 else "")
        response += "<b>Всего:</b> <code>{}</code>💰\n".format(gold_added + gold_lost)
        return response

    def on_stock_info(self, channel, method, header, body):
        try:
            if body.get("result") != "Ok":
                logging.error("error while requesting stock info, {}".format(body))
                return
            # print(json.dumps(body, sort_keys=1, indent=4, ensure_ascii=False))
            payload = body.get("payload")
            player_id = payload.get("userId")
            player = Player.get_player(player_id, notify_on_error=False, new_cursor=self.cursor)
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
            player.api_info.update({"stock_update": datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None).strftime(
                "%d/%m/%y %H:%M")})
            player.update()
            if player.settings is None:
                send_change = True
            else:
                send_change = player.settings.get("stock_change")
                if send_change is None:
                    send_change = True
            # logging.error("Got stock through api for {}, {} {}"
            #               "".format(player.nickname, player.api_info.get("change_stock_send"), send_change))
            if player.api_info.get("change_stock_send") and send_change is True:
                # Уведомление игрока о изменении в стоке
                response = self.get_stock_change_text(old_stock, player.stock)
                self.bot.send_message(chat_id=player.id, text=response, parse_mode='HTML')
                player.api_info.pop("change_stock_send")
                player.update()

            # print(player.stock)
        except Exception:
            logging.error(traceback.format_exc())

    def on_guild_info(self, channel, method, header, body):
        try:
            payload = body.get("payload")
            player_id = payload.get("userId")
            player = Player.get_player(player_id, notify_on_error=False)
            guild = Guild.get_guild(player.guild)
            if body.get("result") != "Ok":
                logging.error("error while requesting guild info, {}".format(body))
                if body.get("result") == "Forbidden":
                    try:
                        guild.api_info.get("api_players", []).remove(player_id)
                        guild.update_to_database(need_order_recashe=False)
                    except ValueError:
                        pass
                    except Exception:
                        logging.error("Can not remove guild api access: {}".format(traceback.format_exc()))
                return
            # print(body)
            # print(json.dumps(body, sort_keys=1, indent=4, ensure_ascii=False))
            name, glory, lvl, members, stock_size, stock_limit, \
                tag, castle = payload.get("name"), payload.get("glory"), payload.get("level"), \
                payload.get("members"),  payload.get("stockSize"), payload.get("stockLimit"), \
                payload.get("tag"), payload.get("castle")
            got_stock = payload.get("stock")
            codes = payload.get("itemCodes")
            stock, equipment_temp, equipment = {}, {}, []
            for i_name, count in list(got_stock.items()):
                code = get_item_code_by_name(i_name)
                eq = get_equipment_by_name(i_name)
                if eq is not None:
                    lst = equipment_temp.get(eq.name)
                    if lst is None:
                        lst = []
                        equipment_temp.update({eq.name: lst})
                    for i in range(count):
                        lst.append(copy.deepcopy(eq))
                stock.update({code or i_name: count})
            stock = {k: stock[k] for k in sorted(stock, key=stock_sort_comparator)}
            self.__set_guild_equipment_codes(codes, equipment_temp, equipment)
            player = Player.get_player(player_id, notify_on_error=False)
            if player is None or player.guild is None:
                logging.warning("Received guild info, but player is None (or guild) for id {}".format(player_id))
                return
            if guild is None or guild.tag != tag:
                logging.warning("Received guild info, but guild is None or not euqal for"
                                " {} (@{})".format(player.nickname, player.username))
                return
            old_stock, old_glory, change_send = guild.api_info.get("stock") or {}, guild.api_info.get("glory") or 0, \
                                                guild.api_info.get("change_stock_send") or False
            if change_send:
                self.guild_changes.update({guild.tag: glory - old_glory})
                if self.guild_changes_work is None:
                    self.guild_changes_work = threading.Timer(60, self.send_guild_changes_to_mid)
                    self.guild_changes_work.start()
                response = "Итоги битвы {}<b>{}</b>\n".format(guild.castle, guild.tag)
                response += "<b>🎖Glory:</b> <code>{}</code>\n\n".format(glory - old_glory)
                response += self.get_stock_change_text(old_stock, stock)
                attack, defense, exp, gold, total_stock = guild.count_battle_stats()
                response += "\nПредыдущая битва:\n<code>Атака: {:>5}⚔\nЗащита:{:>5}🛡\nОпыт: {:>6}🔥\nЗолото:{:>5}💰\n" \
                            "Сток:  {:>5}📦</code>\n".format(attack, defense, exp, gold, total_stock)
                self.bot.send_message(chat_id=guild.chat_id, text=response, parse_mode='HTML')
                guild.api_info.pop("change_stock_send")
                guild.update_to_database(need_order_recashe=False)

            guild.name = name
            api_players = guild.api_info.get("api_players")
            if api_players is None:
                api_players = []
                guild.api_info.update({"api_players": api_players})
            if player_id not in api_players:
                api_players.append(player_id)
            guild.api_info.update({"stock": stock, "glory": glory, "lvl": lvl, "members": members,
                                   "stock_size": stock_size, "stock_limit": stock_limit, "equipment": equipment})
            guild.castle = castle
            guild.last_updated = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
            guild.update_to_database(need_order_recashe=False)
        except Exception:
            logging.error(traceback.format_exc())

    @staticmethod
    def __set_guild_equipment_codes(codes: dict, equipment_temp: dict, equipment: list):
        for code, name in list(codes.items()):
            lst: list = equipment_temp.get(name)
            if not lst:
                continue
            eq: Equipment = lst.pop()
            eq.set_code(code)
            if eq.type not in ["k", "r"]:
                equipment.append(eq.to_json())


    #

    def send_guild_changes_to_mid(self):
        guild_changes = {k: v for k, v in sorted(list(self.guild_changes.items()), key=lambda x: x[1], reverse=True)}
        logging.error(guild_changes)
        self.guild_changes_work = None
        self.guild_changes.clear()
        response = "Изменения глори по гильдиям:\n"
        for tag, glory_change in list(guild_changes.items()):
            guild = Guild.get_guild(guild_tag=tag, new_cursor=True)
            response += "{}<b>{}</b> 🎖:<code>{:>3}</code>\n".format(guild.castle, guild.tag, glory_change)
        self.bot.send_message(chat_id=MID_CHAT_ID, text=response, parse_mode='HTML')

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
        player.api_info.update({"operation": operation})
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
        logging.debug("published")

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
        # properties = pika.BasicProperties(app_id='cactiw_castle_skalen', content_type='application/json')
        try:
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
            # print(self.connected, self.channel)
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
        # self.connection.ioloop.stop()
        # self.connect()
        # self.connection.ioloop.start()
        try:
            self.stop()
        except Exception:
            logger.warning("Failed to stop CW API in reconnect: {}".format(traceback.format_exc()))
        self.try_reconnect_forever()

    def try_reconnect_forever(self):
        WAIT_BEFORE_RETRY_SECONDS = 30
        try:
            while True:
                try:
                    self.start()
                except Exception:
                    pass
                    try:
                        self.stop()
                    except Exception:
                        pass
                    logger.info("Failed to reconnect CW API, retrying in {} seconds".format(WAIT_BEFORE_RETRY_SECONDS))
                    time.sleep(WAIT_BEFORE_RETRY_SECONDS)
        except KeyboardInterrupt:
            return
        except Exception:
            logger.error(traceback.format_exc())


    def start(self):
        logger.warning("Starting the API")
        self.active = True
        self.conn = Conn(psql_creditals)
        self.conn.start()
        self.cursor = self.conn.cursor()
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
            self.conn.close()
            # Loop until we're fully closed, will stop on its own
            self.connection.ioloop.start()

    def stop(self):
        print("closing connection")
        logging.error("Sent {} requests, got {} responses".format(self.sent, self.got_responses))
        self.active = False
        for i in range(self.num_workers):
            self.requests_queue.put(None)
        if self.consumer_tags:
            for tag in self.consumer_tags:
                self.in_channel.basic_cancel(tag, self.__on_cancel)
        self.channel.close()
        self.in_channel.close()
        self.connection.close()
        self.conn.close()
        print("starting loop")
        self.connection.ioloop.stop()
        print("loop ended")
        for worker in self.workers:
            worker.join()
