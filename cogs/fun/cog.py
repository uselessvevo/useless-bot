"""
Description: Old fun module. Will be rewritten
Version: 0620/prototype
Author: useless_vevo
"""
# Standard library
import os
import hashlib

import requests
from io import BytesIO

# Discord
import discord
from discord.ext import commands

# Pillow/PIL
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

# Common
from tools.locales import tr
from tools.locales import alias


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
        file = f'hash_{hashlib.sha1(file.encode()).hexdigest()[:8]}.jpg'
        output_file = os.path.join(self._temp_images_folder, file)
        response = requests.get(file)
        image = Image.open(BytesIO(response.content))
        image.save(output_file, 'PNG')
        return output_file

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


def setup(bot):
    bot.add_cog(Fun(bot))
