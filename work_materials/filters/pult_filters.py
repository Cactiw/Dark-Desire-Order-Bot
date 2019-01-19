from telegram.ext import BaseFilter


class FilterAttackCommand(BaseFilter):
    def filter(self, message):
        return message.text.find('⚔') == 1

filter_attack_command = FilterAttackCommand()