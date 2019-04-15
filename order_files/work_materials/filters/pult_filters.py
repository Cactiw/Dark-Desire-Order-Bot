from telegram.ext import BaseFilter


class FilterAttackCommand(BaseFilter):
    def filter(self, message):
        return message.text.find('⚔') == 1

filter_attack_command = FilterAttackCommand()

class FilterRemoveOrder(BaseFilter):
    def filter(self, message):
        return message.text.find('/remove_order') == 0


filter_remove_order = FilterRemoveOrder()
