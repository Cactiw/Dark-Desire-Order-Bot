
from castle_files.work_materials.globals import cursor


class AllianceLocation:

    def __init__(self, location_id, link, name, location_type, lvl, owner_id, turns_owned, can_expired, expired):
        self.id = location_id
        self.link = link
        self.name = name
        self.type = location_type
        self.emoji = self.type[0] if self.type else ""
        self.lvl = lvl
        self.owner_id = owner_id
        self.turns_owned = turns_owned
        self.can_expired = can_expired
        self.expired = expired

        self.figure_type()

    def figure_type(self):
        lower_name = self.name.lower()
        if "ruins" in lower_name:
            self.type = "🏷Ruins"
        elif "mine" in lower_name:
            self.type = "📦Mine"
        elif "fort" in lower_name or "outpost" in lower_name or "tower" in lower_name:
            self.type = "🎖Glory"
        self.emoji = self.type[0]
        return self.type

    def is_active(self) -> bool:
        return self.owner_id is not None and self.turns_owned > 0

    def format_name(self) -> str:
        return "{} Lvl.{}".format(self.name, self.lvl)

    def format_link_view(self, alliance, new_line=True) -> str:
        s = "{}{}{}{}" \
               "".format(
                self.emoji, '❇️' if self.is_active() else '',
                "<a href=\"t.me/share/url?url={}\">{} Lvl.{}</a>".format(
                    "/ga_atk_{}".format(self.link) if alliance is None or self.owner_id != alliance.id else
                    "/ga_def_{}".format(self.link), self.name,
                    self.lvl) if self.link is not None else "{} Lvl.{}".format(self.name, self.lvl),
                "<a href=\"t.me/share/url?url=/ga_expire {}\">⚠</a>️".format(self.link) if
                self.can_expired else "")
        return s + ("\n" if new_line else "")

    def insert_to_database(self):
        request = "insert into alliance_locations(link, name, type, lvl, owner_id, can_expired, expired) VALUES " \
                  "(%s, %s, %s, %s, %s, %s, %s) returning id"
        cursor.execute(request, (self.link, self.name, self.type, self.lvl, self.owner_id, self.can_expired,
                                 self.expired))
        self.id = cursor.fetchone()[0]

    def update(self):
        request = "update alliance_locations set link = %s, name = %s, type = %s, lvl = %s, owner_id = %s, " \
                  "turns_owned = %s, can_expired = %s, expired = %s " \
                  "where id = %s"
        cursor.execute(request, (self.link, self.name, self.type, self.lvl, self.owner_id, self.turns_owned,
                                 self.can_expired, self.expired,
                                 self.id))

    @staticmethod
    def get_location(location_id: int) -> 'AllianceLocation':
        request = "select link, name, type, lvl, owner_id, turns_owned, can_expired, expired from alliance_locations where id = %s " \
                  "limit 1"
        cursor.execute(request, (location_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        link, name, location_type, lvl, owner_id, turns_owned, can_expired, expired = row
        return AllianceLocation(location_id, link, name, location_type, lvl, owner_id, turns_owned, can_expired,
                                expired)

    @staticmethod
    def get_location_by_link(link: str) -> 'AllianceLocation':
        if link is None:
            return None
        request = "select id from alliance_locations where lower(link) = lower(%s) and expired is false limit 1"
        cursor.execute(request, (link,))
        row = cursor.fetchone()
        if row is None:
            return None
        return AllianceLocation.get_location(row[0])

    @staticmethod
    def get_or_create_location_by_name_and_lvl(name: str, lvl: int) -> 'AllianceLocation':
        request = "select id from alliance_locations where expired is false and lower(name) = lower(%s) and lvl = %s " \
                  "limit 1"
        cursor.execute(request, (name, lvl))
        row = cursor.fetchone()
        if row is None:
            location = AllianceLocation(None, None, name, None, lvl, None, 0, False, False)
            location.insert_to_database()
            return location
        return AllianceLocation.get_location(row[0])

    @staticmethod
    def get_active_locations() -> ['AllianceLocation']:
        request = "select id from alliance_locations where expired is false"
        cursor.execute(request)
        rows = cursor.fetchall()
        return list(map(lambda loc_id: AllianceLocation.get_location(loc_id[0]), rows))

    @staticmethod
    def increase_turns_owned():
        request = "update alliance_locations set turns_owned = turns_owned + 1 where expired is false"
        cursor.execute(request)

    @staticmethod
    def set_possible_expired():
        request = "update alliance_locations set can_expired = true where expired is false"
        cursor.execute(request)

    def __eq__(self, other):
        return self.id == other.id or self.link == other.link

