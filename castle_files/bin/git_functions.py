"""
Здесь находятся всякие функции для работы с гитом
"""


import git
import os
import re
import datetime


def last_commits(bot, update):
    repo = git.Repo(os.getcwd())
    master = repo.head.reference
    commits = master.log()[-1:-6:-1]
    response = "Последние коммиты в гите:\n"
    for line in commits:
        # parse = re.match("\\S+ \\S+ (.+) \\S+ (\\d+) \\S+	(.*)", line)
        response += "<code>{} ({})</code>:\n{}\n\n".format(
            line.actor.name, datetime.datetime.fromtimestamp(int(line.time[0])).strftime('%Y-%m-%d %H:%M:%S'),
            line.message.partition(": ")[2])
    bot.send_message(chat_id=update.message.from_user.id, text=response, parse_mode='HTML')
