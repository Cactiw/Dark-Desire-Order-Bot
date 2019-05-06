"""
В этом файле находятся классы для работы с локациями в виртуальном замке, такие как Казарма, Центральная площадь и тд...
"""
from castle_files.work_materials.globals import conn

import json

cursor = conn.cursor()


# Базовый класс - Локация
class Location:
    def __init__(self, location_id, location_name, enter_text, state=True, building_process=-1, special_info=None):
        self.id = location_id
        self.name = location_name
        self.enter_text = enter_text
        self.state = state  # True - построено, False - не построено
        self.building_process = building_process  # -1 - стройка не начиналась / завершилась, >=0 - идёт стройка
        self.special_info = special_info
        self.load_location()

    @staticmethod
    def get_location(location_id):
        return locations.get(location_id)

    @staticmethod
    def get_location_enter_text_by_id(location_id, without_format=False):
        location = Location.get_location(location_id)
        if location is None:
            return None
        if location.special_info is None:
            return location.enter_text
        insert_values = location.special_info.get("enter_text_format_values")
        if insert_values is None or without_format:
            return location.enter_text
        print(insert_values, *insert_values)
        return location.enter_text.format(*insert_values)

    @staticmethod
    def get_id_by_status(status):
        return status_to_location.get(status)

    def load_location(self):
        request = "select state, building_process, special_info from locations where location_id = %s"
        cursor.execute(request, (self.id,))
        row = cursor.fetchone()
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


#

"""
Далее находятся константы, связанные с локациями в Виртуальном замке - их названия, текст, с которым в локацию входят и
другие вещи, которые будут меняться редко
"""


central_square = Location(0, "⛲️ Центральная площадь",
                          "Вы стоите посреди ⛲️Центральной площади Скалы Темного Желания.\n\n"
                          "На лобном месте, левее фонтана, прибит пергамент с важным объявлением:\n📜\n<em>{}</em>\n📜\n"
                          "Заверено печатью и подписью Короля.",
                          special_info={"enter_text_format_values": ["Добро пожаловать в Скалу.\nСнова."]})
central_square.create_location_in_database()
barracks = Location(1, "🎪 Казарма", "Вы заходите в казарму.")
barracks.create_location_in_database()
throne_room = Location(2, "🏛 Тронный зал",
                       "Вы поднимаетесь в Тронный Зал. Здесь можно обратиться к Высшему Командному Составу Скалы, "
                       "или даже попросить аудиенции у 👑@{}\n\n📜\n{}",
                       special_info={"enter_text_format_values": ["DjedyBreaM", "Дебриф"],
                                     "mid_players": [231900398, 205356091], "banned_in_feedback": []})
throne_room.create_location_in_database()
print(throne_room.special_info.get("enter_text_format_values"))
castle_gates = Location(3, "⛩ Врата замка",
                        "Вы подошли к вратам замка. Здесь как всегда немноголюдно. На посту дежурят стражи Скалы, "
                        "возможно, они смогут подсказать  дорогу до нужного места, поделиться новостями или просто с "
                        "радостью скоротают время в беседе.", special_info={"players_on_duty": [],
                                                                            "banned_in_feedback": []})
castle_gates.create_location_in_database()
headquarters = Location(4, "Штаб", "Являясь генералом, Вы без проблем входите в штаб. На стенах висят карты, "
                                   "посыльные зачитывают донесения.")

status_to_location = {
    "default": None,
    "central_square": 0,
    "barracks": 1,
    "throne_room": 2,
    "castle_gates": 3,
    "headquarters": 4,
}

# Словарь с локациями - { id локации : объект класса Location }
# НЕ МЕНЯЙТЕ ЭТИ ID
locations = {
    0: central_square,
    1: barracks,
    2: throne_room,
    3: castle_gates,
    4: headquarters,
}
