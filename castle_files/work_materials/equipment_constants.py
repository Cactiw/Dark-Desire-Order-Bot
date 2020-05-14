from castle_files.libs.equipment import Equipment

import copy

# ВНИМАНИЕ! Айтемы из одного слова, которое повторяется в более продвинутых айтемах (например, gloves),
# помещать в самый конец!!!
# Товарищ! При добавлении экипировки не забывай добавить данные о её крафте в item_consts.py!
main_hand = [
    Equipment("main_hand", "w", "01", "Wooden sword", 1, 0, 0),
    Equipment("main_hand", "w", "02", "Short sword", 3, 0, 0),
    Equipment("main_hand", "w", "03", "Long sword", 6, 0, 0),
    Equipment("main_hand", "w", "04", "Widow sword", 10, 0, 0),
    Equipment("main_hand", "w", "05", "Knight's sword", 16, 0, 1),
    Equipment("main_hand", "w", "06", "Elven sword", 22, 0, 1),
    Equipment("main_hand", "w", "07", "Rapier", 27, 0, 1),
    Equipment("main_hand", "w", "08", "Short spear", 3, 1, 0),
    Equipment("main_hand", "w", "09", "Long spear", 3, 1, 0),
    Equipment("main_hand", "w", "11", "Elven spear", 12, 7, 1),
    Equipment("main_hand", "w", "12", "Halberd", 14, 10, 1),
    Equipment("main_hand", "w", "18", "Elven Bow", 4, 1, 0),
    Equipment("main_hand", "w", "19", "Wooden Bow", 8, 2, 0),
    Equipment("main_hand", "w", "20", "Long Bow", 12, 4, 0),
    Equipment("main_hand", "w", "21", "Elven Bow", 16, 5, 1),
    Equipment("main_hand", "w", "22", "Forest Bow", 18, 6, 1),
    Equipment("main_hand", "w", "26", "Steel axe", 9, 9, 1),
    Equipment("main_hand", "w", "27", "Mithril axe", 11, 11, 1),
    Equipment("main_hand", "w", "28", "Champion Sword", 31, 0, 2),
    Equipment("main_hand", "w", "29", "Trident", 16, 14, 2),
    Equipment("main_hand", "w", "30", "Hunter Bow", 22, 8, 2),
    Equipment("main_hand", "w", "31", "War hammer", 15, 15, 2),
    Equipment("main_hand", "w", "33", "Thundersoul Sword", 35, 0, 3),
    Equipment("main_hand", "w", "34", "Doomblade Sword", 36, 1, 3),
    Equipment("main_hand", "w", "35", "Eclipse", 37, 0, 3),
    Equipment("main_hand", "w", "36", "Guard's Spear", 18, 16, 3),
    Equipment("main_hand", "w", "37", "King's Defender", 18, 17, 3),
    Equipment("main_hand", "w", "38", "Raging Lance", 19, 16, 3),
    Equipment("main_hand", "w", "39", "Composite Bow", 25, 9, 3),
    Equipment("main_hand", "w", "40", "Lightning Bow", 27, 8, 3),
    Equipment("main_hand", "w", "41", "Hailstorm Bow", 24, 11, 3),
    Equipment("main_hand", "w", "42", "Imperial Axe", 17, 17, 3),
    Equipment("main_hand", "w", "43", "Skull Crusher", 18, 17, 3),
    Equipment("main_hand", "w", "44", "Dragon Mace", 17, 18, 3),
    Equipment("main_hand", "w", "92", "Minotaur Sword", 41, 0, 4),
    Equipment("main_hand", "w", "93", "Phoenix Sword", 45, 0, 4),
    Equipment("main_hand", "w", "94", "Heavy Fauchard", 21, 19, 4),
    Equipment("main_hand", "w", "95", "Guisarme", 23, 21, 4),
    Equipment("main_hand", "w", "96", "Meteor Bow", 29, 11, 4),
    Equipment("main_hand", "w", "97", "Nightfall Bow", 32, 12, 4),
    Equipment("main_hand", "w", "98", "Black Morningstar", 19, 21, 4),
    Equipment("main_hand", "w", "99", "Maiming Bulawa", 22, 22, 4),
    Equipment("main_hand", "w", "101", "Lightbane Katana", 50, 0, 5),
    Equipment("main_hand", "w", "102", "Doom Warglaive", 55, 0, 5),
    Equipment("main_hand", "w", "103", "Decimation Harpoon", 26, 24, 5),
    Equipment("main_hand", "w", "104", "Sinister Ranseur", 29, 29, 5),
    Equipment("main_hand", "w", "105", "Heartstriker Bow", 36, 14, 5),
    Equipment("main_hand", "w", "106", "Windstalker Bow", 40, 15, 5),
    Equipment("main_hand", "w", "107", "Malificent Maul", 24, 26, 5),
    Equipment("main_hand", "w", "108", "Brutalizer Flail", 25, 29, 5),

    Equipment("main_hand", "e", "143", "Witchling Staff", 19, 14, 2),
    Equipment("main_hand", "e", "144", "War Club", 17, 14, 2),
    Equipment("main_hand", "e", "145", "Imp Bow", 23, 8, 2),
    Equipment("main_hand", "e", "148", "Fleder Scimitar", 34, 0, 2),
    Equipment("main_hand", "e", "149", "Witch Staff", 0, 0, 2),
    Equipment("main_hand", "e", "150", "Walker Club", 17, 20, 2),
    Equipment("main_hand", "e", "151", "Demon Bow", 26, 12, 2),
    Equipment("main_hand", "e", "154", "Nosferatu Rapier", 0, 0, 2),

    Equipment("main_hand", "w", "10", "Lance", 11, 5, 0),
]

second_hand = [
    Equipment("second_hand", "w", "13", "Kitchen knife", 3, 0, 0),
    Equipment("second_hand", "w", "14", "Battle knife", 2, 0, 0),
    Equipment("second_hand", "w", "15", "Steel dagger", 3, 0, 0),
    Equipment("second_hand", "w", "16", "Silver dagger", 5, 0, 1),
    Equipment("second_hand", "w", "17", "Mithril dagger", 7, 0, 1),
    Equipment("second_hand", "w", "32", "Hunter dagger", 10, 0, 2),
    Equipment("second_hand", "w", "45", "Ghost dagger", 12, 1, 3),
    Equipment("second_hand", "w", "46", "Lion Knife", 13, 0, 3),
    Equipment("second_hand", "w", "91", "Griffin Knife", 15, 0, 4),
    Equipment("second_hand", "w", "100", "Poniard", 19, 0, 5),


    Equipment("second_hand", "e", "152", "Demon Whip", 15, 1, 2),
    Equipment("second_hand", "e", "153", "Werewolf Knife", 0, 0, 2),
    Equipment("second_hand", "e", "147", "Manwolf Knife", 13, 0, 2),
    Equipment("second_hand", "e", "146", "Imp Whip", 12, 0, 2),

    Equipment("second_hand", "a", "21", "Wooden shield", 0, 1, 0),
    Equipment("second_hand", "a", "22", "Skeleton Buckler", 0, 2, 0),
    Equipment("second_hand", "a", "23", "Bronze shield", 0, 3, 0),
    Equipment("second_hand", "a", "24", "Silver shield", 0, 5, 1),
    Equipment("second_hand", "a", "25", "Mithril shield", 0, 7, 1),
    Equipment("second_hand", "a", "31", "Order Shield", 0, 10, 2),
    Equipment("second_hand", "a", "49", "Crusader Shield", 1, 12, 3),
    Equipment("second_hand", "a", "54", "Royal Shield", 1, 13, 3),
    Equipment("second_hand", "a", "82", "Council Shield", 0, 15, 4),
    Equipment("second_hand", "a", "113", "Overseer shield", 0, 20, 5),

    Equipment("second_hand", "e", "113", "Walker Shield", 0, 12, 2),
    Equipment("second_hand", "e", "118", "Zombie Shield", 1, 14, 2),
]

head = [
    Equipment("head", "a", "06", "Hat", 0, 1, 0),
    Equipment("head", "a", "07", "Leather hood", 0, 2, 0),
    Equipment("head", "a", "08", "Steel helmet", 0, 3, 0),
    Equipment("head", "a", "09", "Silver helmet", 0, 7, 1),
    Equipment("head", "a", "10", "Mithril helmet", 0, 12, 1),
    Equipment("head", "a", "28", "Order Helmet", 3, 15, 2),
    Equipment("head", "a", "37", "Clarity Circlet", 2, 12, 2),
    Equipment("head", "a", "33", "Hunter Helmet", 5, 11, 2),
    Equipment("head", "a", "46", "Crusader Helmet", 6, 19, 3),
    Equipment("head", "a", "51", "Royal Helmet", 5, 20, 3),
    Equipment("head", "a", "64", "Demon Circlet", 5, 15, 3),
    Equipment("head", "a", "68", "Divine Circlet", 4, 16, 3),
    Equipment("head", "a", "56", "Ghost Helmet", 7, 15, 3),
    Equipment("head", "a", "60", "Lion Helmet", 8, 14, 3),
    Equipment("head", "a", "79", "Council Helmet", 8, 25, 4),
    Equipment("head", "a", "88", "Celestial Helmet", 6, 20, 4),
    Equipment("head", "a", "84", "Griffin Helmet", 11, 18, 4),
    Equipment("head", "a", "106", "Manticore Helmet", 14, 24, 5),
    Equipment("head", "a", "107", "Overseer Helmet", 10, 33, 5),
    Equipment("head", "a", "108", "Discarnate Circlet", 9, 25, 5),

    Equipment("head", "e", "102", "Witchling Circlet", 2, 12, 2),
    Equipment("head", "e", "106", "Witch Circlet", 0, 0, 2),
    Equipment("head", "e", "110", "Walker Helmet", 3, 17, 2),
    Equipment("head", "e", "115", "Zombie Helmet", 6, 22, 2),
    Equipment("head", "e", "120", "Imp Circlet", 3, 12, 2),
    Equipment("head", "e", "128", "Manwolf Helmet", 7, 11, 2),
    Equipment("head", "e", "132", "Werewolf Helmet", 0, 0, 2),
    Equipment("head", "e", "136", "Fleder Helmet", 8, 9, 2),
    Equipment("head", "e", "140", "Nosferatu Helmet", 0, 0, 2),
]

gloves = [
    Equipment("gloves", "a", "17", "Leather gloves", 0, 2, 0),
    Equipment("gloves", "a", "18", "Steel gauntlets", 0, 3, 0),
    Equipment("gloves", "a", "19", "Silver gauntlets", 0, 5, 1),
    Equipment("gloves", "a", "20", "Mithril gauntlets", 0, 8, 1),
    Equipment("gloves", "a", "39", "Order Gauntlets", 2, 10, 2),
    Equipment("gloves", "a", "35", "Clarity Bracers", 1, 9, 2),
    Equipment("gloves", "a", "30", "Hunter Gloves", 3, 8, 2),
    Equipment("gloves", "a", "48", "Crusader Gauntlets", 4, 12, 3),
    Equipment("gloves", "a", "53", "Royal Gauntlets", 3, 13, 3),
    Equipment("gloves", "a", "66", "Demon Bracers", 4, 10, 3),
    Equipment("gloves", "a", "70", "Divine Bracers", 3, 11, 3),
    Equipment("gloves", "a", "58", "Ghost Gloves", 5, 10, 3),
    Equipment("gloves", "a", "62", "Lion Gloves", 6, 9, 3),
    Equipment("gloves", "a", "81", "Council Gauntlets", 5, 15, 4),
    Equipment("gloves", "a", "90", "Celestial Bracers", 5, 13, 4),
    Equipment("gloves", "a", "86", "Griffin Gloves", 7, 12, 4),
    Equipment("gloves", "a", "106", "Manticore Gloves", 11, 15, 5),
    Equipment("gloves", "a", "107", "Overseer Gauntlets", 6, 19, 5),
    Equipment("gloves", "a", "108", "Discarnate Bracers", 7, 15, 5),

    Equipment("gloves", "e", "104", "Witchling Bracers", 1, 9, 2),
    Equipment("gloves", "e", "108", "Witch Bracers", 0, 0, 2),
    Equipment("gloves", "e", "112", "Walker Gauntlets", 2, 11, 2),
    Equipment("gloves", "e", "117", "Zombie Gauntlets", 4, 13, 2),
    Equipment("gloves", "e", "122", "Imp Bracers", 2, 9, 2),
    Equipment("gloves", "e", "126", "Demon Bracers", 5, 7, 2),
    Equipment("gloves", "e", "130", "Manwolf Gloves", 5, 8, 2),
    Equipment("gloves", "e", "134", "Werewolf Gloves", 0, 0, 2),
    Equipment("gloves", "e", "138", "Fleder Gloves", 6, 6, 2),
    Equipment("gloves", "e", "142", "Nosferatu Gloves", 0, 0, 2),

    Equipment("gloves", "a", "16", "Gloves", 0, 1, 0),
]

armor = [
    Equipment("armor", "a", "01", "Cloth jacket", 0, 2, 0),
    Equipment("armor", "a", "02", "Leather shirt", 0, 4, 0),
    Equipment("armor", "a", "03", "Chain mail", 0, 12, 0),
    Equipment("armor", "a", "04", "Silver cuirass", 1, 15, 1),
    Equipment("armor", "a", "05", "Mithril armor", 3, 17, 1),
    Equipment("armor", "a", "27", "Order Armor", 5, 25, 2),
    Equipment("armor", "a", "36", "Clarity Robe", 4, 20, 2),
    Equipment("armor", "a", "32", "Hunter Armor", 8, 18, 2),
    Equipment("armor", "a", "45", "Crusader Armor", 10, 32, 3),
    Equipment("armor", "a", "50", "Royal Armor", 8, 34, 3),
    Equipment("armor", "a", "63", "Demon Robe", 9, 25, 3),
    Equipment("armor", "a", "67", "Divine Robe", 8, 26, 3),
    Equipment("armor", "a", "55", "Ghost Armor", 12, 26, 3),
    Equipment("armor", "a", "59", "Lion Armor", 14, 24, 3),
    Equipment("armor", "a", "78", "Council Armor", 13, 42, 4),
    Equipment("armor", "a", "87", "Celestial Armor", 11, 34, 4),
    Equipment("armor", "a", "83", "Griffin Armor", 16, 34, 4),
    Equipment("armor", "a", "106", "Manticore Armor", 24, 45, 5),
    Equipment("armor", "a", "107", "Overseer Armor", 18, 60, 5),
    Equipment("armor", "a", "108", "Discarnate Robe", 19, 45, 5),

    Equipment("armor", "e", "101", "Witchling Robe", 4, 20, 2),
    Equipment("armor", "e", "105", "Witch Robe", 0, 0, 2),
    Equipment("armor", "e", "109", "Walker Armor", 5, 28, 2),
    Equipment("armor", "e", "114", "Zombie Armor", 10, 34, 2),
    Equipment("armor", "e", "119", "Imp Robe", 5, 20, 2),
    Equipment("armor", "e", "123", "Demon Robe", 10, 22, 2),
    Equipment("armor", "e", "127", "Manwolf Armor", 11, 18, 2),
    Equipment("armor", "e", "131", "Werewolf Armor", 0, 0, 2),
    Equipment("armor", "e", "135", "Fleder Armor", 12, 16, 2),
    Equipment("armor", "e", "139", "Nosferatu Armor", 0, 0, 2),
]

boots = [
    Equipment("boots", "a", "11", "Sandals", 0, 1, 0),
    Equipment("boots", "a", "12", "Leather shoes", 0, 2, 0),
    Equipment("boots", "a", "13", "Steel boots", 0, 3, 0),
    Equipment("boots", "a", "14", "Silver boots", 0, 5, 1),
    Equipment("boots", "a", "15", "Mithril boots", 0, 8, 1),
    Equipment("boots", "a", "29", "Order Boots", 2, 10, 2),
    Equipment("boots", "a", "38", "Clarity Shoes", 1, 9, 2),
    Equipment("boots", "a", "34", "Hunter Boots", 3, 8, 2),
    Equipment("boots", "a", "47", "Crusader Boots", 4, 12, 3),
    Equipment("boots", "a", "52", "Royal Boots", 3, 13, 3),
    Equipment("boots", "a", "65", "Demon Shoes", 4, 10, 3),
    Equipment("boots", "a", "69", "Divine Shoes", 3, 11, 3),
    Equipment("boots", "a", "57", "Ghost Boots", 5, 10, 3),
    Equipment("boots", "a", "61", "Lion Boots", 6, 9, 3),
    Equipment("boots", "a", "80", "Council Boots", 5, 15, 4),
    Equipment("boots", "a", "89", "Celestial Boots", 5, 13, 4),
    Equipment("boots", "a", "85", "Griffin Boots", 7, 12, 4),
    Equipment("boots", "a", "106", "Manticore Boots", 12, 15, 5),
    Equipment("boots", "a", "107", "Overseer Boots", 6, 20, 5),
    Equipment("boots", "a", "108", "Discarnate Shoes", 7, 14, 5),

    Equipment("boots", "e", "103", "Witchling Shoes", 1, 9, 2),
    Equipment("boots", "e", "107", "Witch Shoes", 0, 0, 2),
    Equipment("boots", "e", "111", "Walker Boots", 2, 11, 2),
    Equipment("boots", "e", "116", "Zombie Boots", 4, 13, 2),
    Equipment("boots", "e", "121", "Imp Shoes", 2, 9, 2),
    Equipment("boots", "e", "125", "Demon Shoes", 5, 7, 2),
    Equipment("boots", "e", "129", "Manwolf Boots", 5, 8, 2),
    Equipment("boots", "e", "133", "Werewolf Boots", 0, 0, 2),
    Equipment("boots", "e", "137", "Fleder Boots", 6, 6, 2),
    Equipment("boots", "e", "141", "Nosferatu Boots", 0, 0, 2),
]

cloaks = [
    Equipment("cloaks", "a", "26", "Royal Guard Cape", 1, 1, 0),
    Equipment("cloaks", "a", "44", "Veteran's Cloak", 3, 3, 0),
    Equipment("cloaks", "a", "71", "Storm Cloak", 4, 3, 3),
    Equipment("cloaks", "a", "72", "Durable Cloak", 3, 4, 3),
    Equipment("cloaks", "a", "73", "Blessed Cloak", 2, 2, 3),
    Equipment("cloaks", "a", "100", "Assault Cape", 6, 3, 4),
    Equipment("cloaks", "a", "101", "Craftsman Apron", 3, 3, 4),
    Equipment("cloaks", "a", "102", "Stoneskin Cloak", 3, 6, 4),
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

# Хранит имя предмета как ключ (В lower!!) и код (с типом) как значение. Заполняется функцией fill_names
# Пример: { "knight's sword": "w05" }
equipment_names = {}


def fill_names():
    eq_list = list(equipment.values())
    for lst in eq_list:
        for eq in lst:
            equipment_names.update({eq.name.lower(): "{}{}".format(eq.type, eq.code)})


fill_names()


def get_equipment_by_code(code):
    if code is None:
        return None
    eq_type = code[0]
    eq_code = code[1:]
    eq_list = list(equipment.values())
    for lst in eq_list:
        for eq in lst:
            if eq.code == eq_code and eq.type == eq_type:
                return copy.deepcopy(eq)
    return None


def get_equipment_by_name(eq_name):
    search_name = eq_name.lower()
    names_list = list(equipment_names.items())
    code = None
    for name, item_code in names_list:
        if name in search_name:
            code = item_code
            break
    eq = get_equipment_by_code(code)
    if eq is not None:
        eq.name = eq_name
    return eq


def search_equipment_by_name(eq_name):
    eq_name = eq_name.lower()
    found = []
    names_list = list(equipment_names.items())
    for name, item_code in names_list:
        if eq_name in name:
            found.append(get_equipment_by_code(item_code))
    return found
