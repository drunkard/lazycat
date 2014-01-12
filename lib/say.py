# -*- coding: utf-8 -*-
"""This module contains common messages used in this program."""
import logging
import sys
try:
    from lib import color, maxlen
except ImportError as e:
    sys.exit(str(e) + "ERROR: some modules import failed")


class available_cmds(object):
    """Print all available commands in data objects.
    Both list and dict are supported."""
    def __init__(self, cmdlist, justshow=[], msg=""):
        self.cmdlist = cmdlist
        self.justshow = sorted(justshow)
        if msg == "":
            msg = "All available commands:"
        print(msg)
        if isinstance(cmdlist, dict):
            logging.debug('print using dict')
            self.print_dict()
        elif isinstance(cmdlist, list):
            logging.debug('print using list')
            self.print_list()

    def print_dict(self):
        if self.justshow:
            align = maxlen(self.justshow) + 4
            k = self.justshow
        else:
            # No filter, print all
            align = maxlen(self.cmdlist.keys()) + 4
            k = sorted(self.cmdlist.keys())
        for i in k:
            desc = self.cmdlist.get(i).get('desc')
            print('  %s%s' % (i.ljust(align), desc))

    def print_list(self):
        # Print out sorted usable command list
        if len(self.cmdlist) > 0:
            for c in sorted(self.cmdlist):
                print("  " + str(c))


def internal_error():
    print('%sInternal error in program, please report to developer%s' %
          (color.RED_BLINK, color.OFF))


def no_cmd(cmdname):
    print("%sUnknown command:%s %s" %
          (color.RED_BG, color.OFF, cmdname.replace('_', '-')))


def no_sys_cmd(cmdname):
    print("System command %s%s%s is not usable, please notify developer." %
          (color.RED_BLINK, cmdname, color.OFF))


def nofile(f, prefix=""):
    """Say standard words: No such file or directory"""
    if prefix:
        print("%s: %s: No such file or directory" % (str(prefix), f))
    else:
        print("%s: No such file or directory" % f)


def not_implemented():
    print("%sThis is planned, but not implemented yet.%s" %
          (color.CYAN, color.OFF))
