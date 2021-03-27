"""
Description: i18n module/ISO 639-2 Code (modified for the uselessbot)
Version: 0620/prototype
Author: useless_vevo
TODO:
* Add file handler (with parameter "auto_reload")
"""
# Standard libraries
import os

# Base tools
from tools.fs import read_json
from tools.fs import get_filename_path
from tools.fs import normalize_module_path

# Management
from tools import settings
from tools.guilds import Guilds


class Locales:
    translations = {'alias': {}}

    @classmethod
    def load_translations(cls, locales=None, module_paths=None):
        if not locales:
            locales = {g.get('locale') for g in Guilds.guilds.values()}

        elif isinstance(locales, (list, tuple)):
            locales = set(locales)

        elif isinstance(locales, str):
            locales = [locales]

        else:
            raise TypeError(f'locales must be "list" or "tuple" type. Got {type(locales)}')

        if not module_paths:
            module_paths = {
                (os.path.split(normalize_module_path(m))[0], os.path.split(normalize_module_path(m))[1])
                for m in (*settings.COGS, settings.MODULE[0])
            }
        elif isinstance(module_paths, (list, tuple)):
            module_paths = {
                (os.path.split(normalize_module_path(m))[0], os.path.split(normalize_module_path(m))[1])
                for m in module_paths
            }
        else:
            raise TypeError(f'Modules must be "list" or "tuple" type. Got {type(module_paths)}')

        for module_folder, module_name in module_paths:
            for locale in locales:
                if locale not in cls.translations:
                    cls.translations.update({locale: {}})

                # resources/locales/<locale>/<module name>.json
                cls.translations[locale].update(
                    read_json(os.path.join(module_folder, 'locales', locale, f'{module_name}.json'))
                )

    @classmethod
    def load_aliases(cls, modules=None):
        if not modules:
            modules = {
                get_filename_path(normalize_module_path(m))
                for m in [*settings.COGS, settings.MODULE[0]]
            }
        elif isinstance(modules, (list, tuple)):
            modules = {get_filename_path(normalize_module_path(m)) for m in modules}
        else:
            raise TypeError(f'Modules must be list or tuple type. Got {type(modules)}')

        for module in modules:
            # Read "aliases.json" file
            data = read_json(os.path.join(module, 'locales', 'aliases.json'))
            cls.translations['alias'].update(data)


def tr(text, ctx=None, emoji=False, emoji_side=0, spaces=3, **kwargs):
    """
    Get translated string
    Args:
        text (str): translatable string
        ctx (common context)
        emoji (bool or str): emoji key name
        emoji_side (int): emoji side in string; left - 0, right - 1
        spaces (int): space between string and emoji
        kwargs arguments for text format
    Returns:
        formatted string or empty dict
    """
    # Get guild locale from ctx
    # If DMs
    if ctx and ctx.guild:
        locale = Guilds.get_guild_info(ctx.guild.id, 'locale', 'en-US')
        text = Locales.translations[locale].get(text, text)
    else:
        text = Locales.translations[settings.DEFAULT_LOCALE].get(text, text)
    text = text.format(**kwargs)

    if isinstance(emoji, str):
        if emoji_side == 0:
            text = f'{text}{" " * spaces}:{emoji}:'
        elif emoji_side == 1:
            text = f':{emoji}:{" " * spaces}{text}'

    return text


def alias(key):
    return Locales.translations.get('alias', {}).get(key, [])
