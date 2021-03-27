import os
import importlib

from tools import settings
from tools.locales import Locales


def main():
    # Do I need to make "to_check" fields and iter through keys
    # those and keys of global settings?
    if os.name == 'nt' and not os.getenv('MAGICK_HOME'):
        raise EnvironmentError('ImageMagick env var not found')
    if not settings.TOKEN:
        raise Exception('Bot token is empty!')

    Locales.load_aliases()
    Locales.load_translations()

    # Should I add token argument?
    path, obj = settings.MODULE
    application = importlib.import_module(path)
    getattr(application, obj)()


if __name__ == '__main__':
    main()
