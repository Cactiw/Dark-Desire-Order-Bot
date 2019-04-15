from castle_files.work_materials.globals import cursor
from castle_files.work_materials.equipment_constants import get_equipment_by_code

from psycopg2 import ProgrammingError
import logging

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

    @staticmethod
    def get_player(player_id):
        request = "select username, nickname, guild_tag, guild, lvl, attack, defense, stamina, pet, equipment " \
                  "from players where id = %s"
        cursor.execute(request, (player_id,))
        try:
            row = cursor.fetchone()
        except ProgrammingError:
            return None
        username, nickname, guild_tag, guild, lvl, attack, defense, stamina, pet, equipment = row
        eq = {}
        for place, eq_json in equipment:
            current = get_equipment_by_code(eq_json.get("code"))
            if current is None:
                logging.warning("Equipment is None for code {} in get_player".format(eq_json.get("code")))
                continue
            current.name = eq_json.get("name")
            current.attack = eq_json.get("attack")
            current.defense = eq_json.get("defense")
            eq.update({place: current})
        return Player(player_id, username, nickname, guild_tag, guild, lvl, attack, defense, stamina, pet, eq)

    def insert_into_database(self):
        request = "insert into players(id, username, nickname, guild_tag, guild, lvl, attack, defense, stamina, pet, " \
                  "equipment) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        eq_to_db = {}
        equipment_list = list(self.equipment.values())
        for eq in equipment_list:
            eq_to_db.update({eq.place: eq.to_json()})
        cursor.execute(request, (self.id, self.username, self.nickname, self.guild_tag, self.guild, self.lvl,
                                 self.attack, self.defense, self.stamina, self.pet, eq_to_db))

    def update_to_database(self):
        request = "update players set username = %s, nickname = %s, guild_tag = %s, guild = %s, lvl= %s, " \
                  "attack = %s, defense = %s, stamina = %s, pet = %s, equipment = %s where id = %s"
        cursor.execute(request, (self.username, self.nickname, self.guild_tag, self.guild, self.lvl, self.attack,
                                 self.defense, self.stamina, self.pet, self.equipment, self.id))
        return 0

    def update(self):
        players_need_update.put(self)
