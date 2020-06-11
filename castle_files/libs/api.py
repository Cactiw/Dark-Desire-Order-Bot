"""
Библиотека для работы с АПИ ЧВ3
"""

from castle_files.work_materials.globals import dispatcher, classes_to_emoji_inverted, moscow_tz, Conn, psql_creditals,\
    MID_CHAT_ID, SUPER_ADMIN_ID
from globals import master_pid
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
import re
import kombu
import copy
import kafka
import os
import signal

from multiprocessing import Queue
from kombu.mixins import ConsumerMixin

logger = logging.getLogger("API")
logger.setLevel(logging.INFO)

print(threading.current_thread().ident)


class CW3API:
    MAX_REQUESTS_PER_SECOND = 30
    WAIT_BEFORE_RETRY_CONNECTION_SECONDS = 30
    api_info = {}

    def __init__(self, cwuser, cwpass, workers=1):
        # TODO Разобраться с несколькими работниками (нельзя использовать 1 канал на всех)
        self.__lock = threading.Lock()
        self.lock = threading.Condition(self.__lock)
        self.cwuser = cwuser
        self.cwpass = cwpass
        self.url = f'amqps://{cwuser}:{cwpass}@api.chtwrs.com:5673'
        self.connected = False  # Соединение активно в данный момент
        self.connecting = False  # True, если соединение не установлено, но пытается установиться в данный момент
        self.active = True  # True при запуске, и False в самом конце, если self.active == True и
        #                   # self.connected == False, то это значит, что соединение оборвалось само.

        self.kafka_active = False

        self.guild_changes = {}
        self.guild_changes_work = None

        self.conn = None
        self.cursor = None
        self.connection = None
        self.producer = None
        self.bot = dispatcher.bot
        self.consumer_tags = []
        self.num_workers = workers  # Число работников, работающих над отправкой запросов
        self.workers = []  # Сами работники
        self.requests_queue = Queue()  # Очередь с запросами (Dict)
        self.__requests_per_second = 0  # Счётчик запросов в секунду

        self.EXCHANGE = "{}_ex".format(cwuser)
        self.ROUTING_KEY = "{}_o".format(cwuser)
        self.INBOUND = "{}_i".format(self.cwuser)

        self.exchange = kombu.Exchange(self.EXCHANGE)
        self.inbound_queue = kombu.Queue(self.INBOUND)

        self.kafka_consumer = None

        self.sent = 0
        self.got_responses = 0

        self.callbacks = {
            "createAuthCode": self.on_create_auth_code, "grantToken": self.on_grant_token,
            "requestProfile": self.on_request_profile, "guildInfo": self.on_guild_info,
            "requestGearInfo": self.on_gear_info, "authAdditionalOperation": self.on_request_additional_operation,
            "grantAdditionalOperation": self.on_grant_additional_operational, "requestStock": self.on_stock_info,
            'cw3-deals': self.on_deals,
            # 'cw3-offers': self.on_offers,  # not inplemented
            'cw3-sex_digest': self.on_sex_digest,
            'cw3-yellow_pages': self.on_yellow_pages,
            # 'cw3-au_digest': self.on_au_digest,  # not implemented
        }

    def kafka_work(self):
        for message in self.kafka_consumer:
            try:
                self.callbacks.get(message.topic, lambda x: x)(message.value)
            except Exception:
                logging.error(traceback.format_exc())

            if not self.kafka_active:
                return

    def connect(self):
        self.connecting = True
        self.connection = kombu.Connection(self.url)
        self.connection.connect()
        self.producer = self.connection.Producer(auto_declare=False)
        self.connecting = False

    def on_sex_digest(self, body):
        try:
            prices = {}
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

    def on_yellow_pages(self, body):
        try:
            shops = body
            self.api_info.update({"shops": shops})
            # print(json.dumps(body, sort_keys=1, indent=4, ensure_ascii=False))
        except Exception:
            logging.error(traceback.format_exc())

    def on_deals(self, body):
        try:
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

    def __on_message(self, body, message):
        self.got_responses += 1
        print("Got {}".format(body))
        message.ack()

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
            logging.warning("Callback is None for {}".format(body))
            return
        callback(body)

    def on_create_auth_code(self, body):
        print("in callback", body)
        if body.get("result") != "Ok":
            logging.error("error while creating auth code, {}".format(body))
            return

    def on_grant_token(self, body):
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

    def on_request_additional_operation(self, body):
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

    def on_grant_additional_operational(self, body):
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


    def on_request_profile(self, body):
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
            player.pogs = profile.get("pouches")
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

    def on_gear_info(self, body):
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

    def on_stock_info(self, body):
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

    def on_guild_info(self, body):
        try:
            payload = body.get("payload")
            if payload is None:
                logger.debug("Payload is None in guild info: {}".format(body))
                return
            player_id = payload.get("userId")
            player = Player.get_player(player_id, notify_on_error=False)
            guild = Guild.get_guild(player.guild)
            if body.get("result") != "Ok":
                logging.error("error while requesting guild info, {}".format(body))
                if body.get("result") == "Forbidden":
                    try:
                        self.remove_player_from_guild_access(guild, player)
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
            self.remove_player_from_guild_access(Guild.get_guild(player.guild), player)
            raise RuntimeError
        self.publish_message({
            "token": token,
            "action": "guildInfo"
        })

    def remove_player_from_guild_access(self, guild, player):
        try:
            guild.api_info.get("api_players", []).remove(player.id)
            guild.update_to_database(need_order_recashe=False)
        except ValueError:
            logging.warning("Player not found in guild access list (Api.remove_player_from_guild_access)")

    # Запрос кладётся в очередь запросов
    def publish_message(self, message):
        self.requests_queue.put(message)

    # Голая отправка запроса, без ограничений
    def __publish_message(self, message):
        try:
            self.sent += 1
            return self.producer.publish(
                message,
                retry=True,
                retry_policy={
                    'interval_start': 0,  # First retry immediately,
                    'interval_step': 2,  # then increase by 2s for every retry.
                    'interval_max': 30,  # but don't exceed 30s between retries.
                    'max_retries': 30,  # give up after 30 tries.
                },
                exchange=self.EXCHANGE,
                routing_key=self.ROUTING_KEY)
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
            if self.connection is None or not self.connection.connected:
                for i in range(30):
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

    def start(self):
        self.start_pika()

    def start_kafka(self):
        try:
            if self.kafka_active:
                logging.warning("Kafka already consuming, returning")
                return
            self.kafka_active = True
            self.kafka_consumer = kafka.KafkaConsumer(
                'cw3-offers',
                'cw3-deals',
                'cw3-duels',
                'cw3-sex_digest',
                'cw3-yellow_pages',
                'cw3-au_digest',

                bootstrap_servers=['digest-api.chtwrs.com:9092'],
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='cactiw_cw3_group_id',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            self.start_kafka_consuming()
        except Exception:
            logging.exception("Can not start kafka: {}".format(traceback.format_exc()))
            dispatcher.bot.send_message(chat_id=SUPER_ADMIN_ID, text="Невозможно запустить kafka API")

    def start_pika_consuming(self):
        consumer = CWConsumer(self.connection, self.inbound_queue, self.__on_message)
        self.consumer_tags.append(consumer)
        threading.Thread(target=consumer.run).start()

    def start_kafka_consuming(self):
        time.sleep(10)
        kafka_thread = threading.Thread(target=self.kafka_work)
        kafka_thread.start()

    def start_pika(self):
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
        self.start_pika_consuming()

        self.start_kafka()

    def stop(self):
        self.kafka_active = False
        self.stop_pika()

    def stop_pika(self):
        print("closing connection")
        logging.error("Sent {} requests, got {} responses".format(self.sent, self.got_responses))
        self.active = False

        for consumer in self.consumer_tags:
            consumer.should_stop = True

        self.connection.close()
        self.conn.close()
        print("Stopping loop")

        for i in range(self.num_workers):
            self.requests_queue.put(None)

        for worker in self.workers:
            worker.join(timeout=5)
            if worker.is_alive():
                logger.error("API worker alive after waiting (in .stop())")

        logging.info("API shutdown complete")

        self.clear_api_state()

    def clear_api_state(self):
        logging.info("Clearing api state...")
        self.connection = None
        self.conn = None
        self.producer = None
        self.workers.clear()
        self.consumer_tags.clear()


class CWConsumer(ConsumerMixin):
    def __init__(self, connection, queue, on_message):
        self.connection = connection
        self.queue = queue
        self.on_message = on_message  # Pass method to process the message, accepts message body and message class

    def get_consumers(self, Consumer, channel):
        return [
            Consumer([self.queue], callbacks=[self.on_message], accept=['json'], auto_declare=False),
        ]
