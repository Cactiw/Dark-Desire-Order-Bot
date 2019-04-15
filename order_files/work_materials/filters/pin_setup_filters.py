from telegram.ext import BaseFilter


class Filter_pinset(BaseFilter):
    def filter(self, message):
        return 'pinset' in message.text

filter_pinset = Filter_pinset()

class Filter_pinpin(BaseFilter):
    def filter(self, message):
        return 'pinpin' in message.text

filter_pinpin = Filter_pinpin()


class Filter_pinmute(BaseFilter):
    def filter(self, message):
        return 'pinmute' in message.text

filter_pinmute = Filter_pinmute()

class Filter_pindivision(BaseFilter):
    def filter(self, message):
        return 'pindivision' in message.text

filter_pindivision = Filter_pindivision()