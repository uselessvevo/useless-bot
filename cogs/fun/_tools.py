import hashlib


def hash_filename(file, cut=10, prefix='hash', file_format='jpg'):
    """
    Args:
        file (str): filename
        cut (int): list slice
        file_format (str)
        prefix (str): output filename prefix
    """
    return f'{prefix}_{hashlib.sha1(file.encode()).hexdigest()[:cut]}.{file_format}'
