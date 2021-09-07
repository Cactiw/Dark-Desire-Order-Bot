from castle_files.work_materials.globals import conn, moscow_tz

import datetime
from datetime import timedelta, timezone


class Duels:
    attributes = ['winner_id', 'winner_name', 'winner_tag', 'winner_castle', 'winner_level',
                  'loser_id', 'loser_name', 'loser_tag', 'loser_castle', 'loser_level', 'date']

    last_update = None

    def __init__(self, winner_id, winner_name, winner_tag, winner_castle, winner_level, loser_id, loser_name,
                 loser_tag, loser_castle, loser_level, date):
        self.winner_id = winner_id
        self.winner_name = winner_name
        self.winner_tag = winner_tag
        self.winner_castle = winner_castle
        self.winner_level = winner_level

        self.loser_id = loser_id
        self.loser_name = loser_name
        self.loser_tag = loser_tag
        self.loser_castle = loser_castle
        self.loser_level = loser_level

        self.date = date

    @classmethod
    def update_or_create_duel(cls, duel_dict: dict):

        timestamp = duel_dict['date']

        # date = datetime.datetime.fromtimestamp(
        #     int(timestamp / 1000)).replace(tzinfo=local_tz)
        # date = date.astimezone(moscow_tz)

        duel = cls.get_duel(date=timestamp, winner_id=duel_dict['winner_id'], loser_id=duel_dict['loser_id'])
        new = False
        if duel is None:
            duel = cls(*cls.attributes)
            new = True
        for attribute in cls.attributes:
            setattr(duel, attribute, duel_dict.get(attribute, None))

        if new:
            duel.create()

    @staticmethod
    def get_duel(date: datetime, winner_id: str, loser_id: str):

        cursor = conn.cursor()
        request = "select winner_id, winner_name, winner_tag, winner_castle, winner_level, loser_id," \
                  "loser_name, loser_tag, loser_castle, loser_level, date " \
                  "from duels " \
                  "where winner_id = %s and loser_id = %s and date = %s limit 1"
        cursor.execute(request, (winner_id, loser_id, date))
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            return None
        duel = Duels(*row)
        return duel

    @staticmethod
    def today_duels(player_id):
        date = datetime.datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(moscow_tz)
        if date.hour < 13:
            date = date - timedelta(days=1)
        date = date.replace(hour=13, minute=0, second=0)

        timestamp = int(date.timestamp())

        cursor = conn.cursor()
        request = "select winner_id, winner_name, winner_tag, winner_castle, winner_level, loser_id," \
                  "loser_name, loser_tag, loser_castle, loser_level, date " \
                  "from duels " \
                  "where (winner_id = %s or loser_id = %s) and date > %s"
        cursor.execute(request, (player_id, player_id, timestamp))
        rows = cursor.fetchall()
        cursor.close()
        duels = [Duels(*row) for row in rows]
        return duels, date

    @staticmethod
    def today_guilds_duels(guild_tag):
        date = datetime.datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(moscow_tz)
        if date.hour < 13:
            date = date - timedelta(days=1)
        date = date.replace(hour=13, minute=0, second=0)

        timestamp = int(date.timestamp())
        cursor = conn.cursor()
        request = "select winner_id, winner_name, winner_tag, winner_castle, winner_level, loser_id," \
                  "loser_name, loser_tag, loser_castle, loser_level, date " \
                  "from duels " \
                  "where (winner_tag = %s or loser_tag = %s) and date > %s"
        cursor.execute(request, (guild_tag, guild_tag, timestamp))
        rows = cursor.fetchall()
        cursor.close()
        duels = [Duels(*row) for row in rows]
        return duels, date

    def create(self):
        request = "insert into duels(winner_id, winner_name, winner_tag, winner_castle, winner_level, loser_id, loser_name, loser_tag," \
                  "loser_castle, loser_level, date) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor = conn.cursor()

        cursor.execute(request, (
            self.winner_id, self.winner_name, self.winner_tag, self.winner_castle, self.winner_level, self.loser_id,
            self.loser_name, self.loser_tag, self.loser_castle, self.loser_level, self.date))
        cursor.close()
