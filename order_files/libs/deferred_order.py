from order_files.work_materials.globals import conn

cursor = conn.cursor()


class DeferredOrder:

    def __init__(self, deferred_id, order_id, divisions, time_set, target, defense, tactics, potions, job):
        self.deferred_id = deferred_id
        self.order_id = order_id
        self.divisions = divisions
        self.time_set = time_set
        self.target = target
        self.defense = defense
        self.tactics = tactics
        self.potions = potions
        self.job = job

    def delete(self):
        request = "delete from deferred_orders where deferred_id = %s"
        cursor.execute(request, (self.deferred_id,))
