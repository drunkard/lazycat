# -*- coding: utf-8 -*-
import string

# Color defines
OFF = '\033[0m'
BLINK = '\033[5m'

RED = '\033[0;31m'
RED_BG = '\033[00;37;41m'
RED_BLINK = '\033[05;37;41m'
RED_BOLD = '\033[1;31m'

GREEN = '\033[0;32m'
GREEN_BOLD = '\033[1;32m'

GREY = '\033[0;37m'
GREY_DARK = '\033[0;30m'
GREY_BOLD = '\033[1;37m'
GREY_DARK_BOLD = '\033[1;30m'

YELLOW = '\033[0;33m'
YELLOW_BOLD = '\033[1;33m'

BLUE = '\033[0;34m'
BLUE_BOLD = '\033[1;34m'

MAGENTA = '\033[0;35m'
MAGENTA_BOLD = '\033[1;35m'

CYAN = '\033[0;36m'
CYAN_BOLD = '\033[1;36m'

WHITE = '\033[0;37m'
WHITE_BOLD = '\033[1;37m'


all_colors = [x for x in dir()
              for i in string.ascii_uppercase
              if x.startswith(i)]
all_colors.remove('OFF')
all_colors.remove('BLINK')


# Convert all defined colors to function who named as lower named color name.
functext = """
def FUNCNAME(text):
    import inspect
    from lib import color
    if not isinstance(text, str):
        return text
    myname = inspect.stack()[0][3]
    T = myname.upper()
    try:
        color_name = getattr(color, T)
        return color_name + text + OFF
    except AttributeError:
        return text
"""
for c in all_colors:
    donefunc = functext.replace('FUNCNAME', c.lower())
    exec(donefunc)

del c, donefunc, functext
