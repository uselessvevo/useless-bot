"""
Description: file tools: json and that's it
Version: 0520/prototype
Author: useless_vevo
"""
import os
import json
import time
from pathlib import Path


def read_json(file):
    """
    Args:
        file (str or os.PathLike)
    Returns:
        dict
    """
    if os.path.exists(file):
        with open(file, encoding='utf-8') as output:
            return json.load(output)
    return {}


def write_json(file, data, mode='w+', exist_ok=False):
    """
    Args:
        data (dict): data to save
        file (str): file path
        mode (str): write mode
        exist_ok (bool): True - create file if doesn't exist
    """
    data = json.dumps(data, sort_keys=False, indent=4, ensure_ascii=False)
    with open(file, mode, encoding='utf-8') as output:
        output.write(data)


def get_filename_extension(file):
    return Path(file).suffix


def get_filename_without_extension(file):
    return Path(file).stem


def get_filename_path(file):
    parts = Path(file).parts
    return parts[0] if len(parts) == 1 else os.sep.join(parts[0:-1])


def normalize_module_path(path):
    return path.replace('.', os.sep)


def touch(path, make_dir=True):
    if not os.path.exists(path):
        folder = os.path.dirname(os.path.abspath(path))
        if make_dir and not os.path.exists(folder):
            os.makedirs(folder)

        with open(path, 'a'):
            os.utime(path, None)


def remove_file(*path):
    file = Path(*path).absolute()

    if file.exists():
        os.remove(file)
        return file

    return False


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print('%r  %2.2f ms' % (method.__name__, (te - ts) * 1000))

        return result

    return timed