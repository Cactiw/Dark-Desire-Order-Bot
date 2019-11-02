"""
В этом модуле хранятся триггерные функции к различным ситуациям (добавлен квест, возврат со стройки и тп)
"""

from castle_files.libs.quest import Quest


def on_add_cw_quest(player, resources, quest_time):
    daily_quests: [Quest] = player.quests_info.get("daily_quests")
    if not daily_quests:
        return
    for quest in daily_quests:
        if quest.type == "collect_resource" and quest.started_time < quest_time:
            quest.update_progress(resources)
    player.update()


