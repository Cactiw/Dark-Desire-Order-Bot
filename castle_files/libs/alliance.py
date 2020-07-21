from castle_files.work_materials.globals import cursor, dispatcher

from castle_files.libs.guild import Guild
from castle_files.libs.alliance_location import AllianceLocation


class Alliance:

    def __init__(self, alliance_id, link, name, creator_id, assistants, hq_chat_id, active):
        self.id = alliance_id
        self.link = link
        self.name = name
        self.creator_id = creator_id
        self.assistants = assistants
        self.hq_chat_id = hq_chat_id
        self.active = active

    def add_flag_to_name(self, text: str, locations: bool = False) -> str:
        """
        Добавляет значок после каждого вхождения имени данного альянса в тексте
        :param text: str - Тест, в котором требуется произвести замену
        :param locations: bool - Следует ли добавлять эмодзи и к локации
        :return: str - Измененённый тест
        """
        s = text.replace(self.name, "{}{}".format(self.name, '🔻'))
        if locations:
            locations = self.get_alliance_locations()
            for location in locations:
                s = s.replace(location.format_name(), "🔻{}".format(location.format_name()))
        return s

    def format(self) -> str:
        return "<a href=\"t.me/share/url?url=/ga_atk_{}\">🎪{}</a>\n".format(self.link, self.name) if \
            self.link is not None else "🎪{}\n".format(self.name)

    def get_alliance_guilds(self):
        request = "select guild_id from guilds where alliance_id = %s"
        cursor.execute(request, (self.id,))
        return list(map(lambda guild_id: Guild.get_guild(guild_id[0]), cursor.fetchall()))

    def get_alliance_locations(self) -> ['AllianceLocation']:
        request = "select id from alliance_locations where owner_id = %s and expired is false"
        cursor.execute(request, (self.id,))
        return list(map(lambda loc_id: AllianceLocation.get_location(loc_id[0]), cursor.fetchall()))

    def insert_to_database(self):
        request = "insert into alliances(link, name, creator_id, assistants, hq_chat_id) VALUES " \
                  "(%s, %s, %s, %s, %s) returning id"
        cursor.execute(request, (self.link, self.name, self.creator_id, self.assistants, self.hq_chat_id))
        self.id = cursor.fetchone()[0]

    def update(self):
        request = "update alliances set link = %s, name = %s, creator_id = %s, assistants = %s, " \
                  "hq_chat_id = %s, active = %s " \
                  "where id = %s"
        cursor.execute(request, (self.link, self.name, self.creator_id, self.assistants, self.hq_chat_id, self.active,
                                 self.id))

    @staticmethod
    def get_alliance(alliance_id: int) -> 'Alliance':
        if alliance_id is None:
            return None
        request = "select link, name, creator_id, assistants, hq_chat_id, active from alliances where id = %s " \
                  "limit 1"
        cursor.execute(request, (alliance_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        link, name, creator_id, assistants, hq_chat_id, active = row
        return Alliance(alliance_id, link, name, creator_id, assistants, hq_chat_id, active)

    @staticmethod
    def get_alliance_by_link(link: str) -> 'Alliance':
        request = "select id from alliances where lower(link) = lower(%s) limit 1"
        cursor.execute(request, (link,))
        row = cursor.fetchone()
        if row is None:
            return None
        return Alliance.get_alliance(row[0])

    @staticmethod
    def get_or_create_alliance_by_name(name: str) -> 'Alliance':
        request = "select id from alliances where lower(name) = lower(%s)"
        cursor.execute(request, (name,))
        row = cursor.fetchone()
        if row is None:
            alliance = Alliance(None, None, name, None, None, None, True)
            alliance.insert_to_database()
            return alliance
        return Alliance.get_alliance(row[0])

    @staticmethod
    def get_all_alliances() -> ['Alliance']:
        request = "select id from alliances order by id asc"
        cursor.execute(request)
        return list(map(lambda alliance_id: Alliance.get_alliance(alliance_id[0]), cursor.fetchall()))

    @staticmethod
    def get_active_alliances() -> ['Alliance']:
        request = "select id from alliances where active is true order by id asc"
        cursor.execute(request)
        return list(map(lambda alliance_id: Alliance.get_alliance(alliance_id[0]), cursor.fetchall()))

    @staticmethod
    def get_player_alliance(player) -> 'Alliance':
        if player is None:
            return None
        guild = Guild.get_guild(player.guild)
        if guild is None or guild.alliance_id is None:
            return None
        return Alliance.get_alliance(guild.alliance_id)

    def __eq__(self, other):
        return self.id == other.id or self.link == other.link


class AllianceResults:
    text: str = ""
    has_hq: bool = False
    has_locations: bool = False
    old_owned: {str: int} = {}

    @classmethod
    def get_text(cls):
        return cls.text

    @classmethod
    def set_hq_text(cls, text: str):
        cls.text = text + cls.text
        cls.has_hq = True
        cls.check_and_send_results()

    @classmethod
    def set_location_text(cls, text: str):
        cls.text = cls.text + text
        cls.has_locations = True
        cls.check_and_send_results()

    @classmethod
    def check_and_send_results(cls):
        if cls.has_hq and cls.has_locations:
            for alliance in Alliance.get_all_alliances():
                if alliance.hq_chat_id is not None:
                    dispatcher.bot.send_message(
                        chat_id=alliance.hq_chat_id, parse_mode='HTML',
                        text=AllianceResults.add_flag_to_old_alliance_locations(
                            alliance.add_flag_to_name(cls.get_text()), alliance.id))
            for guild in Guild.get_all_guilds():
                if guild.settings is not None and guild.settings.get("alliance_results", False):
                    alliance = Alliance.get_alliance(guild.alliance_id) if guild.alliance_id is not None else None
                    text_to_send = alliance.add_flag_to_name(cls.get_text(), locations=True) if alliance is not None \
                        else cls.get_text()
                    dispatcher.bot.send_message(chat_id=guild.chat_id, text=text_to_send, parse_mode='HTML')

    @classmethod
    def add_flag_to_old_alliance_locations(cls, s, alliance_id):
        print(cls.old_owned)
        for name, owner_id in list(cls.old_owned.items()):
            if owner_id == alliance_id:
                s = s.replace(name, "{}🔻".format(name))
        return s

    @classmethod
    def clear(cls):
        cls.text = ""
        cls.has_hq = False
        cls.has_locations = False
        cls.old_owned.clear()

    @classmethod
    def fill_old_owned_info(cls):
        for location in AllianceLocation.get_active_locations():
            cls.old_owned.update({location.format_name(): location.owner_id})
