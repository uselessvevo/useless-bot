import asyncio
import itertools
import os
import random
from functools import partial
from async_timeout import timeout
import youtube_dl as yt

import discord
from discord.ext import commands
from tools.locales import alias


ytdlopts = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}
temp_folder = os.path.join(os.getcwd(), 'temp')
ffmpegopts = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = yt.YoutubeDL(ytdlopts)


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester

        self.title = data.get('title')
        self.web_url = data.get('webpage_url')
        self.duration = data.get('duration')

        # YTDL info dicts (data) have other useful information you might want
        # https://github.com/rg3/youtube-dl/blob/master/README.md

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when you are NOT downloading.
        """
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop: str, download: bool = False):
        # filename = url.split('=')[1]
        # download: bool = os.path.exists(os.path.join(temp_folder, f'{filename}.mp3'))
        # ytdl.params['outtmpl'] = f'{temp_folder}/{filename}.%(ext)s'
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        embed = discord.Embed(
            title="",
            description=f"Queued [{data['title']}]({data['webpage_url']}) [{ctx.author.mention}]",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title']}

        return cls(discord.FFmpegPCMAudio(source), data=data, requester=ctx.author)

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """Used for preparing a stream, instead of downloading.
        Since Youtube Streaming links expire."""
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester)


class MusicPlayer:
    """A class which is assigned to each guild using the bot for Music.
    This class implements a queue and loop, which allows for different guilds to listen to different playlists
    simultaneously.
    When the bot disconnects from the Voice it's instance will be destroyed.
    """

    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None  # Now playing message
        self.volume = .5
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Our main player loop."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(300):  # 5 minutes...
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            if not isinstance(source, YTDLSource):
                # Source was probably a stream (not downloaded)
                # So we should regather to prevent stream expiration
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(f'There was an error processing your song.\n'
                                             f'```css\n[{e}]\n```')
                    continue

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            embed = discord.Embed(
                title="Now playing",
                description=f"[{source.title}]({source.web_url}) [{source.requester.mention}]",
                color=discord.Color.green()
            )
            self.np = await self._channel.send(embed=embed)
            await self.next.wait()

            # Make sure the FFmpeg process is cleaned up.
            source.cleanup()
            self.current = None

    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))


class YTPlayer(commands.Cog):
    __slots__ = ('bot', 'players')

    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    async def get_current_channel(self, ctx: commands.Context):
        return ctx.author.voice.channel

    async def get_voice_client(self, ctx: commands.Context):
        return discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

    def get_player(self, ctx):
        """Retrieve the guild player, or generate one."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player

    @commands.command(aliases=alias('play'), pass_context=True)
    async def play(self, ctx, *, search: str):
        # TODO: handle `vc.is_connected`
        if not getattr(ctx.voice_client, 'is_connected', None):
            voice_channel = await self.get_current_channel(ctx)
            await voice_channel.connect()

        player = self.get_player(ctx)
        source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=False)
        await player.queue.put(source)

    @commands.command(aliases=alias('leave'), pass_context=True)
    async def leave(self, ctx):
        if ctx.message.guild.voice_client:  # If the bot is in a voice channel
            await ctx.message.guild.voice_client.disconnect()
            await ctx.send('Bot left')
        else:
            await ctx.send("I'm not in a voice channel, use the join command to make me join")

    @commands.command(aliases=alias('pause'), pass_context=True)
    async def pause(self, ctx):
        voice = ctx.message.guild.voice_client
        if voice.is_playing():
            voice.pause()
        else:
            await ctx.send('Currently no audio is playing.')

    @commands.command(aliases=alias('resume'), pass_context=True)
    async def resume(self, ctx):
        voice = ctx.message.guild.voice_client
        if voice.is_paused():
            voice.resume()
        else:
            await ctx.send('The audio is not paused.')

    @commands.command(name='skip', description="skips to next song in queue")
    async def skip_(self, ctx):
        """Skip the song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="",
                description="I'm not connected to a voice channel",
                color=discord.Color.green()
            )
            return await ctx.send(embed=embed)

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()

    @commands.command(aliases=alias('stop'), pass_context=True)
    async def stop(self, ctx):
        ctx.message.guild.voice_client.stop()

    @commands.command(name='queue', aliases=['q', 'playlist', 'que'], description="shows the queue")
    async def queue_info(self, ctx):
        """Retrieve a basic queue of upcoming songs."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="",
                description="I'm not connected to a voice channel",
                color=discord.Color.green()
            )
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if player.queue.empty():
            embed = discord.Embed(
                title="",
                description="queue is empty", color=discord.Color.green())
            return await ctx.send(embed=embed)

        seconds = vc.source.duration % (24 * 3600)
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        if hour > 0:
            duration = "%dh %02dm %02ds" % (hour, minutes, seconds)
        else:
            duration = "%02dm %02ds" % (minutes, seconds)

        # Grabs the songs in the queue...
        upcoming = list(itertools.islice(player.queue._queue, 0, int(len(player.queue._queue))))
        fmt = '\n'.join(
            f"`{(upcoming.index(_)) + 1}.` [{_['title']}]({_['webpage_url']}) | "
            f"`{duration} Requested by: {_['requester']}`\n"
            for _ in upcoming
        )

        fmt = (f"\n__Now Playing__:\n[{vc.source.title}]({vc.source.web_url}) | "
               f"`{duration} Requested by: {vc.source.requester}`\n\n__Up Next:__\n" +
               fmt + f"\n**{len(upcoming)} songs in queue**")

        embed = discord.Embed(
            title=f'Queue for {ctx.guild.name}',
            description=fmt,
            color=discord.Color.green()
        )
        embed.set_footer(
            text=f"{ctx.author.display_name}",
            icon_url=ctx.author.avatar_url
        )

        await ctx.send(embed=embed)

    @commands.command(name='np', aliases=['song', 'current', 'currentsong', 'playing'],
                      description="shows the current playing song")
    async def now_playing(self, ctx):
        """Display information about the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="",
                description="I'm not connected to a voice channel",
                color=discord.Color.green()
            )
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if not player.current:
            embed = discord.Embed(
                title="",
                description="I am currently not playing anything",
                color=discord.Color.green()
            )
            return await ctx.send(embed=embed)

        seconds = vc.source.duration % (24 * 3600)
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        if hour > 0:
            duration = "%dh %02dm %02ds" % (hour, minutes, seconds)
        else:
            duration = "%02dm %02ds" % (minutes, seconds)

        embed = discord.Embed(
            title="",
            description=f"[{vc.source.title}]({vc.source.web_url}) "
                        f"[{vc.source.requester.mention}] | `{duration}`",
            color=discord.Color.green()
        )
        embed.set_author(icon_url=self.bot.user.avatar_url, name=f"Now Playing 🎶")
        await ctx.send(embed=embed)

    @commands.command(name='volume', aliases=['vol', 'v'], description="changes Kermit's volume")
    async def change_volume(self, ctx, *, vol: float = None):
        """Change the player volume.
        Parameters
        ------------
        volume: float or int [Required]
            The volume to set the player to in percentage. This must be between 1 and 100.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="",
                description="I am not currently connected to voice",
                color=discord.Color.green()
            )
            return await ctx.send(embed=embed)

        if not vol:
            embed = discord.Embed(
                title="",
                description=f"🔊 **{(vc.source.volume) * 100}%**",
                color=discord.Color.green()
            )
            return await ctx.send(embed=embed)

        if not 0 < vol < 101:
            embed = discord.Embed(
                title="",
                description="Please enter a value between 1 and 100",
                color=discord.Color.green()
            )
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)

        if vc.source:
            vc.source.volume = vol / 100

        player.volume = vol / 100
        embed = discord.Embed(
            title="",
            description=f'**`{ctx.author}`** set the volume to **{vol}%**',
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(YTPlayer(bot))
