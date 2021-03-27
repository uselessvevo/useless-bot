"""
Description: useful tools (administration, module management, etc.)
Version: 0620/prototype
Author: useless_vevo
"""
# Standard libraries
import re

# Discord
import discord
from discord.ext import commands

# i18n module
from tools.locales import tr
from tools.locales import alias
from tools.locales import Locales

# Management
from tools.guilds import Guilds


class Administration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=alias('set_guild_prefix'), pass_context=True)
    @commands.has_permissions(administrator=True)
    async def set_guild_prefix(self, ctx, prefix):
        # if prefix is a word then add space
        if not re.match(r'[@_!#$%^&*()<>?/\|}{~:]', prefix):
            prefix += ' '

        Guilds.update_guild(ctx.message.guild.id, prefix=prefix)
        await ctx.send(tr('Cogs.Tools.Admin.PrefixHasBeenSet', ctx, prefix=prefix))

    @commands.command(aliases=alias('set_guild_locale'), pass_context=True)
    @commands.has_permissions(administrator=True)
    async def set_guild_locale(self, ctx, locale: str = None):
        """
        Set guild locale
        Args:
            ctx (common.Message): context
            locale (str): locale key code in lower case
        """
        locale = locale.lower()
        if re.match(r'[a-z\-A-Z]{5}', locale):
            if locale == Guilds.get_guild_info(ctx.message.guild.id, 'locale'):
                await ctx.send(tr('Cogs.Tools.Admin.SameLocale', ctx))
            else:
                Guilds.update_guild(ctx.message.guild.id, locale=locale)
                Locales.load_translations(locale)

                await ctx.send(tr('Cogs.Tools.Admin.LocaleHasBeenSet', ctx, locale=locale))
        else:
            await ctx.send(tr('Cogs.Tools.Admin.LocaleFormatIsIncorrect', ctx))

    @commands.command(aliases=alias('guild_info'), pass_context=True)
    async def guild_info(self, ctx):
        info = Guilds.get_guild_info(ctx.message.guild.id)
        embed = discord.Embed()
        embed.title = tr('Guild info', ctx)
        embed.description = (
            f'\n• {tr("Locale", ctx)}: {info.get("locale")}'
            f'\n\n• {tr("Prefix", ctx)}: {info.get("prefix")}'
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=alias('purge_message'), pass_context=True)
    @commands.has_permissions(administrator=True)
    async def purge_message(self, ctx, amount: int, channel: int = None):
        if channel:
            pass
        else:
            await ctx.channel.purge(limit=amount)


def setup(bot):
    bot.add_cog(Administration(bot))
