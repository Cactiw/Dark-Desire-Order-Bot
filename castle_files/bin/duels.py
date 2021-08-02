from castle_files.libs.player import Player
from castle_files.libs.duels import Duels
from castle_files.libs.guild import Guild


def my_duels(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if not player:
        print('no player')
        return
    if player.api_info and player.api_info.get('in_game_id'):
        cw_id = player.api_info.get('in_game_id')

        duels, date = Duels.today_duels(cw_id)

        text = format_myduels(duels, date, player, cw_id)

        bot.send_message(chat_id=mes.chat_id, text=text)


def myguild_duels(bot, update):
    mes = update.message
    player = Player.get_player(mes.from_user.id)
    if not player:
        return
    guild = Guild.get_guild(guild_id=player.guild)
    if not guild:
        return

    duels, date = Duels.today_guilds_duels(guild.tag)
    text = format_guild_duels(duels, date, guild.tag)
    bot.send_message(chat_id=mes.chat_id, text=text)


def format_myduels(duels, date, player, cw_id):

    text = '{} {}\n duels on {}/{}'.format(player.lvl, player.nickname, date.day, date.month)
    if len(duels):
        win_count = 0
        win_text = ''
        lose_count = 0
        lose_text = ''
        lvl = 0
        for duel in duels:
            if cw_id == duel.winner_id:
                win_count += 1
                lvl = duel.winner_level
                if duel.loser_tag:
                    guild = r'[{}]'.format(duel.loser_tag)
                else:
                    guild = ''
                win_text += '{} {} {} {}\n'.format(duel.loser_level, duel.loser_castle, guild, duel.loser_name)
            elif cw_id == duel.loser_id:
                lose_count += 1
                lvl = duel.loser_level
                if duel.winner_tag:
                    guild = r'[{}]'.format(duel.winner_tag)
                else:
                    guild = ''
                lose_text += '{} {} {} {}\n'.format(duel.winner_level, duel.winner_castle, guild, duel.winner_name)
        text = '{} {}\n'.format(lvl, player.nickname)
        text += 'duels on {}/{}\n\n'.format(date.day, date.month)
        text += '❤️ Won {}\n'.format(win_count)
        text += win_text
        text += '\n'

        text += '💔 Lost {}\n'.format(lose_count)
        text += lose_text
        text += '\n'
        text += 'Total {}/{}'.format(win_count, lose_count)

    else:
        print('no duels')
        text += '\nDuels not found'

    return text


def format_guild_duels(duels, date, guild_tag):
    text = '[{}] duels on {}/{}'.format(guild_tag, date.day, date.month)
    if len(duels):
        guildmates = {}
        for duel in duels:
            if guild_tag == duel.winner_tag:
                if not guildmates.get(duel.winner_name, False):
                    guildmates[duel.winner_name] = {}
                    guildmates[duel.winner_name]['lvl'] = duel.winner_level
                    guildmates[duel.winner_name]['win'] = 1
                    guildmates[duel.winner_name]['lose'] = 0
                else:
                    guildmates[duel.winner_name]['win'] += 1
            elif guild_tag == duel.loser_tag:
                if not guildmates.get(duel.loser_name, False):
                    guildmates[duel.loser_name] = {}
                    guildmates[duel.loser_name]['lvl'] = duel.loser_level
                    guildmates[duel.loser_name]['win'] = 0
                    guildmates[duel.loser_name]['lose'] = 1
                else:
                    guildmates[duel.loser_name]['lose'] += 1
        text = r'[{}] duels on {}/{}'.format(guild_tag, date.day, date.month)
        text += '\n\n'
        won = 0
        lost = 0
        # guildmates = guildmates.items().sort(key=lambda x: (x[1]['win']))
        sorted_keys = sorted(guildmates, key=lambda x: (guildmates[x]['win']), reverse=True)
        for key in sorted_keys:
            value = guildmates.get(key)
            won += value.get('win', 0)
            lost += value.get('lose', 0)
            text += '{}/{} {} {}\n'.format(
                value.get('win', 0), value.get('lose', 0), key, value.get('lvl'))

        text += '\n'
        text += '{} fighters won {} lost {}'.format(len(guildmates.keys()), won, lost)
        # if '_' in text:
        #     text = text.replace('_', r'\_')
    return text
