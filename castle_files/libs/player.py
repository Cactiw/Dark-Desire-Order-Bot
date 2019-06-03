"""
В этом модуле объявляется класс Player - класс, хранящий все данных о конкретном игроке.
"""
from castle_files.work_materials.globals import conn, dispatcher
from castle_files.work_materials.equipment_constants import get_equipment_by_code

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
                 game_class=None, class_skill_lvl=None, castle=None, last_updated=None, reputation=0, created=None):
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

    """
    Метод получения игрока по его id. Сначала проверяется, находится ли игрок в словаре players, то есть был ли
    он загружен из БД ранее. Если да, то он возвращается, ежели нет, то происходит его загрузка из БД
    """
    @staticmethod
    def get_player(player_id, notify_on_error=True):
        player = players.get(player_id)
        if player is not None:
            # Игрок уже загружен из базы данных
            player.last_access_time = time.time()
            return player
        # Загрузка игрока из базы данных
        request = "select username, nickname, guild_tag, guild, lvl, attack, defense, stamina, pet, equipment, " \
                  "game_class, class_skill_lvl, castle, last_updated, reputation, created from players where id = %s"
        cursor.execute(request, (player_id,))
        try:
            row = cursor.fetchone()
        except ProgrammingError:
            return None
        if row is None:
            if notify_on_error:
                dispatcher.bot.send_message(chat_id=player_id,
                                            text="Вы не зарегистрированы. Для регистрации необходимо "
                                                 "прислать ответ @ChatWarsBot на команду /hero")
            return None
        username, nickname, guild_tag, guild, lvl, attack, defense, stamina, pet, equipment, game_class, \
            class_skill_lvl, castle, last_updated, reputation, created = row
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
                        reputation=reputation, created=created)
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
                  "equipment, castle, last_updated, reputation, created) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                  "%s, %s, %s, %s, %s, %s)"

        eq_to_db = self.equipment_to_json()
        print(self.id, self.username, self.nickname, self.guild_tag, self.guild, self.lvl,
              self.attack, self.defense, self.stamina, self.pet, eq_to_db)
        cursor.execute(request, (self.id, self.username, self.nickname, self.guild_tag, self.guild, self.lvl,
                                 self.attack, self.defense, self.stamina, self.pet, eq_to_db, self.castle,
                                 self.last_updated, self.reputation, self.created))
        players.update({self.id: self})

    # Метод для обновления уже существующей информации о игроке в БД
    def update_to_database(self):
        request = "update players set username = %s, nickname = %s, guild_tag = %s, guild = %s, lvl= %s, " \
                  "attack = %s, defense = %s, stamina = %s, pet = %s, equipment = %s, game_class = %s, " \
                  "class_skill_lvl = %s, castle = %s, last_updated = %s, reputation = %s, created = %s where id = %s"
        eq_to_db = self.equipment_to_json()

        print(self.id, self.username, self.nickname, self.guild_tag, self.guild, self.lvl,
              self.attack, self.defense, self.stamina, self.pet, eq_to_db, self.game_class, self.class_skill_lvl)

        cursor.execute(request, (self.username, self.nickname, self.guild_tag, self.guild, self.lvl, self.attack,
                                 self.defense, self.stamina, self.pet, eq_to_db, self.game_class, self.class_skill_lvl,
                                 self.castle, self.last_updated, self.reputation, self.created, self.id))
        return 0

    def update(self):
        self.update_to_database()
        # players_need_update.put(self)
