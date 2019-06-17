"""
Библиотека для работы с АПИ ЧВ3
"""

from castle_files.work_materials.globals import dispatcher
from castle_files.libs.player import Player

import threading
import logging
import traceback
import time
import json
import pika

from multiprocessing import Queue

logger = logging.getLogger("API")
logger.setLevel(logging.INFO)


class CW3API:
    MAX_REQUESTS_PER_SECOND = 30

    def __init__(self, cwuser, cwpass, workers=4):
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
        self.bot = dispatcher.bot
        self.consumer_tags = []
        self.num_workers = workers  # Число работников, работающих над отправкой запросов
        self.workers = []  # Сами работники
        self.requests_queue = Queue()  # Очередь с запросами (Dict)
        self.__requests_per_second = 0  # Счётчик запросов в секунду

        self.EXCHANGE = "{}_ex".format(cwuser)
        self.ROUTING_KEY = "{}_o".format(cwuser)
        self.INBOUND = "{}_i".format(self.cwuser)

        self.callbacks = {"createAuthCode": self.on_create_auth_code, "grantToken": self.on_grant_token}

    def connect(self):
        self.connecting = True
        self.connection = pika.SelectConnection(self.parameters, on_open_callback=self.__on_conn_open)

    def __on_conn_open(self, connection):
        logger.warning("Connection opened")
        self.connection = connection
        self.connection.channel(on_open_callback=self.__on_channel_open)

    def __on_channel_open(self, channel):
        self.connected = True
        self.connecting = False
        logger.warning("Channel opened")
        self.channel = channel
        logger.warning("Consuming")
        tag = self.channel.basic_consume(self.INBOUND, self.__on_message)
        self.consumer_tags.append(tag)

    def __on_cancel(self, obj=None):
        print(obj)
        logger.warning("Consumer cancelled")

    def __on_message(self, channel, method, header, body):
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
        player = Player.get_player(player_id, notify_on_error=False)
        if not all([player, token, player_id]):
            logging.error("Value is None: {} {} {}".format(player, token, player_id))
            return
        if player.api_info is None:
            player.api_info = {}
        player.api_info.update({"token": token})
        player.update()
        self.bot.send_message(chat_id=player_id, text="API успешно подключено.")

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

    def get_message(self):
        self.channel.basic_get(self.INBOUND, self.__on_message)

    # Запрос кладётся в очередь запросов
    def publish_message(self, message):
        self.requests_queue.put(message)

    # Голая отправка запроса, без ограничений
    def __publish_message(self, message):
        if not self.connected:
            if self.connecting:
                for i in range(5):
                    time.sleep(1)
                    if self.connected:
                        break
                if not self.connected:
                    raise RuntimeError
        print("sending request", message)
        print(json.dumps(message))
        # properties = pika.BasicProperties(app_id='cactiw_castle_skalen', content_type='application/json')
        return self.channel.basic_publish(exchange=self.EXCHANGE, routing_key=self.ROUTING_KEY,
                                          body=json.dumps(message), properties=None)

    # Функция для отправки запроса с учётом всех ограничений
    def actually_publish_message(self, message):
        try:
            self.lock.acquire()
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
                    self.channel.basic_cancel(self.__on_cancel, tag)
            self.channel.close()
            self.connection.close()
            # Loop until we're fully closed, will stop on its own
            self.connection.ioloop.start()

    def stop(self):
        print("closing connection")
        self.active = False
        for i in range(self.num_workers):
            self.requests_queue.put(None)
        if self.consumer_tags:
            for tag in self.consumer_tags:
                self.channel.basic_cancel(tag, self.__on_cancel)
        self.channel.close()
        self.connection.close()
        print("starting loop")
        self.connection.ioloop.stop()
        print("loop ended")
        for worker in self.workers:
            worker.join()
