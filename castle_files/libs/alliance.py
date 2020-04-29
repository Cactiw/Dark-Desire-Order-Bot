
from castle_files.work_materials.globals import cursor


class Alliance:

    def __init__(self, alliance_id, link, name, creator_id, assistants, hq_chat_id):
        self.id = alliance_id
        self.link = link
        self.name = name
        self.creator_id = creator_id
        self.assistants = assistants
        self.hq_chat_id = hq_chat_id


    def insert_to_database(self):
        request = "insert into alliances(link, name, creator_id, assistants, hq_chat_id) VALUES " \
                  "(%s, %s, %s, %s, %s) returning id"
        cursor.execute(request, (self.name, self.creator_id, self.assistants, self.hq_chat_id))
        self.id = cursor.fetchone()[0]

    def update(self):
        request = "update alliances set link = %s, name = %s, creator_id = %s, assistants = %s, " \
                  "hq_chat_id = %s " \
                  "where id = %s"
        cursor.execute(request, (self.link, self.name, self.creator_id, self.assistants, self.hq_chat_id, self.id))

    @staticmethod
    def get_alliance(alliance_id: int):
        request = "select link, name, creator_id, assistants, hq_chat_id from alliances where id = %s " \
                  "limit 1"
        cursor.execute(request, (alliance_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        link, name, creator_id, assistants, hq_chat_id = row
        return Alliance(alliance_id, link, name, creator_id, assistants, hq_chat_id)

    @staticmethod
    def get_or_create_alliance_by_name(name: str):
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
        return map(lambda alliance_id: Alliance.get_alliance(alliance_id), cursor.fetchall())
