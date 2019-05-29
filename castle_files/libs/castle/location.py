"""
В этом файле находятся классы для работы с локациями в виртуальном замке, такие как Казарма, Центральная площадь и тд...
"""
from castle_files.work_materials.globals import conn

from telegram import KeyboardButton, ReplyKeyboardMarkup

import json
import logging

cursor = conn.cursor()
cursor2 = conn.cursor()


# Базовый класс - Локация
class Location:
    def __init__(self, location_id, location_name, enter_text, need_clicks_to_construct=None,
                 state=True, building_process=-1, special_info=None, need_res_to_construct=None):
        self.id = location_id
        self.name = location_name
        self.enter_text = enter_text
        self.need_clicks_to_construct = need_clicks_to_construct
        self.state = state  # True - построено, False - не построено
        self.building_process = building_process  # -1 - стройка не начиналась / завершилась, >=0 - идёт стройка
        self.special_info = special_info
        self.load_location()
        self.need_res_to_construct = need_res_to_construct
        self.child_locations = None

    def under_construction(self):
        return self.state is False and self.building_process >= 0

    def is_constructed(self):
        return self.state

    @staticmethod
    def get_location(location_id):
        return locations.get(location_id)

    @staticmethod
    def get_location_enter_text_by_id(location_id, without_format=False):
        location = Location.get_location(location_id)
        if location is None:
            return None
        if hasattr(location, "update_enter_text"):
            location.update_enter_text()
        if location.special_info is None:
            return location.enter_text
        insert_values = location.special_info.get("enter_text_format_values")
        if insert_values is None or without_format:
            return location.enter_text
        return location.enter_text.format(*insert_values)

    @staticmethod
    def get_id_by_status(status):
        return status_to_location.get(status)

    def load_location(self, other_process=False):
        new_cursor = cursor
        if other_process:
            new_cursor = cursor2
        request = "select state, building_process, special_info from locations where location_id = %s"
        new_cursor.execute(request, (self.id,))
        row = new_cursor.fetchone()
        if row is None:
            return -1
        self.state = row[0]
        self.building_process = row[1]
        self.special_info = row[2]

    def update_location_to_database(self):
        request = "update locations set state = %s, building_process = %s, special_info = %s where location_id = %s"
        cursor.execute(request, (self.state, self.building_process,
                                 json.dumps(self.special_info) if self.special_info is not None else None, self.id))

    def create_location_in_database(self):
        request = "select location_id from locations where location_id = %s"
        cursor.execute(request, (self.id,))
        row = cursor.fetchone()
        if row is not None:
            return -1
        request = "insert into locations(location_id, state, building_process, special_info) values (%s, %s, %s, %s)"
        cursor.execute(request, (self.id, self.state, self.building_process,
                                 json.dumps(self.special_info) if self.special_info is not None else None))


# Тронный зал с сокровищницей
class ThroneRoom(Location):
    def __init__(self, location_id, location_name, enter_text, need_clicks_to_construct=None,
                 state=True, building_process=-1, special_info=None):
        if location_id != 2:
            raise NameError
        super(ThroneRoom, self).__init__(location_id, location_name, enter_text, need_clicks_to_construct,
                                       state, building_process, special_info)
        treasury = self.special_info.get("treasury")
        self.treasury = Treasury(6, "Сокровищница",
                                 "Вы входите в сокровищницу. Ценные ресурсы аккуратно разложены в кучки, "
                                 "золото и ценное обмундирование занимает всё видимое пространство.\n\n"
                                 "Текущее состояние: 🌲Дерево: <b>{}</b>, ⛰Камень: <b>{}</b>",
                                 wood=treasury.get("wood"), stone=treasury.get("stone"), throne_room=self)

    def update_location_to_database(self):
        treasury = self.special_info.get("treasury")
        treasury.update({"wood": self.treasury.wood, "stone": self.treasury.stone})
        super().update_location_to_database()


# Сокровищница, с методами для работы с ресурсами
class Treasury(Location):
    def __init__(self, location_id, location_name, enter_text, need_clicks_to_construct=None,
                 state=True, building_process=-1, special_info=None, wood=0, stone=0, throne_room=None):
        super(Treasury, self).__init__(location_id, location_name, enter_text, need_clicks_to_construct,
                                       state, building_process, special_info)
        print(wood, stone)
        self.wood = wood
        self.stone = stone
        self.throne_room = throne_room
        if self.special_info is None:
            self.special_info = {}
        self.special_info.update({"enter_text_format_values": [self.wood, self.stone]})

    def change_resource(self, resource, count):
        if count >= 0:
            self.__setattr__(resource, self.__getattribute__(resource) + count)
        else:
            attr = self.__getattribute__(resource)
            if attr < count:
                return -1
            self.__setattr__(resource, attr + count)
        self.special_info.update({"enter_text_format_values": [self.wood, self.stone]})
        old = central_square.special_info.get("enter_text_format_values")
        old[1] = self.wood
        old[2] = self.stone
        central_square.update_location_to_database()
        self.update_location_to_database()

    def update_location_to_database(self):
        self.throne_room.update_location_to_database()


class ConstructionPlate(Location):

    BUTTONS_IN_ROW_LIMIT = 3

    def __init__(self, location_id, location_name, enter_text, need_clicks_to_construct=None,
                 state=True, building_process=-1, special_info=None):
        super(ConstructionPlate, self).__init__(location_id, location_name, enter_text, need_clicks_to_construct,
                                                state, building_process, special_info)
        self.construction_active = False
        self.buttons = [[KeyboardButton("↩️ Назад")]]

    def refill_current_buildings_info(self):
        current_row = 0
        old_text = "Сейчас в замке нет активного строительства. Следите за новостями."
        self.construction_active = False
        new_text = "Сейчас происходят следующие стройки:\n\n"
        self.buttons = [[], [KeyboardButton("↩️ Назад")]]
        for loc in list(locations.values()):
            if loc.state is False and loc.building_process >= 0:
                # Стройка на локации активна
                if not self.construction_active:
                    self.buttons = [[], [KeyboardButton("↩️ Назад")]]
                self.construction_active = True
                new_text += "<b>{}</b>\nПрогресс: <code>{}</code> из <code>{}</code>\n\n" \
                            "".format(loc.name, loc.building_process, loc.need_clicks_to_construct)
                if len(self.buttons[current_row]) >= self.BUTTONS_IN_ROW_LIMIT:
                    self.buttons.append([])
                    current_row += 1
                self.buttons[current_row].append(KeyboardButton(loc.name))
        new_text += "\nВыберите, куда отправиться!"
        if self.construction_active:
            self.special_info.update({"enter_text_format_values": [new_text]})
        else:
            self.special_info.update({"enter_text_format_values": [old_text]})

    def update_enter_text(self):
        self.refill_current_buildings_info()


#

"""
Далее находятся константы, связанные с локациями в Виртуальном замке - их названия, текст, с которым в локацию входят и
другие вещи, которые будут меняться редко
Это бы конечно закинуть в отдельный модуль с константами, но тогда ошибки импорта возникают
"""

throne_room = ThroneRoom(2, "🏛 Тронный зал",
                         "Вы поднимаетесь в Тронный Зал. Здесь можно обратиться к Высшему Командному Составу Скалы "
                         "и даже попросить аудиенции у ВРИО 👑@{}\n\n📜\n{}", need_clicks_to_construct=1000,
                         special_info={"enter_text_format_values": ["DjedyBreaM", "Дебриф"],
                                       "mid_players": [231900398, 205356091], "banned_in_feedback": [],
                                       "treasury": {"wood": 0, "stone": 0}})
throne_room.create_location_in_database()
central_square = Location(0, "⛲️ Центральная площадь",
                          "Вы стоите посреди ⛲️Центральной площади Скалы Темного Желания.\n\n"
                          "На лобном месте, левее фонтана, прибит пергамент с важным объявлением:\n📜\n<em>{}</em>\n📜\n"
                          "Заверено печатью и подписью Короля.\n\nТекущее состояние казны: 🌲Дерево: <b>{}</b>, "
                          "⛰Камень: <b>{}</b>\n\n"
                          "<a href=\"https://t.me/joinchat/GFFOhRbguH_dJK_6eiccIg\">Чат центральной площади</a>",
                          special_info={"enter_text_format_values": [
                              "Добро пожаловать в Скалу.\nСнова.", throne_room.treasury.wood,
                              throne_room.treasury.stone]
                          })
central_square.create_location_in_database()
try:
    old = central_square.special_info.get("enter_text_format_values")
    old[1] = throne_room.treasury.wood
    old[2] = throne_room.treasury.stone
except IndexError:
    # первый запуск с казной
    logging.error("Old format values in central square")
    pass
barracks = Location(1, "🎪 Казарма", "Вы заходите в казарму.")
barracks.create_location_in_database()
castle_gates = Location(3, "⛩ Врата замка",
                        "Вы подошли к вратам замка. Здесь как всегда немноголюдно. На посту дежурят стражи Скалы, "
                        "возможно, они смогут подсказать дорогу до нужного места, поделиться новостями или просто с "
                        "радостью скоротают время в беседе.", special_info={"players_on_duty": [],
                                                                            "banned_in_feedback": []})
castle_gates.create_location_in_database()
headquarters = Location(4, "Штаб", "Являясь генералом, Вы без проблем входите в штаб. На стенах висят карты, "
                                   "посыльные зачитывают донесения.")

technical_tower = Location(5, "Башню техно-магических наук",
                           "Добро пожаловать в башню Техно-Магических наук.\n"
                           "Глашатай верховного  Архимейстера Темного Желания вещает:\n\n📜\n{}",
                           special_info={"enter_text_format_values": ["Последнее обновление бота"],
                                         "last_update_id": 0})
technical_tower.create_location_in_database()

construction_plate = ConstructionPlate(7, "Стойплощадка", "Вы входите на стройплощадку.\n{}",
                                       special_info={
                                           "enter_text_format_values": ["Сейчас в замке нет активного строительства. "
                                                                        "Следите за новостями."]})
construction_plate.create_location_in_database()

hall_of_fame = Location(8, "🏤Мандапа Славы", "Мандапа Славы - почетное место, где увековечены герои Скалы, "
                        "их подвиги и заслуги перед замком. Вечная слава и почет!",
                        need_clicks_to_construct=1000, state=False, building_process=-1,
                        need_res_to_construct={"wood": 500, "stone": 500})
hall_of_fame.create_location_in_database()


# ТОВАРИЩ! СОЗДАЛ ЛОКАЦИЮ -- ВНЕСИ В СЛОВАРИ НИЖЕ!

status_to_location = {
    "default": None,
    "central_square": 0,
    "barracks": 1,
    "throne_room": 2,
    "castle_gates": 3,
    "headquarters": 4,
    "technical_tower": 5,
    "treasury": 6,
    "construction_plate": 7,
    "hall_of_fame": 8,
}

# Словарь с локациями - { id локации : объект класса Location }
# НЕ МЕНЯЙТЕ ЭТИ ID
locations = {
    0: central_square,
    1: barracks,
    2: throne_room,
    3: castle_gates,
    4: headquarters,
    5: technical_tower,
    6: throne_room.treasury,
    7: construction_plate,
    8: hall_of_fame,
}
