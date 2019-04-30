"""
В этом модуле находится монитор, работающий в отдельном потоке в приказе в главном процессе и выполняющий обновление
кешированных ресурсов по запросу из замкового бота.
"""
from globals import update_request_queue
from order_files.bin.order import recashe_order_chats
from order_files.work_materials.globals import conn


# Сам монитор, работает до получения None из очереди update_request_queue
def castle_update_monitor():
    cursor = conn.cursor()
    guild_id = update_request_queue.get()
    while guild_id is not None:
        recashe_order_chats(new_cursor=cursor)  # Неоптимально, но это не должно вызываться часто.
        # upd: TODO: говнище, всё переделать. Могут не уйти приказы из-за этого
        guild_id = update_request_queue.get()
