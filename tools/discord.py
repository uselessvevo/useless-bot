import asyncio
import random

import discord
from discord.ext import commands

from tools import settings
from tools.locales import tr


class ModifiedHelpCommand(commands.MinimalHelpCommand):
    def add_aliases_formatting(self, aliases):
        self.paginator.add_line(
            '**{}**: {}'.format(tr('Bot.AliasHeading', self.context), ', '.join(aliases)), empty=True
        )

    def get_command_signature(self, command):
        return '{0.clean_prefix}{1.qualified_name} {1.signature}'.format(self, command)


async def set_presence(bot: discord.Client, timer=1800, presence=0):
    presences = (
        discord.Status.online,
        discord.Status.idle,
        discord.Status.dnd,
        discord.Status.offline,
        discord.Status.invisible,
    )
    # Connect watchdog listener for file
    statuses = settings.STATUSES
    game = discord.Game(name=random.choice(statuses))

    while True:
        await bot.change_presence(
            status=presences[presence],
            activity=game,
        )
        await asyncio.sleep(timer)


async def get_members(ctx):
    return [m.mention for m in ctx.guild.members if not m.bot]
