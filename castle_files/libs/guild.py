"""
Этот модуль содержит класс Гильдия и методы работы с ней, в том числе и с БД.
"""
from castle_files.work_materials.globals import cursor

import logging
import traceback


# Гильдия, содержит открытые поля - id в базе данных, тэг, список айдишников(!) членов гильдии,
class Guild:
    def __init__(self, guild_id, tag, members, commander_id, division, chat_id, chat_name, invite_link, orders_enabled,
                 pin_enabled, disable_notification):
        self.id = guild_id
        self.tag = tag
        self.members = members
        self.commander_id = commander_id
        self.division = division
        self.chat_id = chat_id
        self.chat_name = chat_name
        self.invite_link = invite_link
        self.orders_enabled = orders_enabled
        self.pin_enabled = pin_enabled
        self.disable_notification = disable_notification

    # Метод получения гильдии из БД
    @staticmethod
    def get_guild(guild_tag=None, guild_id=None):
        request = "select guild_tag, guild_id, chat_id, members, commander_id, division, chat_name, invite_link, " \
                  "orders_enabled, pin_enabled, disable_notification from guilds "
        if guild_tag:
            request += "where guild_tag = %s"
            cursor.execute(request, (guild_tag,))
        elif guild_id:
            request += "where guild_id = %s"
            cursor.execute(request, (guild_id,))
        else:
            return None
        row = cursor.fetchone()
        if row is None:
            return None
        guild_tag, guild_id, chat_id, members, commander_id, division, chat_name, invite_link, orders_enabled, \
            pin_enabled, disable_notification = row
        guild = Guild(guild_id, guild_tag, members, commander_id, division, chat_id, chat_name, invite_link,
                      orders_enabled, pin_enabled, disable_notification)
        return guild

    # Метод для обновления информации о гильдии в БД
    def update_to_database(self):
        request = "update guilds set members = %s, commander_id = %s, division = %s, chat_id = %s, chat_name = %s, " \
                  "invite_link = %s, orders_enabled = %s, pin_enabled = %s,disable_notification = %s " \
                  "where guild_tag = %s"
        try:
            cursor.execute(request, (self.members, self.commander_id, self.division, self.chat_id, self.chat_name,
                                     self.invite_link, self.orders_enabled, self.pin_enabled, self.disable_notification,
                                     self.tag))
        except Exception:
            logging.error(traceback.format_exc())
            return -1
        return 0

    def create_guild(self):
        request = "insert into guilds(guild_tag) values (%s) returning guild_id"
        cursor.execute(request, (self.tag,))
        row = cursor.fetchone()
        self.id = row[0]
        return self
