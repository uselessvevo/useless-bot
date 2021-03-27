"""
Description: text games (rps, guess, etc.)
Version: 0620/prototype
Author: useless_vevo
"""
# Standard libraries
import random
import datetime
from collections import OrderedDict

# Discord
from discord.ext import commands

# Common
from tools.locales import tr
from tools.locales import alias
from tools.discord import get_members


class RussianRoulette:
    rooms = OrderedDict({})

    @classmethod
    async def add_room(cls, ctx, bullets=6):
        player = ctx.message.author
        if not cls.rooms.get(player.id):
            cls.rooms[player.id] = {
                'name': f'{player.name}\'s room',
                'master': player.id,
                'bullets': 6,
                'fatal_bullet': random.randint(1, int(bullets)),
                'players': {}
            }
            return True
        return False

    @classmethod
    async def remove_room(cls, ctx):
        player_id = ctx.message.author.id
        if cls.rooms.get(player_id):
            del cls.rooms[player_id]
            return True
        return False

    @classmethod
    async def set_bullets_amount(cls, ctx, amount):
        if cls.rooms.get(ctx.message.author.id):
            cls.rooms[ctx.message.author.id]['bullets'] = amount

    @classmethod
    async def rooms_list(cls):
        return cls.rooms.items()

    @classmethod
    async def join_room(cls, ctx, room_number):
        player = ctx.message.author
        if cls.rooms[room_number]:
            cls.rooms[room_number]['players'].update({
                player.id: {
                    'name': player.name,
                    'is_dead': False
                }
            })
            return True
        return False


class RockPaperScissors:
    _weapons = {}


class TextGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=alias('who'), pass_context=True)
    async def who(self, ctx, *text):
        member = random.choice(await get_members(ctx))
        await ctx.send(tr('Cogs.TextGames.TextGames.WhoIsMember', ctx, True, member=member, action=' '.join(text)))

    @commands.command(aliases=alias('when'), pass_context=True)
    async def when(self, ctx):
        # the day of soviet union death. no commo
        min_year = 1991
        max_year = datetime.datetime.now().year
        start = datetime.datetime(min_year, 1, 1)
        years = max_year - min_year + 1
        end = start + datetime.timedelta(days=365 * years)
        result_date = start + (end - start) * random.random()

        if result_date >= datetime.datetime.now():
            await ctx.send(tr(
                'Cogs.TextGames.TextGames.WhenWillHappen',
                ctx=ctx,
                date=datetime.datetime.strftime(result_date, '%D'),
                time=datetime.datetime.strftime(result_date, '%d:%m:%y')
            ))
        elif result_date <= datetime.datetime.now():
            await ctx.send(tr(
                'Cogs.TextGames.TextGames.WhenHappened',
                ctx=ctx,
                date=datetime.datetime.strftime(result_date, '%D'),
                time=datetime.datetime.strftime(result_date, '%d:%m:%y')
            ))

    @commands.group(aliases=alias('rock_paper_scissors'), pass_context=False)
    async def rock_paper_scissors(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.send('ctx.invoked_subcommand error')

    @commands.group(aliases=alias('russian_roulette'), pass_context=True)
    async def russian_roulette(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(tr('Invalid Russian Roulette input!'))

    @russian_roulette.command(aliases=alias('russian_roulette.add_room'), pass_context=True)
    async def add_room(self, ctx, bullets: int = 6):
        room = await RussianRoulette.add_room(ctx, bullets)
        if room:
            await ctx.send(tr('Cogs.TextGames.TextGames.RoomWasCreated', ctx))
        else:
            await ctx.send(tr('Cogs.TextGames.TextGames.CantCreateNewRoom', ctx))

    @russian_roulette.command(aliases=alias('russian_roulette.set_bullets_amount'), pass_context=True)
    async def set_bullets_amount(self, ctx, amount: int = 8):
        await RussianRoulette.set_bullets_amount(ctx, amount)

    @russian_roulette.command(aliases=alias('russian_roulette.join_room'), pass_context=True)
    async def join_room(self, ctx, room_number: int = 0):
        await RussianRoulette.join_room(ctx, room_number)

    @russian_roulette.command(aliases=alias('russian_roulette.leave_room'), pass_context=True)
    async def leave_room(self, ctx):
        pass

    @russian_roulette.command(aliases=alias('russian_roulette.spin_bar'), pass_context=True)
    async def spin_bar(self, ctx):
        pass

    @russian_roulette.command(aliases=alias('russian_roulette.rooms_list'), pass_context=True)
    async def rooms_list(self, ctx):
        rooms = await RussianRoulette.rooms_list()
        if rooms:
            # Check if variable is dict derivatives
            await ctx.send('\n'.join(f'{k} - {v}' for (k, v) in rooms))
        else:
            await ctx.send(tr('Cogs.TextGames.TextGames.NoRoomsAvailable', ctx))


def setup(bot):
    bot.add_cog(TextGames(bot))
