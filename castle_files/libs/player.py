"""
В этом модуле объявляется класс Player - класс, хранящий все данных о конкретном игроке.
"""
from castle_files.work_materials.globals import conn, dispatcher
from castle_files.work_materials.equipment_constants import get_equipment_by_code
from castle_files.bin.service_functions import count_week_by_battle_id, count_battle_id

from psycopg2 import ProgrammingError
import logging
import json
import time

from multiprocessing import Queue

players = {}
players_need_update = Queue()

cursor = conn.cursor()
classes_list = ['Alchemist', 'Blacksmith', 'Collector', 'Ranger', 'Knight', 'Sentinel']


class Player:
    def __init__(self, player_id, username, nickname, guild_tag, guild, lvl, attack, defense, stamina, pet, equipment,
                 game_class=None, class_skill_lvl=None, castle=None, last_updated=None, reputation=0, created=None,
                 status=None, guild_history=None, exp=None, api_info=None, stock=None, settings=None):
        self.id = player_id
        self.username = username
        self.nickname = nickname
        self.guild_tag = guild_tag
        self.guild = guild
        self.lvl = lvl
        self.attack = attack
        self.defense = defense
        self.stamina = stamina
        self.pet = pet
        self.equipment = equipment.copy()
        self.game_class = game_class
        self.class_skill_lvl = class_skill_lvl
        self.last_access_time = time.time()
        self.castle = castle
        self.last_updated = last_updated
        self.reputation = reputation
        self.created = created
        self.status = status
        self.guild_history = guild_history
        self.exp = exp
        self.api_info = api_info
        self.stock = stock
        self.settings = settings or {}

        self.__current_reports_count = -1
        self.__previous_reports_count = -1
        self.__total_reports_count = -1
        self.__reports_counted_battle_id = -1

    # Метод для подсчёта количества репортов за эту, прошлую неделю и всего
    def count_reports(self):
        self.__current_reports_count, self.__previous_reports_count, self.__total_reports_count = 0, 0, 0
        request = "select battle_id from reports where player_id = %s and exp != 0"
        cursor.execute(request, (self.id,))
        row = cursor.fetchone()
        self.__reports_counted_battle_id = count_battle_id(None)
        current_week = count_week_by_battle_id(self.__reports_counted_battle_id)
        while row is not None:
            week = count_week_by_battle_id(row[0])
            if week == current_week:
                self.__current_reports_count += 1
            elif week == current_week - 1:
                self.__previous_reports_count += 1
            self.__total_reports_count += 1
            row = cursor.fetchone()

    # Возвращает список из трёх чисел - число репортов за эту неделю, за прошлую и всего.
    # Если до этого подсчёт не выполнялся, то производит его
    def get_reports_count(self):
        if count_battle_id(None) != self.__reports_counted_battle_id or \
                not (self.__total_reports_count >= 0 and self.__current_reports_count >= 0 and
                     self.__previous_reports_count >= 0):
            self.count_reports()
        return [self.__current_reports_count, self.__previous_reports_count, self.__total_reports_count]

    """
    Метод получения игрока по его id. Сначала проверяется, находится ли игрок в словаре players, то есть был ли
    он загружен из БД ранее. Если да, то он возвращается, ежели нет, то происходит его загрузка из БД
    """
    @staticmethod
    def get_player(player_id=None, player_in_game_id=None, notify_on_error=True, new_cursor=None):
        if new_cursor is not None:
            cur_cursor = new_cursor
        else:
            cur_cursor = cursor
        if player_id is not None:
            player = players.get(player_id)
            if player is not None:
                # Игрок уже загружен из базы данных
                player.last_access_time = time.time()
                return player
            arg = player_id
        else:
            arg = player_in_game_id
        # Загрузка игрока из базы данных
        request = "select username, nickname, guild_tag, guild, lvl, attack, defense, stamina, pet, equipment, " \
                  "game_class, class_skill_lvl, castle, last_updated, reputation, created, status, guild_history, " \
                  "exp, api_info, stock, id, settings from players where "
        if player_id is not None:
            request += "id = %s"
        elif player_in_game_id is not None:
            request += "api_info ->> 'in_game_id' = %s"
        cur_cursor.execute(request, (arg,))
        try:
            row = cur_cursor.fetchone()
        except ProgrammingError:
            return None
        if row is None:
            if notify_on_error and player_id is not None:
                dispatcher.bot.send_message(chat_id=player_id,
                                            text="Вы не зарегистрированы. Для регистрации необходимо "
                                                 "прислать ответ @ChatWarsBot на команду /hero")
            return None
        print(row)
        username, nickname, guild_tag, guild, lvl, attack, defense, stamina, pet, equipment, game_class, \
            class_skill_lvl, castle, last_updated, reputation, created, status, guild_history, exp, api_info, \
            stock, player_id, settings = row
        if api_info is None:
            api_info = {}
        eq = {}
        for place, eq_json in list(equipment.items()):
            equipment_list = json.loads(eq_json)
            current = get_equipment_by_code(equipment_list.get("code"))
            if current is None:
                logging.warning("Equipment is None for code {} in get_player".format(eq_json.get("code")))
                continue
            current.name = equipment_list.get("name")
            current.attack = equipment_list.get("attack")
            current.defense = equipment_list.get("defense")
            eq.update({place: current})
        player = Player(player_id, username, nickname, guild_tag, guild, lvl, attack, defense, stamina, pet, eq,
                        game_class, class_skill_lvl=class_skill_lvl, castle=castle, last_updated=last_updated,
                        reputation=reputation, created=created, status=status, guild_history=guild_history, exp=exp,
                        api_info=api_info, stock=stock, settings=settings)
        players.update({player_id: player})  # Кладу игрока в память для дальнейшего ускоренного использования
        return player

    # Преобразование экипировки игрока в готовый для записи в БД json-объект
    def equipment_to_json(self):
        eq_to_db = {}
        equipment_list = list(self.equipment.values())
        if equipment_list:
            for eq in equipment_list:
                if eq is None:
                    # Слот экипировки свободен
                    continue
                eq_to_db.update({eq.place: eq.to_json()})
        eq_to_db = json.dumps(eq_to_db)
        return eq_to_db

    def reload_from_database(self):
        if self.id in players:
            players.pop(self.id)
        return Player.get_player(self.id)

    # Метод для первичного внесения данных о игроке в БД
    def insert_into_database(self):
        request = "insert into players(id, username, nickname, guild_tag, guild, lvl, attack, defense, stamina, pet, " \
                  "equipment, castle, last_updated, reputation, created, status, guild_history, exp, api_info, stock) "\
                  "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

        eq_to_db = self.equipment_to_json()
        print(self.id, self.username, self.nickname, self.guild_tag, self.guild, self.lvl,
              self.attack, self.defense, self.stamina, self.pet, eq_to_db)
        cursor.execute(request, (self.id, self.username, self.nickname, self.guild_tag, self.guild, self.lvl,
                                 self.attack, self.defense, self.stamina, self.pet, eq_to_db, self.castle,
                                 self.last_updated, self.reputation, self.created, self.status, self.guild_history,
                                 self.exp, json.dumps(self.api_info), json.dumps(self.stock)))
        players.update({self.id: self})

    # Метод для обновления уже существующей информации о игроке в БД
    def update_to_database(self):
        request = "update players set username = %s, nickname = %s, guild_tag = %s, guild = %s, lvl= %s, " \
                  "attack = %s, defense = %s, stamina = %s, pet = %s, equipment = %s, game_class = %s, " \
                  "class_skill_lvl = %s, castle = %s, last_updated = %s, reputation = %s, created = %s, status = %s, " \
                  "guild_history = %s, exp = %s, api_info = %s, stock = %s, settings = %s " \
                  "where id = %s"
        eq_to_db = self.equipment_to_json()

        # print(self.id, self.username, self.nickname, self.guild_tag, self.guild, self.lvl,
        #       self.attack, self.defense, self.stamina, self.pet, eq_to_db, self.game_class, self.class_skill_lvl)

        cursor.execute(request, (self.username, self.nickname, self.guild_tag, self.guild, self.lvl, self.attack,
                                 self.defense, self.stamina, self.pet, eq_to_db, self.game_class, self.class_skill_lvl,
                                 self.castle, self.last_updated, self.reputation, self.created, self.status,
                                 self.guild_history, self.exp, json.dumps(self.api_info), json.dumps(self.stock),
                                 json.dumps(self.settings), self.id))
        return 0

    def update(self):
        self.update_to_database()
        # players_need_update.put(self)
