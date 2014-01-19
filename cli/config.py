# -*- coding: utf-8 -*-
import logging
try:
    import cli
    from lib import color, say
except ImportError as e:
    raise e

DEBUG_FORMAT = color.grey_dark('DEBUG: %(message)s')


class do_config(list):
    def __init__(self, rawcmd):
        self.cmd_list = rawcmd.split()
        self.rawcmd = rawcmd
        try:
            l2cmd = self.cmd_list[1].replace('-', '_')
        except IndexError:
            l2cmd = ''
        # Start execution
        try:
            func = getattr(self, 'do_' + l2cmd)
            func()
        except AttributeError:
            say.available_cmds(cli.config_l2)
            return

    def do_debug(self):
        try:
            l3cmd = self.cmd_list[2].replace('-', '_')
        except IndexError:
            l3cmd = ''
        try:
            func = getattr(self, 'do_debug_' + l3cmd)
            func()
        except AttributeError:
            say.available_cmds(cli.config_debug_l3)
            return

    def do_debug_on(self):
        logging.getLogger().setLevel(10)
        print(color.yellow('Debug is on'))
        msg = """Debug messages are colored dark grey, make sure your terminal
            supports this color."""
        print(' '.join(msg.split()))

    def do_debug_off(self):
        logging.getLogger().setLevel(50)
        print(color.yellow('Debug is off'))
