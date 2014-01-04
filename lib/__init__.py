"""Common libraries that suitable for anywhere.
Both my own or borrowed from internet.
"""


def cmd_exists(command, PATH=""):
    """Check if given command exists.
    PATH is optional.
    """
    import logging
    from distutils.spawn import find_executable
    if PATH == "":
        PATH = "/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/sbin:/usr/local/bin"
    logging.debug('checking if command exists: ' + command)
    if find_executable(command, path=PATH) is None:
        return False
    else:
        return True


def hanzi2pinyin(hanzi):
    """Convert HanZi to PinYin using lib xpinyin from github"""
    import string
    from lib.xpinyin import Pinyin
    p = Pinyin()
    pinyin = ''
    for i in hanzi:
        if i in string.ascii_letters:
            pinyin += i
            continue
        pinyin += p.get_pinyin(i).title()
    return pinyin


def human_readable_size(nbytes):
    import math
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    if nbytes == 0:
        return '0 B'
    rank = int((math.log10(nbytes)) / 3)
    rank = min(rank, len(suffixes) - 1)
    human = nbytes / (1024.0 ** rank)
    f = ('%.1f' % human).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[rank])


def random_char(y):
    import string
    from random import choice
    return ''.join(choice(string.ascii_letters) for x in range(y))
