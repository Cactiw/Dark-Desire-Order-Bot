from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from castle_files.work_materials.globals import dispatcher, updater, conn

from castle_files.work_materials.filters.profile_filters import filter_is_hero

from castle_files.bin.profile import hero


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Привет! Пришли мне форвард /hero из @chatwarsbot!")



def castle_bot_processing():
    dispatcher.add_handler(CommandHandler('start', start))

    dispatcher.add_handler(MessageHandler(Filters.text & filter_is_hero, hero))

    updater.start_polling(clean=False)

    updater.idle()

    conn.close()
