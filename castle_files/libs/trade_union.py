from castle_files.work_materials.globals import cursor


class TradeUnion:

    def __init__(self, id, creator_id, name, players, view_link):
        self.id = id
        self.creator_id = creator_id
        self.name = name
        self.players = players
        self.view_link = view_link

    @staticmethod
    def get_union(union_id=None, creator_id=None, chat_id=None):
        request = "select id, creator_id, name, players, view_link from trade_unions where "
        arg = None
        if union_id is not None:
            request += "id = %s"
            arg = union_id
        elif creator_id is not None:
            request += "creator_id = %s"
            arg = creator_id
        elif chat_id is not None:
            request += "chat_id = %s"
            arg = chat_id
        cursor.execute(request, (arg,))
        row = cursor.fetchone()
        if row is None:
            return None
        return TradeUnion(row[0], row[1], row[2], row[3], row[4])

    def update_to_database(self):
        request = "update trade_unions set creator_id = %s, name = %s, players = %s, view_link = %s where id = %s"
        cursor.execute(request, (self.creator_id, self.name, self.players, self.view_link, self.id,))
        return 0
