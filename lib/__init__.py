"""Common libraries that suitable for anywhere.
Both my own or borrowed from internet.
"""


def cmd_exists(command, PATH=""):
    """Check if given command exists.
    PATH is optional.
    """
    from distutils.spawn import find_executable
    if PATH == "":
        PATH = "/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/sbin:/usr/local/bin"
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


def random_char(y):
    import string
    from random import choice
    return ''.join(choice(string.ascii_letters) for x in range(y))
