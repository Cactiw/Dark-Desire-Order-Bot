"""
В этом модуле хранятся триггерные функции к различным ситуациям (добавлен квест, возврат со стройки и тп)
"""

from castle_files.libs.quest import Quest

import datetime


def on_add_cw_quest(player, resources, quest_time):
    daily_quests: [Quest] = player.quests_info.get("daily_quests")
    if not daily_quests:
        return
    for quest in daily_quests:
        if quest.type == "collect_resource" and quest.started_time < quest_time:
            quest.update_progress(resources)
    player.update()


def update_quest_type(player, quest_type, update_value, time_check=None):
    if isinstance(time_check, datetime.datetime):
        time_check = time_check.timestamp()
    daily_quests: [Quest] = player.quests_info.get("daily_quests")
    if not daily_quests:
        return
    for quest in daily_quests:
        if quest.type == quest_type:
            if time_check is None or quest.started_time < time_check:
                quest.update_progress(update_value)
    player.update()


def on_king_audience(player):
    update_quest_type(player, "feedback_request_king", 1)


def on_duty_request(player):
    update_quest_type(player, "feedback_request_duty", 1)


def on_mid_request(player):
    update_quest_type(player, "feedback_request_mid", 1)


def on_resource_return(player, resource):
    res = {"wood": "🌲Wood", "stone": "⛰Stone"}
    resource = res.get(resource)
    update_quest_type(player, "castle_collect_resource", {resource: 1})


def on_add_report(player, report_time):
    update_quest_type(player, "reports", 1, time_check=report_time)


def on_doc_status(player):
    update_quest_type(player, "doc_statuses", 1)


def on_won_arena(player, won_time):
    update_quest_type(player, "arena_win", 1, time_check=won_time)
