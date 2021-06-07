from telethon import TelegramClient, events
import asyncio

from config import forward_api_id, forward_api_hash


async def main():

    session = "./current.session"
    async with TelegramClient(session, forward_api_id, forward_api_hash) as client:

        @client.on(events.NewMessage(chats=(-1001369273162,)))
        async def handler(event: events.NewMessage.Event):
            await client.send_message(-1001274086574, event.message.message)

        await client.run_until_disconnected()


asyncio.get_event_loop().run_until_complete(main())
