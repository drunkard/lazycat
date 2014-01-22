# -*- coding: utf-8 -*-
import logging
import os
import readline

import cli
from lib import say


class do_show(str):
    """show ...
    """
    def __init__(self, rawcmd):
        self.rawcmd = rawcmd
        rawcmd_list = rawcmd.split()
        # If there's no sub-command, print usable sub-command and return
        if len(rawcmd_list) <= 1:  # We have only 2 levels by now.
            say.available_cmds(cli.show_l2)
            return
        l2cmd = rawcmd_list[1]
        # Start execution
        try:
            func = getattr(self, 'do_' + l2cmd)
            func()
        except AttributeError:
            if self.try_system_cmd(l2cmd) is None:
                prefix_matches = [c for c in cli.show_l2.keys()
                                  if c and c.startswith(l2cmd)]
                say.available_cmds(cli.show_l2, justshow=prefix_matches)
            return

    def do_history(self):
        cnt = 0
        for h in range(readline.get_current_history_length()):
            cnt += 1
            print ("%s%s" % (str(cnt).ljust(5, ' '),
                             readline.get_history_item(h)))

    def do_shortcuts(self):
        u"""终端快捷键：
        ?               显示可用命令

        Ctrl-A          光标移到行首
        Ctrl-E          光标移到行尾
        Ctrl-B | Left   左移光标
        Ctrl-F | Right  右移光标
        Ctrl-P | Up     前一个命令
        Ctrl-N | Down   后一个命令

        Backspace       删除左边一个字符
        Del | Ctrl-D    删除右边一个字符

        Ctrl-U          剪切光标到行首之间的字符
        Ctrl-K          剪切光标到行尾之间的字符
        Ctrl-W          剪切光标左边一个词
        Alt-D           剪切光标右边一个词

        Ctrl-R          向前搜索历史命令
        Return          把命令发给终端
        """
        try:
            print(self.do_shortcuts.__doc__.replace('\n        ', '\n'))
        except Exception as e:
            print(e)

    def try_system_cmd(self, cmd):
        logging.debug('routed to do_show.try_system_cmd: %s' % cmd)
        try:
            real_cmd = cli.show_l2.get(cmd).get('cmd')
            os.system(real_cmd)
            return True  # could be anything but None
        except AttributeError:
            say.no_cmd(self.rawcmd)
            return None
