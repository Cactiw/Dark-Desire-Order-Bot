"""
В этом файле находятся классы для работы с локациями в виртуальном замке, такие как Казарма, Центральная площадь и тд...
"""


# Базовый класс - Локация
class Location:
    def __init__(self, location_id, location_name, enter_text, state=True, building_process=-1, special_info=None):
        self.id = location_id
        self.name = location_name
        self.enter_text = enter_text
        self.state = state  # True - построено, False - не построено
        self.building_process = building_process  # -1 - стройка не начиналась / завершилась, >=0 - идёт стройка
        self.special_info = special_info

    @staticmethod
    def get_location(location_id):
        return locations.get(location_id)

    @staticmethod
    def get_location_enter_text_by_id(location_id):
        location = Location.get_location(location_id)
        if location is None:
            return None
        if location.special_info is None:
            return location.enter_text
        insert_values = location.special_info.get("enter_text_format_values")
        if insert_values is None:
            return location.enter_text
        return location.enter_text.format(insert_values)


#

"""
Далее находятся константы, связанные с локациями в Виртуальном замке - их названия, текст, с которым в локацию входят и
другие вещи, которые будут меняться редко
"""


central_square = Location(0, "⛲️ Центральная площадь",
                          "Вы стоите посреди ⛲️Центральной площади Скалы Темного Желания.\n\n"
                          "На лобном месте, левее фонтана, прибит пергамент с важным объявлением:\n📜\n<em>{}</em>\n📜\n"
                          "Заверено печатью и подписью Короля.",
                          special_info={"enter_text_format_values": "Добро пожаловать в Скалу.\nСнова."})
barracks = Location(1, "🎪 Казарма", "Вы заходите в казарму.")
throne_room = Location(2, "🏛 Тронный зал",
                       "Вы поднимаетесь в Тронный Зал. Здесь можно обратиться к Высшему Командному Составу Скалы, "
                       "или даже попросить аудиенции у 👑 @{}", special_info={"enter_text_format_values": "DjedyBreaM"})

# Словарь с локациями - { id локации : объект класса Location }
locations = {
    0: central_square,
    1: barracks,
    2: throne_room

}
