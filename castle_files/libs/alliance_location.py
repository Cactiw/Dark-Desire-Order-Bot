
from castle_files.work_materials.globals import cursor


class AllianceLocation:

    def __init__(self, location_id, link, name, location_type, lvl, owner_id, turns_owned, expired):
        self.id = location_id
        self.link = link
        self.name = name
        self.type = location_type
        self.lvl = lvl
        self.owner_id = owner_id
        self.turns_owned = turns_owned
        self.expired = expired

    def figure_type(self):
        lower_name = self.name.lower()
        if "ruins" in lower_name:
            self.type = "ruins"
        elif "mine" in lower_name:
            self.type = "mine"
        elif "fort" in lower_name or "outpost" in lower_name:
            self.type = "glory"
        return self.type


    def insert_to_database(self):
        request = "insert into alliance_locations(link, name, type, lvl, owner_id, expired) VALUES " \
                  "(%s, %s, %s, %s, %s, %s) returning id"
        cursor.execute(request, (self.link, self.name, self.type, self.lvl, self.owner_id, self.expired))
        self.id = cursor.fetchone()[0]

    def update(self):
        request = "update alliance_locations set link = %s, name = %s, type = %s, lvl = %s, owner_id = %s, " \
                  "turns_owned = %s, expired = %s " \
                  "where id = %s"
        cursor.execute(request, (self.link, self.name, self.type, self.lvl, self.owner_id, self.turns_owned,
                                 self.expired,
                                 self.id))

    @staticmethod
    def get_location(location_id: int) -> 'AllianceLocation':
        request = "select link, name, type, lvl, owner_id, turns_owned, expired from alliance_locations where id = %s " \
                  "limit 1"
        cursor.execute(request, (location_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        link, name, location_type, lvl, owner_id, turns_owned, expired = row
        return AllianceLocation(location_id, link, name, location_type, lvl, owner_id, turns_owned, expired)

    @staticmethod
    def get_or_create_location_by_name_and_lvl(name: str, lvl: int) -> 'AllianceLocation':
        request = "select id from alliance_locations where expired is false and lower(name) = lower(%s) and lvl = %s " \
                  "limit 1"
        cursor.execute(request, (name, lvl))
        row = cursor.fetchone()
        if row is None:
            location = AllianceLocation(None, None, name, None, lvl, None, 0, False)
            location.insert_to_database()
            return location
        return AllianceLocation.get_location(row[0])
