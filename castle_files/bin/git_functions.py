"""
Здесь находятся всякие функции для работы с гитом
"""


import git
import os
import re
import datetime


def last_commits(bot, update):
    repo = git.Repo(os.getcwd())
    # master = repo.head.reference
    # repo.git.
    commits = list(repo.iter_commits('master', max_count=7))
    response = "Последние коммиты в гите:\n"
    for line in commits:
        # parse = re.match("\\S+ \\S+ (.+) \\S+ (\\d+) \\S+	(.*)", line)
        response += "<code>{} ({})</code>:\n{}\n".format(
            line.author.name, line.committed_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            line.message)
    bot.send_message(chat_id=update.message.from_user.id, text=response, parse_mode='HTML')
