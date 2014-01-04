import os
import readline

import cli
from lib import say


class do_show(str):
    """show ...
    """
    def __init__(self, rawcmd):
        rawcmd_list = rawcmd.split()
        # If there's no sub-command, print usable sub-command and return
        if len(rawcmd_list) <= 1:  # We have only 2 levels by now.
            say.available_cmds(cli.show_l2)
            return
        l2cmd = rawcmd_list[1]
        l2cmd = cli.complete_cmd(l2cmd, cli.show_l2)
        if l2cmd is None:
            return
        # Start execution
        try:
            func = getattr(self, 'do_' + l2cmd)
        except AttributeError:
            if not self.try_system_cmd(l2cmd):
                say.available_cmds(cli.show_l2)
            return
        return func()

    def try_system_cmd(self, cmd):
        real_cmd = cli.show_l2.get(cmd).get('cmd')
        if real_cmd is None:
            return False
        else:
            os.system(real_cmd)
            return True

    def do_history(self):
        cnt = 0
        for h in range(readline.get_current_history_length()):
            cnt += 1
            print ("%s%s" % (str(cnt).ljust(4, ' '),
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
