"""
В этом модуле объявляется класс Player - класс, хранящий все данных о конкретном игроке.
"""
from castle_files.work_materials.globals import cursor
from castle_files.work_materials.equipment_constants import get_equipment_by_code

from psycopg2 import ProgrammingError
import logging
import json

from multiprocessing import Queue

players = {}
players_need_update = Queue()


class Player:
    def __init__(self, player_id, username, nickname, guild_tag, guild, lvl, attack, defense, stamina, pet, equipment):
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
        self.equipment = equipment

    """
    Метод получения игрока по его id. Сначала проверяется, находится ли игрок в словаре players, то есть был ли
    он загружен из БД ранее. Если да, то он возвращается, ежели нет, то происходит его загрузка из БД
    """
    @staticmethod
    def get_player(player_id):
        player = players.get(player_id)
        if player is not None:
            # Игрок уже загружен из базы данных
            return player
        # Загрузка игрока из базы данных
        request = "select username, nickname, guild_tag, guild, lvl, attack, defense, stamina, pet, equipment " \
                  "from players where id = %s"
        cursor.execute(request, (player_id,))
        try:
            row = cursor.fetchone()
        except ProgrammingError:
            return None
        if row is None:
            return None
        username, nickname, guild_tag, guild, lvl, attack, defense, stamina, pet, equipment = row
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
        player = Player(player_id, username, nickname, guild_tag, guild, lvl, attack, defense, stamina, pet, eq)
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

    # Метод для первичного внесения данных о игроке в БД
    def insert_into_database(self):
        request = "insert into players(id, username, nickname, guild_tag, guild, lvl, attack, defense, stamina, pet, " \
                  "equipment) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

        eq_to_db = self.equipment_to_json()
        print(self.id, self.username, self.nickname, self.guild_tag, self.guild, self.lvl,
              self.attack, self.defense, self.stamina, self.pet, eq_to_db)
        cursor.execute(request, (self.id, self.username, self.nickname, self.guild_tag, self.guild, self.lvl,
                                 self.attack, self.defense, self.stamina, self.pet, eq_to_db))
        players.update({self.id: self})

    # Метод для обновления уже существующей информации о игроке в БД
    def update_to_database(self):
        request = "update players set username = %s, nickname = %s, guild_tag = %s, guild = %s, lvl= %s, " \
                  "attack = %s, defense = %s, stamina = %s, pet = %s, equipment = %s where id = %s"
        eq_to_db = self.equipment_to_json()

        print(self.id, self.username, self.nickname, self.guild_tag, self.guild, self.lvl,
              self.attack, self.defense, self.stamina, self.pet, eq_to_db)

        cursor.execute(request, (self.username, self.nickname, self.guild_tag, self.guild, self.lvl, self.attack,
                                 self.defense, self.stamina, self.pet, eq_to_db, self.id))
        return 0

    def update(self):
        self.update_to_database()
        # players_need_update.put(self)
