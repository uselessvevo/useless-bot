import time
from datetime import datetime

import discord
from discord.ext import commands

from bot import settings
from tools.locales import tr
from tools.guilds import Guilds
from tools.discord import set_presence


class UselessBot(commands.Bot):
    
    def __init__(self):
        super().__init__(
            command_prefix=self._get_prefix,
            case_insensitive=settings.CASE_SENSITIVE,
        )
        
        for module in getattr(settings, 'COGS', []):
            try:
                self.load_extension(module)
            except discord.ext.commands.errors.ExtensionNotLoaded as e:
                raise discord.ext.commands.errors.ExtensionNotLoaded(f'Failed to load "{module}", traceback: {e}')
        
        self.run(settings.TOKEN)
        
    async def _get_prefix(self, bot, ctx):
        if ctx.guild:
            return [Guilds.get_guild_info(ctx.guild.id, 'prefix'), settings.DEFAULT_PREFIX]
        return settings.DEFAULT_PREFIX
    
    async def on_guild_join(self, guild):
        Guilds.insert_guild(
            id=guild.id,
            locale=settings.DEFAULT_LOCALE,
            prefix=settings.DEFAULT_PREFIX
        )
        
        logs_channel = self.get_channel(settings.LOG_ROOMS['messages'])
        embed = discord.Embed()
        embed.set_author(name='New guild')
        embed.colour = discord.Color.from_rgb(169, 245, 110)
        embed.description = f'Bot has been added to the new channel ({guild.name}, {guild.id})'
        
        await logs_channel.send(embed=embed)
        for channel in guild.text_channel:
            if channel.permissions_for(guild.me).send_message:
                await channel.send('Hello! :tennis:')
            break
            
    async def on_guild_remove(self, guild):
        """ If bot was removed from the server """
        Guilds.delete_guild(guild.id)

        logs_channel = self.get_channel(settings.LOG_ROOMS['messages'])
        embed = discord.Embed()
        embed.set_author(name='Guild has been removed')
        embed.colour = discord.Color.from_rgb(245, 110, 110)
        embed.description = f'Bot has been deleted from the guild ({guild.name}, {guild.id})'

        await logs_channel.send(embed=embed)

    async def on_message(self, ctx: discord.Message):
        """
        (AVATAR) [Type of event]
        User sent message in <#channel.mention>
        [Content title]
        Content
        [If File title]
        File URL
        """

        if not ctx.author.bot:
            logs_channel = self.get_channel(settings.LOG_ROOMS['messages'])

            embed = discord.Embed()
            embed.colour = discord.Color.from_rgb(110, 162, 245)

            embed.set_author(
                name=tr('Bot.Message', ctx),
                icon_url=ctx.author.avatar_url
            )

            embed.description = tr(
                'Bot.EventOccurredIn',
                ctx=ctx,
                author=ctx.author.mention,
                guild=ctx.guild.name if ctx.guild else ctx.author.mention,
                channel=ctx.channel.mention if not isinstance(ctx.channel, discord.channel.DMChannel) else ctx.author.mention
            )

            if ctx.content:
                embed.add_field(
                    name=tr('Bot.Message', ctx),
                    value=ctx.content,
                    inline=False
                )
            if ctx.attachments:
                embed.add_field(
                    name=tr('Bot.File', ctx),
                    value=ctx.attachments[0].proxy_url,
                    inline=False
                )

            await logs_channel.send(embed=embed)
            await self.process_commands(ctx)

    async def on_message_edit(self, ctx_before, ctx_after):
        if not ctx_before.author.bot:
            logs_channel = self.get_channel(settings.LOG_ROOMS['messages'])

            embed = discord.Embed()
            embed.colour = discord.Color.from_rgb(245, 124, 110)

            embed.set_author(
                name=tr('Bot.Edited', ctx_before),
                icon_url=ctx_before.author.avatar_url
            )

            if not isinstance(ctx_before.channel, discord.channel.DMChannel):
                channel = ctx_before.channel.mention
            else:
                channel = ctx_before.author.mention

            embed.description = tr(
                'Bot.EventOccurredIn',
                ctx=ctx_before,
                author=ctx_before.author.mention,
                guild=ctx_before.guild.name if ctx_before.guild else ctx_before.author.mention,
                channel=channel
            )

            embed.add_field(
                name=tr('Before', ctx_before),
                value=ctx_before.content,
                inline=False
            )
            embed.add_field(
                name=tr('After', ctx_after),
                value=ctx_after.content,
                inline=False
            )

            await logs_channel.send(embed=embed)

    async def on_message_delete(self, ctx):
        if not ctx.author.bot:
            logs_channel = self.get_channel(settings.LOG_ROOMS['messages'])

            embed = discord.Embed()
            embed.colour = discord.Color.from_rgb(245, 124, 110)

            embed.set_author(
                name=tr('Bot.Deleted', ctx),
                icon_url=ctx.author.avatar_url
            )

            embed.description = tr(
                'Bot.EventOccurredIn',
                ctx=ctx,
                author=ctx.author.mention,
                guild=ctx.guild.name if ctx.guild else ctx.author.mention,
                channel=ctx.channel.mention if not isinstance(ctx.channel, discord.channel.DMChannel) else ctx.author.mention
            )

            embed.add_field(
                name=tr('Bot.Message', ctx),
                value=ctx.content,
                inline=False
            )

            await logs_channel.send(embed=embed)

    async def on_command(self, ctx):
        await ctx.trigger_typing()

    async def on_command_error(self, ctx, error):
        logs_channel = self.get_channel(settings.LOG_ROOMS['errors'])
        message = tr('Error', ctx)

        if isinstance(error, commands.CommandOnCooldown):
            member = ctx.message.author.mention
            message = tr('Bot.PleaseWait', ctx, member=member)

        elif isinstance(error, commands.UserInputError):
            message = tr('Bot.InvalidInput', ctx, arg=ctx.command)

        elif isinstance(error, commands.BadArgument):
            message = tr('Bot.BadCommandArgument', arg=ctx.command.content)

        elif isinstance(error, commands.CommandNotFound):
            message = tr('Bot.CommandNotFound', ctx, arg=ctx.message.content)

        elif isinstance(error, commands.CommandInvokeError):
            message = f'{tr("Bot.CommandInvokeError", ctx)}: {error.original}'

        elif isinstance(error, UnboundLocalError):
            message = f'{tr("Bot.LocalError", ctx)}: {error}'

        title = tr('Error', ctx)
        embed_logs = discord.Embed()
        embed_logs.set_author(
            name=title,
            icon_url=ctx.message.author.avatar_url
        )
        embed_logs.colour = discord.Color.from_rgb(252, 197, 114)
        channel = ctx.guild.id if ctx.guild else 'DM'
        embed_logs.description = f'{ctx.message.author.mention} in {channel}\n{message}'
        embed_logs.set_footer(text=f'{datetime.fromtimestamp(time.time())}')

        await ctx.send(message)
        await logs_channel.send(embed=embed_logs)

    # Tasks

    async def on_ready(self):
        self.loop.create_task(set_presence(bot=self, presence='online'))
        print('* Ready')
