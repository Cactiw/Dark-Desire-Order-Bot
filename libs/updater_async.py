from telegram.ext import Updater

class AsyncUpdater(Updater):

    def __init__(self,
                 token=None,
                 base_url=None,
                 workers=4,
                 bot=None,
                 private_key=None,
                 private_key_password=None,
                 user_sig_handler=None,
                 request_kwargs=None,
                 persistence=None):
        super(AsyncUpdater, self).__init__(token=token, base_url=base_url, workers=workers, bot=bot,
                                           private_key = private_key, private_key_password=private_key_password,
                                           user_sig_handler=user_sig_handler, request_kwargs = request_kwargs)
                                           #persistence = persistence)    #   Требуется на гите, но не требуется тут (?)

    def stop(self):
        try:
            self.bot.stop()
        except AttributeError:
            pass
        super(AsyncUpdater, self).stop()
