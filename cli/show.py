import os
import readline

import cli
from lib import say


class do_show(str):
    """show ...
    """
    def __init__(self, line):
        full_cmd = line.split()
        # If there's no sub-command, print usable sub-command and return
        if len(full_cmd) != 2:  # We have only 2 levels by now.
            say.available_cmds(cli.show_l2)
            return
        l2cmd = full_cmd.pop()
        # If matched more/less than one, return False
        matched = []
        for c in cli.show_l2:
            if c.startswith(l2cmd):
                matched.append(c)
        if len(matched) != 1:
            say.available_cmds(cli.show_l2)
            return
        # Start execution
        try:
            func = getattr(self, matched[0])
        except AttributeError:
            say.available_cmds(cli.show_l2)
            return
        return func()

    def history(self):
        cnt = 0
        for h in range(readline.get_current_history_length()):
            cnt += 1
            print ("%s%s" % (str(cnt).ljust(4, ' '),
                             readline.get_history_item(h)))

    def ip(self):
        print("IP address configs on this host:")
        os.system('ip addr')

    def route(self):
        print("Routes on this host:")
        os.system('ip route | grep -e default -e kernel ')

    def time(self):
        os.system('cal -3; echo; date')

    def user(self):
        os.system('w -f')
