# Моё(Рея всм(@reirose, если забыл))

daytime_table = {
    '01': 'night',
    '03': 'morning',
    '05': 'day',
    '07': 'evening',
    '09': 'night',
    '11': 'morning',
    '13': 'day',
    '15': 'evening',
    '17': 'night',
    '19': 'morning',
    '21': 'day',
    '23': 'evening'
}

avalible_tiers = {
    't2': 't2',
    't3': 't3',
    't4': 't4',
    'т2': 't2',
    'т3': 't3',
    'т4': 't4',
}


drop = {
    't2': {
        '🍄Болото':
            {
                'morning': [
                            "Hunter Helmet Fragment", "Hunter Armor Part", "Order Gauntlets Part",
                            "Order Boots Part", "Clarity Bracers Part",
                            "Clarity Shoes Part", "Hunter Blade", "War Hammer Head", "Champion Blade"],
                'day': [
                        "Hunter Helmet Fragment", "Hunter Armor Part", "Order Gauntlets Part",
                        "Order Boots Part", "Clarity Bracers Part",
                        "Clarity Shoes Part", "Hunter Blade", "War Hammer Head", "Champion Blade"],
                'evening': [
                            "Hunter Helmet Fragment", "Hunter Armor Part", "Order Gauntlets Part",
                            "Order Boots Part", "Clarity Bracers Part"
                            "Clarity Shoes Part", "Hunter Blade", "War Hammer Head", "Champion Blade"],
                'night': [
                          "Hunter Gloves Part", "Hunter Boots Part", "Order Helmet Fragment", "Order Armor Piece",
                          "Clarity Circlet Fragment",
                          "Clarity Robe Piece", "Trident Blade", "Order Shield Part", "Hunter Shaft"]
                    },
        '⛰Горы':
            {
                'morning': [
                            "Hunter Helmet Recipe", "Hunter Armor Recipe", "Order Gauntlets Recipe",
                            "Order Boots Recipe", "Clarity Bracers Recipe", "Clarity Shoes Recipe",
                            "Hunter Hunter Dagger Recipe", "War Hammer Recipe", "Champion Sword Recipe"],
                'day': [
                        "Hunter Helmet Recipe", "Hunter Armor Recipe", "Order Gauntlets Recipe", "Order Boots Recipe",
                        "Clarity Bracers Recipe", "Clarity Shoes Recipe", "Hunter Hunter Dagger Recipe",
                        "War Hammer Recipe", "Champion Sword Recipe"],
                'evening': [
                            "Hunter Helmet Recipe", "Hunter Armor Recipe", "Order Gauntlets Recipe",
                            "Order Boots Recipe", "Clarity Bracers Recipe", "Clarity Shoes Recipe",
                            "Hunter Dagger Recipe", "War Hammer Recipe", "Champion Sword Recipe"],
                'night': [
                        "Hunter Gloves Recipe", "Hunter Boots Recipe", "Order Helmet Recipe", "Order Armor Recipe",
                        "Clarity Circlet Recipe", "Clarity Robe Recipe", "Trident Recipe",
                        "Order Shield Recipe", "Hunter Bow Recipe"]
                    }
    },
    't3': {
         '🌲Лес': {
                'morning': ["Eclipse Recipe", "Doomblade Blade"],
                'day': ["Raging Lance Recipe", "King's Defender Blade"],
                'evening': ["Hailstorm Bow Recipe", "Lightning Bow Shaft"],
                'night': ["Dragon Mace Recipe", "Skull Crusher Head"]
                    },
         '🍄Болота': {
                    'morning': ["Eclipse Blade", "Royal Shield Part", "Crusader Armor Piece", "Crusader Armor Piece",
                                "Royal Helmet Fragment", "Ghost Armor Part", "Demon Circlet Fragment",
                                "Divine Shoes Part"],
                    'day': ["Dragon Mace Head", "Lion Blade", "Crusader Gauntlets Part", "Royal Armor Piece",
                            "Ghost Gloves Part", "Lion Helmet Fragment", "Demon Robe Piece", "Divine Circlet Fragment"],
                    'evening': ["Raging Lance Blade", "Ghost Blade", "Lion Armor Part", "Lion Gloves Part",
                                "Lion Boots Part", "Demon Bracers Part", "Demon Shoes Part", "Divine Robe Piece"],
                    'night': ["Hailstorm Bow Shaft", "Crusader Shield Part", "Crusader Helmet Fragment",
                              "Royal Helmet Fragment", "Royal Gauntlets Part", "Royal Boots Part",
                              "Ghost Helmet Fragment", "Ghost Boots Part", "Divine Bracers Part"]
                        },
         '⛰Горы': {
                    'morning': ["Doomblade Sword Recipe", "Royal Shield Recipe", "Crusader Armor Recipe",
                                "Crusader Boots Recipe", "Royal Helmet Recipe", "Ghost Armor Recipe",
                                "Demon Circlet Recipe", "Divine Shoes Recipe"],
                    'day': ["Skull Crusher Recipe", "Lion Knife Recipe", "Crusader Gauntlets Recipe",
                            "Royal Armor Recipe", "Ghost Gloves Recipe", "Lion Helmet Recipe",
                            "Demon Robe Recipe", "Divine Circlet Recipe"],
                    'evening': ["King's Defender Recipe", "Ghost Dagger Recipe", "Lion Armor Recipe",
                                "Lion Gloves Recipe", "Lion Boots Recipe", "Demon Bracers Recipe",
                                "Demon Shoes Recipe", "Divine Robe Recipe"],
                    'night': ["Lightning Bow Recipe", "Crusader Shield Recipe", "Crusader Helmet Recipe",
                              "Royal Gauntlets Recipe", "Royal Boots Recipe", "Ghost Helmet Recipe",
                              "Ghost Boots Recipe", "Divine Bracers Recipe"]
                        }
    },
    't4': {
        '🌲Лес':
            {
                'morning': ["Council Gauntlets Recipe", "Phoenix Sword Part", "Griffin Knife Recipe",
                            "Assault Cape Recipe"],
                'day': ["Celestial Boots Part", "Heavy Fauchard Recipe", "Griffin Knife Part", "Craftsman Apron Part"],
                'evening': ["Celestial Bracers Recipe", "Minotaur Sword Recipe", "Heavy Fauchard Part",
                            "Stoneskin Cloak Recipe"],
                'night': ["Griffin Armor Recipe", "Celestial Bracers Part", "Minotaur Sword Part",
                          "Stoneskin Cloak Recipe"]
                    },
        '🍄Болота':
            {
                'morning': ["Griffin Gloves Part", "Griffin Boots Recipe", "Council Boots Recipe",
                            "Black Morningstar Part", "Craftsman Apron Part"],
                'day': ["Griffin Helmet Part", "Council Helmet Recipe", "Celestial Helmet Part",
                        "Maiming Bulawa Recipe", "Stoneskin Cloak Part"],
                'evening': ["Griffin Gloves Recipe", "Council Helmet Part", "Council Armor Recipe",
                            "Celestial Armor Part", "Stoneskin Cloak Part"],
                'night': ["Council Armor Part", "Council Boots Part", "Celestial Helmet Recipe",
                          "Celestial Armor Recipe", "Stoneskin Cloak Part"]
                    },
        '⛰Горы':
            {
                'morning': ["Celestial Boots Recipe", "Guisarme Recipe", "Meteor Bow Part", "Council Shield Part",
                            "Assault Cape Part"],
                'day': ["Council Gauntlets Part", "Phoenix Sword Recipe", "Guisarme Part", "Nightfall Bow Recipe",
                        "Assault Cape Part"],
                'evening': ["Griffin Armor Part", "Meteor Bow Recipe", "Nightfall Bow Part", "Council Shield Recipe",
                            "Assault Cape Part"],
                'night': ["Griffin Helmet Recipe", "Griffin Boots Part", "Black Morningstar Recipe",
                          "Maiming Bulawa Part", "Craftsman Apron Recipe"]
                    }
    }
}
