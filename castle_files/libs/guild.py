"""
Этот модуль содержит класс Гильдия и методы работы с ней, в том числе и с БД.
"""
from castle_files.work_materials.globals import conn, moscow_tz

from castle_files.libs.player import Player
from globals import update_request_queue

import logging
import traceback
import time
import json
import datetime

MAX_GUILD_HISTORY_LENGTH = 10

# Словарь, пара элементов: { id гильдии: класс Guild } )
# Гильдии записываются в словарь при выборке из базы данных, хранятся примерно 30 минут (?), потом выгружаются
guilds = {}

cursor = conn.cursor()


# Гильдия, содержит открытые поля - id в базе данных, тэг, список айдишников(!) членов гильдии,
class Guild:
    guild_ids = []

    def __init__(self, guild_id, tag, name, members, commander_id, assistants, division, chat_id, chat_name, invite_link,
                 orders_enabled, pin_enabled, disable_notification, settings=None, api_info=None, mailing_enabled=True,
                 last_updated=None):
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
        self.settings = settings
        self.api_info = api_info if api_info is not None else {}
        self.mailing_enabled = mailing_enabled
        self.last_updated = last_updated  # Последнее обновление ЧЕРЕЗ АПИ

        # Приватные поля, равные общей атаке и дефу гильдии,
        # подсчёт проиводится только при необходимости в соответствующих методах
        self.__attack = None
        self.__defense = None

        self.__report_count = 0
        self.__counted_attack = 0
        self.__counted_defense = 0
        self.__counted_gold = 0

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

    def clear_counted_reports(self):
        self.__report_count = 0
        self.__counted_attack = 0
        self.__counted_defense = 0
        self.__counted_gold = 0

    def add_count_report(self, attack, defense, gold):
        self.__report_count += 1
        self.__counted_attack += attack
        self.__counted_defense += defense
        self.__counted_gold += gold

    def get_counted_report_values(self):
        return [self.__report_count, self.__counted_attack, self.__counted_defense, self.__counted_gold]

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
            self.members.sort(key=lambda player_id: Player.get_player(player_id).lvl, reverse=True)
            self.update_to_database(need_order_recashe=False)
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

        if player_to_add.guild_history is None or not player_to_add.guild_history:
            player_to_add.guild_history = []
            player_to_add.guild_history.append(self.id)
        elif player_to_add.guild_history[-1] != self.id:
            if len(player_to_add.guild_history) > MAX_GUILD_HISTORY_LENGTH:
                player_to_add.guild_history.pop()
            player_to_add.guild_history.insert(0, self.id)

        player_to_add.update()
        self.sort_players_by_exp()
        self.update_to_database()

        if self.__attack is not None and self.__defense is not None:
            self.__attack += player_to_add.attack
            self.__defense += player_to_add.defense

    # Удаление игрока из гильдии
    def delete_player(self, player):
        if player.id in self.members:
            self.members.remove(player.id)
        self.members_count = len(self.members)
        if player.id in self.assistants:
            self.assistants.remove(player.id)

        player.guild = None
        player.update()
        self.update_to_database()
        if self.__attack is not None and self.__defense is not None:
            self.__attack -= player.attack
            self.__defense -= player.defense

    # Метод для проверки, является ли игрок командиром или замом гильдии
    def check_high_access(self, player_id):
        return player_id == self.commander_id or player_id in self.assistants

    # Метод получения гильдии из БД
    @staticmethod
    def get_guild(guild_id=None, guild_tag=None, new_cursor=False):
        """
        if new_cursor:
            cur_cursor = conn.cursor()
        else:
            cur_cursor = cursor
        """
        cur_cursor = conn.cursor()
        guild = None
        if guild_tag is not None:
            for guild_id, current_guild in list(guilds.items()):
                if current_guild.tag == guild_tag:
                    guild = current_guild
                    break
        elif guild_id is not None:
            guild = guilds.get(guild_id)
        if guild is not None:
            # Гильдия нашлась в кэше
            guild.last_access_time = time.time()
            return guild
        # Гильдии нет в кэше, получение гильдии из базы данных
        request = "select guild_tag, guild_id, guild_name, chat_id, members, commander_id, division, chat_name, " \
                  "invite_link, orders_enabled, pin_enabled, disable_notification, assistants, settings, api_info, " \
                  "mailing_enabled, last_updated" \
                  " from guilds "
        if guild_tag is not None:
            request += "where lower(guild_tag) = %s"
            cur_cursor.execute(request, (guild_tag.lower(),))
        elif guild_id is not None:
            request += "where guild_id = %s"
            cur_cursor.execute(request, (guild_id,))
        else:
            return None
        row = cur_cursor.fetchone()
        if row is None:
            return None
        guild_tag, guild_id, name, chat_id, members, commander_id, division, chat_name, invite_link, orders_enabled, \
            pin_enabled, disable_notification, assistants, settings, api_info, mailing_enabled, last_updated = row
        if assistants is None:
            assistants = []
        # Инициализация новой гильдии
        guild = Guild(guild_id, guild_tag, name, members, commander_id, assistants, division, chat_id, chat_name,
                      invite_link, orders_enabled, pin_enabled, disable_notification, settings, api_info,
                      mailing_enabled, last_updated)

        # Сохранение гильдии в словарь для дальнейшего быстрого доступа
        guilds.update({guild.id: guild})
        guild.last_access_time = time.time()
        cur_cursor.close()
        return guild

    @staticmethod
    def get_academy():
        return Guild.get_guild(guild_tag="АКАДЕМИЯ")

    def is_academy(self):
        return self.tag == "АКАДЕМИЯ"

    @staticmethod
    def fill_guild_ids():
        Guild.guild_ids.clear()
        request = "select guild_id from guilds order by guild_id asc"
        cursor.execute(request)
        row = cursor.fetchone()
        while row is not None:
            Guild.guild_ids.append(row[0])
            row = cursor.fetchone()

    # Метод для обновления информации о гильдии в БД
    def update_to_database(self, need_order_recashe=True):
        cursor = conn.cursor()
        request = "update guilds set guild_name = %s, members = %s, commander_id = %s, division = %s, chat_id = %s, " \
                  "chat_name = %s, invite_link = %s, orders_enabled = %s, pin_enabled = %s,disable_notification = %s, " \
                  "assistants = %s, settings = %s, api_info = %s, mailing_enabled = %s, last_updated = %s " \
                  "where guild_tag = %s"
        try:
            cursor.execute(request, (self.name, self.members, self.commander_id, self.division, self.chat_id,
                                     self.chat_name, self.invite_link, self.orders_enabled, self.pin_enabled,
                                     self.disable_notification, self.assistants, json.dumps(self.settings),
                                     json.dumps(self.api_info), self.mailing_enabled, self.last_updated, self.tag))
        except Exception:
            logging.error(traceback.format_exc())
            return -1
        if need_order_recashe:
            pass
            # update_request_queue.put(["update_guild", self.id])
        cursor.close()
        return 0

    def create_guild(self):
        request = "insert into guilds(guild_tag) values (%s) returning guild_id"
        cursor.execute(request, (self.tag,))
        row = cursor.fetchone()
        self.id = row[0]
        Guild.fill_guild_ids()
        return self

    def delete_guild(self):
        for player_id in self.members:
            player = Player.get_player(player_id)
            if player is None:
                continue
            player.guild = None
            player.update_to_database()
        request = "delete from guilds where guild_id = %s"
        cursor.execute(request, (self.id,))
        guilds.pop(self.id)
