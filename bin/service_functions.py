from globals import moscow_tz

import datetime


def count_next_battle_time():
    next_battle = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None, hour=1, minute=0, second=0,
                                                              microsecond=0)

    now = datetime.datetime.now(tz=moscow_tz).replace(tzinfo=None)
    while next_battle < now:
        next_battle += datetime.timedelta(hours=8)
    return next_battle

