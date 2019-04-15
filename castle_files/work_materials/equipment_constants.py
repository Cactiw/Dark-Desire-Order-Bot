from castle_files.libs.equipment import Equipment

main_hand = [
    Equipment("main_hand", "w", "05", "Knight's sword", 16, 0, 1),
    Equipment("main_hand", "w", "06", "Elven sword", 22, 0, 1),
    Equipment("main_hand", "w", "07", "Rapier", 27, 0, 1),
    Equipment("main_hand", "w", "21", "Elven Bow", 16, 5, 1),
    Equipment("main_hand", "w", "22", "Forest Bow", 18, 6, 1),
    Equipment("main_hand", "w", "11", "Elven spear", 12, 7, 1),
    Equipment("main_hand", "w", "12", "Halberd", 14, 10, 1),
    Equipment("main_hand", "w", "26", "Steel axe", 9, 9, 1),
    Equipment("main_hand", "w", "27", "Mithril axe", 11, 11, 1),
    # TODO добавить всё, кроме мечей из лавки + тир 2-4
]

second_hand = [
    Equipment("second_hand", "w", "16", "Silver dagger", 5, 0, 1),
    Equipment("second_hand", "w", "17", "Mithril dagger", 7, 0, 1),
    Equipment("second_hand", "w", "13", "Kitchen knife", 3, 0, 0),
    Equipment("second_hand", "w", "14", "Battle knife", 2, 0, 0),
    Equipment("second_hand", "w", "15", "Steel dagger", 3, 0, 0),
    Equipment("second_hand", "w", "16", "Silver dagger", 5, 0, 0),
    Equipment("second_hand", "w", "17", "Mithril dagger", 7, 0, 0),

    Equipment("a", "21", "Wooden shield", 0, 1, 0),
    Equipment("a", "22", "Skeleton Buckler", 0, 2, 0),
    Equipment("a", "23", "Bronze shield", 0, 3, 0),
    Equipment("a", "24", "Silver shield", 0, 5, 0),
    Equipment("a", "25", "Mithril shield", 0, 7, 0),
    # TODO Добавить тир 2-4
]
# TODO Добавить всё остальное, тир 0-4

head = [
    Equipment("w", "05", "Knight's sword", 16, 0, 1),
    Equipment("w", "06", "Elven sword", 22, 0, 1),
    Equipment("w", "07", "Rapier", 27, 0, 1),
]

gloves = [
    Equipment("w", "05", "Knight's sword", 16, 0, 1),
    Equipment("w", "06", "Elven sword", 22, 0, 1),
    Equipment("w", "07", "Rapier", 27, 0, 1),
]

armor = [
    Equipment("w", "05", "Knight's sword", 16, 0, 1),
    Equipment("w", "06", "Elven sword", 22, 0, 1),
    Equipment("w", "07", "Rapier", 27, 0, 1),
]

boots = [
    Equipment("w", "05", "Knight's sword", 16, 0, 1),
    Equipment("w", "06", "Elven sword", 22, 0, 1),
    Equipment("w", "07", "Rapier", 27, 0, 1),
]

cloaks = [
    Equipment("w", "05", "Knight's sword", 16, 0, 1),
    Equipment("w", "06", "Elven sword", 22, 0, 1),
    Equipment("w", "07", "Rapier", 27, 0, 1),
]

equipment = {
    "main_hand": main_hand,
    "second_hand": second_hand,
    "head": head,
    "gloves": gloves,
    "armor": armor,
    "boots": boots,
    "cloaks": cloaks
}

# Хранит имя предмета как ключ и код (с типом) как значение. Заполняется функцией fill_names
# Пример: { "Knight's sword": "w05" }
equipment_names = {}


def fill_names():
    eq_list = list(equipment.values())
    for lst in eq_list:
        for eq in lst:
            equipment_names.update({eq.name: "{}{}".format(eq.type, eq.name)})


fill_names()


def get_equipment_by_code(code):
    eq_type = code[0]
    eq_code = code[1:]
    eq_list = list(equipment.values())
    for lst in eq_list:
        for eq in lst:
            if eq.code == eq_code and eq.type == eq_type:
                return eq
    return None
