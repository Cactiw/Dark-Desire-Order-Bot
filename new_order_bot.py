from order_files.work_materials.globals import admin_ids
from aiogram import Bot, Dispatcher, executor

import asyncio

from asyncio.queues import Queue


async def send_mes(bot: Bot, chat_id, text):
    print("sending")
    await bot.send_message(chat_id=chat_id, text=text)


def order_bot_processing(token='857787013:AAErrP3z_ZIAPmirKVEMYY12YUvGjTBglJU'):
    print("in")
    bot = Bot(token=token, proxy='socks5://163.172.152.192:1080')
    dp = Dispatcher(bot)
    loop = asyncio.get_event_loop()
    # loop.call_later(1, send_mes, bot, 231900398, 'test')
    asyncio.ensure_future(send_mes(bot, 231900398, 'test'))
    loop.run_forever()

