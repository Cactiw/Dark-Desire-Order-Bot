
from castle_files.work_materials.globals import cursor, dispatcher

from castle_files.libs.guild import Guild


class Alliance:

    def __init__(self, alliance_id, link, name, creator_id, assistants, hq_chat_id):
        self.id = alliance_id
        self.link = link
        self.name = name
        self.creator_id = creator_id
        self.assistants = assistants
        self.hq_chat_id = hq_chat_id

    def add_flag_to_name(self, text: str) -> str:
        """
        Добавляет значок после каждого вхождения имени данного альянса в тексте
        :param text: str - Тест, в котором требуется произвести замену
        :return: str - Измененённый тест
        """
        return text.replace(self.name, "{}{}".format(self.name, '🔻'))


    def get_alliance_guilds(self):
        request = "select guild_id from guilds where alliance_id = %s"
        cursor.execute(request, (self.id,))
        return list(map(lambda guild_id: Guild.get_guild(guild_id), cursor.fetchall()))

    def insert_to_database(self):
        request = "insert into alliances(link, name, creator_id, assistants, hq_chat_id) VALUES " \
                  "(%s, %s, %s, %s, %s) returning id"
        cursor.execute(request, (self.link, self.name, self.creator_id, self.assistants, self.hq_chat_id))
        self.id = cursor.fetchone()[0]

    def update(self):
        request = "update alliances set link = %s, name = %s, creator_id = %s, assistants = %s, " \
                  "hq_chat_id = %s " \
                  "where id = %s"
        cursor.execute(request, (self.link, self.name, self.creator_id, self.assistants, self.hq_chat_id, self.id))

    @staticmethod
    def get_alliance(alliance_id: int) -> 'Alliance':
        request = "select link, name, creator_id, assistants, hq_chat_id from alliances where id = %s " \
                  "limit 1"
        cursor.execute(request, (alliance_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        link, name, creator_id, assistants, hq_chat_id = row
        return Alliance(alliance_id, link, name, creator_id, assistants, hq_chat_id)

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
            alliance = Alliance(None, None, name, None, None, None)
            alliance.insert_to_database()
            return alliance
        return Alliance.get_alliance(row[0])

    @staticmethod
    def get_all_alliances() -> ['Alliance']:
        request = "select id from alliances order by id asc"
        cursor.execute(request)
        return list(map(lambda alliance_id: Alliance.get_alliance(alliance_id), cursor.fetchall()))

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
                        text=alliance.add_flag_to_name(cls.get_text()))

    @classmethod
    def clear(cls):
        cls.text = ""
        cls.has_hq = False
        cls.has_locations = False


