"""Common libraries that suitable for anywhere.
Both my own or borrowed from internet.
"""


def hanzi2pinyin(hanzi):
    """Convert HanZi to PinYin using lib xpinyin from github"""
    from lib.xpinyin import Pinyin
    p = Pinyin()
    pinyin = ''
    for i in hanzi:
        pinyin += p.get_pinyin(i).title()
    return pinyin
