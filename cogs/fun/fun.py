"""
Description: Old fun module. Will be rewritten
Version: 0620/prototype
Author: useless_vevo
"""
# Standard library
import os
import hashlib
import textwrap

import requests
from io import BytesIO

# Discord
import discord
from discord.ext import commands

# Pillow/PIL
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from wand.color import Color

# Wand
from wand.image import Image as WImage

# Common
from tools.locales import tr
from tools.locales import alias

from ._tools import hash_filename
from ._mediaconverter import AudioConverter


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._resources = os.path.join(os.path.dirname(__file__), 'resources')
        self._images_folder = os.path.join(self._resources, 'images')
        self._temp_images_folder = os.path.join(self._resources, 'images', 'Temp')

        if not os.path.exists(self._temp_images_folder):
            os.makedirs(self._temp_images_folder)

    # tools

    @staticmethod
    async def get_image(ctx):
        history_limit = 2000
        formats = ('png', 'gif', 'jpeg', 'jpg')

        async for c in ctx.history(limit=history_limit):
            if len(c.attachments) > 0:
                background_url = c.attachments[0].url
                background_ext = background_url.split('.')[-1]
                return background_url if background_ext in formats else None

    def save_image(self, file):
        output_file = os.path.join(self._temp_images_folder, hash_filename(file))
        response = requests.get(file)
        image = Image.open(BytesIO(response.content))
        image.save(output_file, 'PNG')
        return output_file

    async def blend_images(self, ctx, template, bg_size, bg_coord):
        """
        Old function. Will be replaced.
        Blend two images
        Args:
            ctx (common.Message): context
            template (str): template image key
            bg_size (int): background size
            bg_coord (int): background coordinates
        """
        # Replace it by async request
        response = requests.get(await self.get_image(ctx))
        foreground = os.path.join(self._images_folder, template)
        foreground = Image.open(foreground)
        background = Image.open(BytesIO(response.content))

        if 3000 in background.size:
            await ctx.send(
                tr('Cogs.Fun.Fun.ImageSizeError', ctx, w=background.size[0], h=background.size[1])
            )
        else:
            filepath = f'{self._temp_images_folder}/{template}'
            background = background.resize(bg_size)
            blended = Image.new('RGBA', foreground.size)
            blended.paste(background, bg_coord)
            blended.paste(foreground, (0, 0), foreground)
            blended.save(filepath, 'PNG')

            await ctx.send(file=discord.File(filepath))
            os.remove(filepath)

    # MediaConverter commands

    @commands.command(aliases=alias('text_to_speech'), pass_context=True)
    @commands.cooldown(2, 5, type=commands.BucketType.user)
    async def text_to_speech(self, ctx, section: str, *text: str):
        """
        Text to speech command.
        Example:
            pls <section; f.e: vox> <file1> <file2>
        Or if files contains more than one word:
            pls <section; f.e: kingpin> <file name 1>, <file name 2>
        """
        text = str(' '.join(text))
        text = text.split(',') if ',' in text else text.split(' ')

        result = await AudioConverter.text_to_speech(section, *text)
        if result:
            await ctx.send(ctx.message.author.mention, file=discord.File(result.get('output')))
            os.remove(result.get('output'))
        else:
            await ctx.send(tr('Cogs.Fun.WrongCategory', ctx))

    @commands.command(aliases=alias('text_to_speech.list'), pass_context=True)
    @commands.cooldown(2, 5, type=commands.BucketType.user)
    async def text_to_speech_list(self, ctx, section: str):
        lines = await AudioConverter.get_alphabet(section)
        lines = '"{}"'.format('", "'.join(lines.keys()))

        embed = discord.Embed()
        embed.set_author(name=tr('Cogs.Fun.TextToSpeechList', ctx))
        await ctx.author.send(embed=embed)

        for line in textwrap.wrap(lines, 500):
            # await ctx.author.send(line)
            embed.add_field(name='================', value=line)
            await ctx.author.send(embed=embed)

    # Wand commands

    @commands.command(aliases=alias('jpeg'), pass_context=True)
    @commands.cooldown(2, 3)
    async def jpeg(self, ctx, distortion: int = 3):
        image_path = self.save_image(await self.get_image(ctx))
        with WImage(filename=image_path) as image:
            image.compression_quality = distortion
            image.resolution = (image.width // 10, image.height // 10)
            image.save(filename=image_path)

            await ctx.send(file=discord.File(image_path))

            os.remove(image_path)

    @commands.command(aliases=alias('magic'), pass_context=True)
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def magic(self, ctx, scale=3):
        if scale > 10:
            scale = 3
            await ctx.send(tr('The scale argument can\'t be more than 10', ctx))

        image_path = self.save_image(await self.get_image(ctx))
        image = WImage(filename=image_path)

        image.liquid_rescale(
            width=int(image.width * 0.5),
            height=int(image.height * 0.5),
            delta_x=int(0.5 * scale) if scale else 1,
            rigidity=0
        )

        image.liquid_rescale(
            width=int(image.width * 1.5),
            height=int(image.height * 1.5),
            delta_x=scale if scale else 2,
            rigidity=0
        )
        image.save(filename=image_path)

        await ctx.send(file=discord.File(image_path))
        os.remove(image_path)

    @commands.command(aliases=alias('wand_swirl'), pass_context=True)
    @commands.cooldown(1, 3)
    async def wand_swirl(self, ctx, degree=-90):
        image_path = self.save_image(await self.get_image(ctx))

        with WImage(filename=image_path) as image:
            image.swirl(degree=degree)
            image.save(filename=image_path)

        await ctx.send(file=discord.File(image_path))
        os.remove(image_path)

    @commands.command(aliases=alias('wand_matte'), pass_context=True)
    @commands.cooldown(1, 3)
    async def wand_matte(self, ctx):
        image_path = self.save_image(await self.get_image(ctx))

        with WImage(filename=image_path) as image:
            image.resize(320, 240)
            image.matte_color = Color('ORANGE')
            image.virtual_pixel = 'tile'
            args = (
                0, 0, 30, 60, 140, 0, 110, 60,
                0, 92, 2, 90, 140, 92, 138, 90
            )
            image.distort('perspective', args)
            image.save(filename=image_path)

        await ctx.send(file=discord.File(image_path))
        os.remove(image_path)

    @commands.command(aliases=alias('minecraft'), pass_context=True)
    @commands.cooldown(1, 3)
    async def minecraft(self, ctx, *text):
        if len(text) == 0:
            text = 'Насрал в штаны'
        else:
            text = ' '.join(text)

        symbols = (
            u'абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ',
            u'abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA'
        )

        translate = {ord(a): ord(b) for a, b in zip(*symbols)}

        url = f'https://mcgen.herokuapp.com/a.php?i=1&h=%s&t=%s' % (
            text.capitalize().translate(translate),
            str(ctx.message.author.name).translate(translate)
        )

        minecraft_image = f'{self._temp_images_folder}/{hash_filename("minecraft.png")}'
        response = requests.get(url)

        image = Image.open(BytesIO(response.content))
        image.save(minecraft_image, 'PNG')

        await ctx.send(file=discord.File(minecraft_image))
        os.remove(minecraft_image)

    @commands.command(aliases=alias('bruh'), pass_context=True)
    @commands.cooldown(1, 10)
    async def bruh(self, ctx):
        for image in os.listdir(f'{self._images_folder}/bruh'):
            await ctx.send(file=discord.File(f'{self._images_folder}/bruh/{image}'))

        await ctx.send(':regional_indicator_b: :regional_indicator_r: :regional_indicator_u: :regional_indicator_h:')

    @commands.command(aliases=alias('impact-meme'), pass_context=True)
    @commands.cooldown(2, 3)
    async def impact_meme(self, ctx, *string):
        # Forked from: https://github.com/Littlemansmg/Discord-Meme-Generator
        image_path = self.save_image(await self.get_image(ctx))
        font_path = f'{self._resources}/Fonts/impact.ttf'

        if string:
            string_size = len(string) // 2
            top_string = ' '.join(string[:string_size])
            bottom_string = ' '.join(string[string_size:])

            with Image.open(image_path) as image:
                size = image.size
                font_size = int(size[1] / 5)
                font = ImageFont.truetype(font_path, font_size)
                edit = ImageDraw.Draw(image)

                # find biggest font size that works

                top_text_size = font.getsize(top_string)
                bottom_text_size = font.getsize(bottom_string)

                while top_text_size[0] > size[0] - 20 or bottom_text_size[0] > size[0] - 20:
                    font_size = font_size - 1
                    # fix it
                    font = ImageFont.truetype(font_path, font_size)
                    top_text_size = font.getsize(top_string)
                    bottom_text_size = font.getsize(bottom_string)

                # find top centered position for top text
                top_text_posx = (size[0] / 2) - (top_text_size[0] / 2)
                top_text_posy = 0
                top_text_pos = (top_text_posx, top_text_posy)

                # find bottom centered position for bottom text
                bottom_text_posx = (size[0] / 2) - (bottom_text_size[0] / 2)
                bottom_text_posy = size[1] - bottom_text_size[1] - 10
                bottom_text_pos = (bottom_text_posx, bottom_text_posy)

                # draw outlines
                # there may be a better way
                outline_range = int(font_size / 15)
                for x in range(-outline_range, outline_range + 1):
                    for y in range(-outline_range, outline_range + 1):
                        edit.text(
                            (top_text_pos[0] + x, top_text_pos[1] + y),
                            top_string,
                            (0, 0, 0),
                            font=font
                        )
                        edit.text(
                            (bottom_text_pos[0] + x, bottom_text_pos[1] + y),
                            bottom_string,
                            (0, 0, 0),
                            font=font
                        )

                edit.text(top_text_pos, top_string, (255, 255, 255), font=font)
                edit.text(bottom_text_pos, bottom_string, (255, 255, 255), font=font)
                image.save(image_path, 'PNG')

            await ctx.send(file=discord.File(image_path))
            os.remove(image_path)
        else:
            await ctx.send(tr('Cogs.Fun.Fun.ImpactMemeEmptyString', ctx))

    # Blend image commands
    # Old functions before project rewrite
    # TODO: add subcommands or generate functions

    @commands.command(aliases=alias('sex'), pass_context=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def sex(self, ctx):
        await self.blend_images(
            ctx=ctx,
            template='sex.png',
            bg_size=(646, 600),
            bg_coord=(4, 120)
        )

    @commands.command(aliases=alias('spongebob'), pass_context=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def spongebob(self, ctx):
        await self.blend_images(
            ctx=ctx,
            template='spongebob1.png',
            bg_size=(399, 299),
            bg_coord=(97, 305)
        )

    @commands.command(aliases=alias('ihadtogrind'), pass_context=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def ihadtogrind(self, ctx):
        await self.blend_images(
            ctx=ctx,
            template='ihadtogrind.png',
            bg_size=(545, 531),
            bg_coord=(15, 64),
        )

    @commands.command(aliases=alias('granpatv'), pass_context=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def granpatv(self, ctx):
        await self.blend_images(
            ctx=ctx,
            template='granpatv.png',
            bg_size=(430, 243),
            bg_coord=(45, 253),
        )

    @commands.command(aliases=alias('mrkrupp'), pass_context=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def mrkrupp(self, ctx):
        await self.blend_images(
            ctx=ctx,
            template='mrkrupp.png',
            bg_size=(566, 418),
            bg_coord=(0, 0),
        )

    @commands.command(aliases=alias('spore'), pass_context=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def spore(self, ctx):
        await self.blend_images(
            ctx=ctx,
            template='spore.png',
            bg_size=(1024, 1024),
            bg_coord=(0, 0),
        )

    @commands.command(aliases=alias('spywow'), pass_context=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def spywow(self, ctx):
        await self.blend_images(
            ctx=ctx,
            template='spywow.png',
            bg_size=(600, 339),
            bg_coord=(0, 0),
        )

    @commands.command(aliases=alias('thisguy'), pass_context=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def thisguy(self, ctx):
        await self.blend_images(
            ctx=ctx,
            template='thisguy.png',
            bg_size=(520, 451),
            bg_coord=(0, 191),
        )

    @commands.command(aliases=alias('thiswoman'), pass_context=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def thiswoman(self, ctx):
        await self.blend_images(
            ctx=ctx,
            template='thiswoman.png',
            bg_size=(964, 467),
            bg_coord=(0, 444),
        )

    @commands.command(aliases=alias('icecream'), pass_context=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def icecream(self, ctx):
        await self.blend_images(
            ctx=ctx,
            template='icecream.png',
            bg_size=(309, 261),
            bg_coord=(202, 250),
        )

    @commands.command(aliases=alias('obstetrician'), pass_context=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def obstetrician(self, ctx):
        await self.blend_images(
            ctx=ctx,
            template='obstetrician.png',
            bg_size=(962, 727),
            bg_coord=(22, 13),
        )

    @commands.command(aliases=alias('anus'), pass_context=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def anus(self, ctx):
        await self.blend_images(
            ctx=ctx,
            template='anus.png',
            bg_size=(225, 191),
            bg_coord=(0, 0),
        )

    @commands.command(aliases=alias('dream'), pass_context=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def dream(self, ctx):
        await self.blend_images(
            ctx=ctx,
            template='dream.png',
            bg_size=(685, 450),
            bg_coord=(0, 308),
        )

    @commands.command(aliases=alias('nope'), pass_context=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def nope(self, ctx):
        await self.blend_images(
            ctx=ctx,
            template='nope.png',
            bg_size=(315, 447),
            bg_coord=(338, 14),
        )

    @commands.command(aliases=alias('heroes'), pass_context=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def heroes(self, ctx):
        await self.blend_images(
            ctx=ctx,
            template='heroes.png',
            bg_size=(428, 412),
            bg_coord=(0, 0),
        )

    @commands.command(aliases=alias('dickgrow'), pass_context=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def dickgrow(self, ctx):
        await self.blend_images(
            ctx=ctx,
            template='dickgrow.jpg',
            bg_size=(668, 345),
            bg_coord=(0, 0),
        )


def setup(bot):
    bot.add_cog(Fun(bot))
