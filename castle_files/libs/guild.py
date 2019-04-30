"""
Этот модуль содержит класс Гильдия и методы работы с ней, в том числе и с БД.
"""
from castle_files.work_materials.globals import conn

from castle_files.libs.player import Player
from globals import update_request_queue

import logging
import traceback
import time

# Словарь, пара элементов: { id гильдии: класс Guild } )
# Гильдии записываются в словарь при выборке из базы данных, хранятся примерно 30 минут (?), потом выгружаются
guilds = {}

cursor = conn.cursor()


# Гильдия, содержит открытые поля - id в базе данных, тэг, список айдишников(!) членов гильдии,
class Guild:
    def __init__(self, guild_id, tag, name, members, commander_id, assistants, division, chat_id, chat_name, invite_link,
                 orders_enabled, pin_enabled, disable_notification):
        self.id = guild_id
        self.tag = tag
        self.name = name
        self.members = members
        if not self.members:
            self.members = []
        self.members_count = len(self.members)
        self.commander_id = commander_id
        self.assistants = assistants
        self.division = division
        self.chat_id = chat_id
        self.chat_name = chat_name
        self.invite_link = invite_link
        self.orders_enabled = orders_enabled
        self.pin_enabled = pin_enabled
        self.disable_notification = disable_notification

        # Приватные поля, равные общей атаке и дефу гильдии,
        # подсчёт проиводится только при необходимости в соответствующих методах
        self.__attack = None
        self.__defense = None

        # Поле, которое хранит последнее время обращения. Если оно отличается от текущего более, чем на n минут,
        # то гильдия выгружается из памяти
        self.last_access_time = time.time()

    # Метод для получения общей атаки гильдии. Если она не посчитана, то происходит её рассчёт
    def get_attack(self):
        if self.__attack is None:
            self.calculate_attack_and_defense()
        return self.__attack

    # Метод для получения общего дефа гильдии.
    def get_defense(self):
        if self.__defense is None:
            self.calculate_attack_and_defense()
        return self.__defense

    # Рассчёт общего количества атаки и дефа гильдии
    def calculate_attack_and_defense(self):
        self.__attack = 0
        self.__defense = 0
        for player_id in self.members:
            player = Player.get_player(player_id)
            if player is None:
                logging.warning("Player in guild is None, guild = {}, player_id = {}".format(self.tag, player_id))
                continue
            self.__attack += player.attack
            self.__defense += player.defense
        return

    def sort_players_by_exp(self):
        try:
            self.members.sort(key=lambda player_id: Player.get_player(player_id).lvl)
            self.update_to_database()
        except (TypeError, AttributeError, ValueError):
            logging.error(traceback.format_exc())

    # Метод для добавления игрока в гильдию
    def add_player(self, player_to_add):
        if self.members is None:
            self.members = []
        if player_to_add.id not in self.members:
            self.members.append(player_to_add.id)
        self.members_count = len(self.members)

        player_to_add.guild = self.id
        player_to_add.guild_tag = self.tag

        player_to_add.update()
        self.update_to_database()

        if self.__attack is not None and self.__defense is not None:
            self.__attack += player_to_add.attack
            self.__defense += player_to_add.defense

    def delete_player(self, player):
        if player.id in self.members:
            self.members.remove(player.id)
        self.members_count = len(self.members)

        player.guild = None
        player.update()
        self.update_to_database()
        if self.__attack is not None and self.__defense is not None:
            self.__attack -= player.attack
            self.__defense -= player.defense

    # Метод получения гильдии из БД
    @staticmethod
    def get_guild(guild_id=None, guild_tag=None):
        guild = None
        if guild_tag is not None:
            for guild_id, current_guild in list(guilds.items()):
                if current_guild.tag == guild_tag:
                    guild = current_guild
                    break
        elif guild_id is not None:
            guild = guilds.get(guild_id)
        if guild is not None:
            guild.last_access_time = time.time()
            return guild
        request = "select guild_tag, guild_id, guild_name, chat_id, members, commander_id, division, chat_name, " \
                  "invite_link, orders_enabled, pin_enabled, disable_notification from guilds "
        if guild_tag is not None:
            request += "where guild_tag = %s"
            cursor.execute(request, (guild_tag,))
        elif guild_id is not None:
            request += "where guild_id = %s"
            cursor.execute(request, (guild_id,))
        else:
            return None
        row = cursor.fetchone()
        if row is None:
            return None
        guild_tag, guild_id, name, chat_id, members, commander_id, division, chat_name, invite_link, orders_enabled, \
            pin_enabled, disable_notification = row
        assistants = []
        # Инициализация новой гильдии
        guild = Guild(guild_id, guild_tag, name, members, commander_id, assistants, division, chat_id, chat_name, invite_link,
                      orders_enabled, pin_enabled, disable_notification)

        # Сохранение гильдии в словарь для дальнейшего быстрого доступа
        guilds.update({guild.id: guild})
        return guild

    # Метод для обновления информации о гильдии в БД
    def update_to_database(self):
        request = "update guilds set guild_name = %s, members = %s, commander_id = %s, division = %s, chat_id = %s, " \
                  "chat_name = %s, invite_link = %s, orders_enabled = %s, pin_enabled = %s,disable_notification = %s " \
                  "where guild_tag = %s"
        try:
            cursor.execute(request, (self.name, self.members, self.commander_id, self.division, self.chat_id,
                                     self.chat_name, self.invite_link, self.orders_enabled, self.pin_enabled,
                                     self.disable_notification, self.tag))
        except Exception:
            logging.error(traceback.format_exc())
            return -1
        update_request_queue.put(self.id)
        return 0

    def create_guild(self):
        request = "insert into guilds(guild_tag) values (%s) returning guild_id"
        cursor.execute(request, (self.tag,))
        row = cursor.fetchone()
        self.id = row[0]
        return self
