"""
Здесь находится класс лавки в ЧВ
"""

from castle_files.work_materials.globals import conn, moscow_tz

from castle_files.bin.service_functions import get_current_datetime, translate_number_to_emoji

import datetime
import json


class Shop:
    attributes = ["link", "name", "ownerTag", "ownerName", "ownerCastle", "kind", "mana", "offers", "castleDiscount",
                  "guildDiscount", "specialization", "qualityCraftLevel", "maintenanceEnabled", "maintenanceCost",
                  "last_seen"]
    last_update = None
    UPDATE_LIMIT = 5 * 60

    def __init__(self, id, link, name, ownerTag, ownerName, ownerCastle, kind, mana, offers, castleDiscount,
                 guildDiscount, specialization, qualityCraftLevel, maintenanceEnabled, maintenanceCost, last_seen):
        self.id = id
        self.link = link
        self.name = name
        self.ownerTag = ownerTag
        self.ownerName = ownerName
        self.ownerCastle = ownerCastle
        self.kind = kind
        self.mana = mana
        self.offers = offers
        self.castleDiscount = castleDiscount
        self.guildDiscount = guildDiscount
        self.specialization = specialization
        self.qualityCraftLevel = qualityCraftLevel
        self.maintenanceEnabled = maintenanceEnabled
        self.maintenanceCost = maintenanceCost

        self.last_seen = last_seen

    def get_json_offers(self):
        return json.dumps(self.offers, ensure_ascii=False) if self.offers is not None else None

    def get_json_specialization(self):
        return json.dumps(self.specialization, ensure_ascii=False) if self.specialization is not None else None

    def get_offered_names(self):
        return list(map(lambda offer: offer.get("item"), self.offers))

    def get_offer(self, item_name: str) -> dict:
        for offer in self.offers:
            if offer["item"].lower() == item_name.lower():
                return offer
        return None

    def format_offer(self, eq, offer):
        return "{} ({}%) {}💰 {}💧 <a href=\"t.me/share/url?url=/ws_{}\">{}{}</a>\n".format(
            translate_number_to_emoji(self.qualityCraftLevel), self.specialization.get(eq.get_quality_type()),
            offer.get("price"), self.mana,
            self.link, self.ownerCastle, self.name
        )

    def is_open(self) -> bool:
        return -self.UPDATE_LIMIT < (self.last_update - self.last_seen).total_seconds() < self.UPDATE_LIMIT

    @classmethod
    def update_or_create_shop(cls, shop_dict: dict):
        link = shop_dict.get("link")
        shop = cls.get_shop(link=link)
        new = False
        if shop is None:
            shop = cls(None, *cls.attributes)
            new = True

        for attribute in cls.attributes:
            setattr(shop, attribute, shop_dict.get(attribute, None))
        shop.last_seen = get_current_datetime()

        if new:
            shop.create()
        else:
            shop.update()

        if cls.last_update is None or shop.last_seen > cls.last_update:
            cls.last_update = shop.last_seen

    @classmethod
    def get_quality_shops(cls, place):
        request = "select id from shops where specialization -> '{}' is not null order by qualitycraftlevel desc, " \
                  "last_seen desc".format(place)
        cursor = conn.cursor()
        cursor.execute(request)
        rows = cursor.fetchall()
        cursor.close()

        return list(map(lambda shop_id: cls.get_shop(shop_id), rows))


    @staticmethod
    def get_shop(shop_id: int = None, link: str = None):
        arg_name = "id" if shop_id is not None else "link"
        arg = shop_id if shop_id is not None else link

        cursor = conn.cursor()
        request = "select id, link, name, ownerTag, ownerName, ownerCastle, kind, mana, offers, castleDiscount, " \
                  "guildDiscount, specialization, qualityCraftLevel, maintenanceEnabled, maintenanceCost, last_seen " \
                  "from shops " \
                  "where {} = %s limit 1".format(arg_name)
        cursor.execute(request, (arg,))
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            return None
        shop = Shop(*row)
        if shop.last_update is None or shop.last_seen > shop.last_update:
            Shop.last_update = shop.last_seen
        return shop

    def update(self):
        request = "update shops set id = %s, link = %s, name = %s, ownerTag = %s, ownerName = %s, ownerCastle = %s, " \
                  "kind = %s, mana = %s, offers = %s, castleDiscount = %s, guildDiscount = %s, specialization = %s, " \
                  "qualityCraftLevel = %s, maintenanceEnabled = %s, maintenanceCost = %s, last_seen = %s where id = %s"
        cursor = conn.cursor()
        cursor.execute(request, (
            self.id, self.link, self.name, self.ownerTag, self.ownerName, self.ownerCastle, self.kind, self.mana,
            self.get_json_offers(), self.castleDiscount, self.guildDiscount, self.get_json_specialization(),
            self.qualityCraftLevel, self.maintenanceEnabled, self.maintenanceCost, self.last_seen, self.id))
        cursor.close()

    def create(self):
        request = "insert into shops(link, name, ownerTag, ownerName, ownerCastle, kind, mana, offers, " \
                  "castleDiscount, guildDiscount, specialization, qualityCraftLevel, maintenanceEnabled, " \
                  "maintenanceCost, last_seen) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor = conn.cursor()
        cursor.execute(request, (
            self.link, self.name, self.ownerTag, self.ownerName, self.ownerCastle, self.kind, self.mana,
            self.get_json_offers(),
            self.castleDiscount, self.guildDiscount, self.get_json_specialization(), self.qualityCraftLevel,
            self.maintenanceEnabled, self.maintenanceCost, get_current_datetime()))
        cursor.close()

