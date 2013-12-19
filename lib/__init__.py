"""Common libraries that suitable for anywhere.
Both my own or borrowed from internet.
"""


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
