#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This program is a pseudo-shell and gives the user interactive control.
The entire ssh/telnet session is logged to a file, others won't be logged.
"""

import os
import readline
import sys
import threading
import time

import signal
import fcntl
import termios
import struct

try:
    import pexpect
    import cli
    from cli import history
    from lib import cmd_exists, color, say
except ImportError as e:
    raise ImportError(e + """\033[05;37;41m

A critical module was not found. Probably this operating system does not
support it. Pexpect is intended for UNIX-like operating systems.\033[0m""")


__author__ = "Drunkard Zhang"
__email__ = "gongfan193@gmail.com"
__version__ = "0.1"
__productname__ = "lazycat"
__description__ = "A pseudo shell with restricted capability for AAA purpose."


PROMPT = color.GREEN_BOLD + "jumper" + color.OFF + "> "

flush_interval = 10
global_pexpect_instance = None  # Used by signal handler


class MLCompleter(object):  # Custom completer
    """Means Multi-Level Completer, used to complete multi level commands
    Usage:
    completer = MLCompleter(["hello", "hi", "how are you", "goodbye", "great"])
    readline.set_completer(completer.complete)
    readline.parse_and_bind('tab: complete')

    input = input("Input: ")
    print "You entered", input
    """
    def __init__(self, options):
        self.options = sorted(options)

    def complete(self, text, state):
        if state == 0:  # on first trigger, build possible matches
            if text:    # cache matches (entries that start with entered text)
                self.matches = [s for s in self.options
                                if s and s.startswith(text)]
                # print("\ntext value: %s" % self.matches)  # debug
            else:  # no text entered, all matches possible
                self.matches = self.options[:]

        # return match indexed by state
        try:
            # return matched word, plus a space
            return self.matches[state] + ' '
        except IndexError:
            return None


class bgrun(threading.Thread):
    """Run something in background"""
    def __init__(self, flushlog):
        threading.Thread.__init__(self)
        self.runnable = flushlog
        self.daemon = True

    def run(self):
        self.runnable()


def flushlog():
    from socket import gethostname
    title = os.getlogin() + "@" + gethostname()
    while True:
        ts = '\n### %4d-%02d-%02dT%02d:%02d:%02d ' % time.localtime()[:-3]
        try:
            # Add timestamp
            fout.write(ts + title + "\n")
            fout.flush()  # flush back to file
            time.sleep(flush_interval)
        except ValueError:
            break
            # for debug
            print("flushlog(): I/O operation failed, maybe lost some log")
            time.sleep(10)  # To avoid dead lock
            return 127


def run_with_log(command):
    # Check if command exists
    if not cmd_exists(command.split()[0]):
        say.nocmd(command.split()[0])
        return False
    # Begin log with timestamp
    from cli.oplog import get_log_file
    global fout
    log_filename = get_log_file(command.strip().replace(' ', '-'))
    fout = open(log_filename, "ab")
    bgrun(flushlog).start()
    # Start pexpect session
    try:
        thissession = pexpect.spawn('bash', ['-c', command])
    except pexpect.ExceptionPexpect as e:
        raise e
    except SystemExit as e:
        print(e)
        return False
    except (KeyboardInterrupt, pexpect.EOF, pexpect.TIMEOUT):
        return False
    except BaseException as e:
        print(e)
        return False

    thissession.logfile = fout
    global global_pexpect_instance
    global_pexpect_instance = thissession
    signal.signal(signal.SIGWINCH, sigwinch_passthrough)

    fout.write("### First command: %s\n" % command)
    # TODO: rewrite, control on every cmd
    thissession.interact()
    fout.close()
    return True


def run_without_log(command):
    command = command.strip()
    command_name = command.split()[0]
    command_args = command.split()[1:]
    # First, try to lookup command map
    FOUND_IN_MAP = False
    for entry in cli.l1_map:
        if command_name == entry[0]:
            command = entry[1] + ' '.join(command_args)
            FOUND_IN_MAP = True
            break
        else:
            continue

    # Second, test if it's in PATH, return if not
    if cmd_exists(command_name) or FOUND_IN_MAP:
        pass
    else:
        print("This function is not usable, please recheck PATH or l1_map: %s"
              % command)
        return 1

    # Run the command, this should be OK
    try:
        print("Raw command executed: %s" % command)
        os.system(command)
    except BaseException as e:
        print(e)
        print("\r")
        return 0


def do_clear():
    os.system("clear")


def do_log(command):
    from cli import oplog
    sub = command.split()
    sub.reverse()
    # If no sub-command, print usable sub-command and return
    if len(sub) == 1:
        say.available_cmds(cli.log_l2)
        return
    else:
        l2cmd = sub.pop()   # pop out 'show'

    l2cmd = sub.pop()
    if l2cmd in cli.log_list_comp:
        oplog.do_list()
    elif l2cmd in cli.log_view_comp:
        try:
            f = sub.pop()
        except Exception:
            print("Need file name listed by \"log list\".")
            return
        oplog.do_view(f)
    else:
        say.available_cmds(cli.log_l2)


def do_help():
    u"""终端快捷键：
    ?               显示可用命令

    Ctrl-A          光标移到行首
    Ctrl-E          光标移到行尾
    Ctrl-B | Left   左移光标
    Ctrl-F | Right  右移光标
    Ctrl-P | Up     前一个命令
    Ctrl-N | Down   后一个命令

    Backspace       删除左边一个字符
    Ctrl-D          删除右边一个字符

    Ctrl-U          剪切光标到行首之间的字符
    Ctrl-K          剪切光标到行尾之间的字符
    Ctrl-W          剪切光标左边一个词
    Alt-D           剪切光标右边一个词

    Ctrl-R          向前搜索历史命令
    Return          把命令发给终端
    """
    try:
        print(do_help.__doc__.replace('\n    ', '\n'))
    except Exception as e:
        print(e)
    return 0


def do_quit():
    print ("%sSee you next time %s;)%s" %
           (color.CYAN_BOLD, color.BLINK, color.OFF))
    sys.exit()


def sigwinch_passthrough(sig, data):
    # Check for buggy platforms (see pexpect.setwinsize()).
    if 'TIOCGWINSZ' in dir(termios):
        TIOCGWINSZ = termios.TIOCGWINSZ
    else:
        TIOCGWINSZ = 1074295912     # assume
    s = struct.pack("HHHH", 0, 0, 0, 0)
    a = struct.unpack('HHHH', fcntl.ioctl(sys.stdout.fileno(), TIOCGWINSZ, s))
    global global_pexpect_instance
    # print ("Windows size: %s x %s" % (a[0], a[1])) # debug
    global_pexpect_instance.setwinsize(a[0], a[1])


def ttywrapper():
    try:
        readline.parse_and_bind('tab: complete')
        readline.set_completer_delims(' ')
    except Exception as e:
        print(e)

    while True:
        readline.set_completer(MLCompleter(cli.all_cmd).complete)
        global command
        # Get input, and deal with exceptions
        try:
            command = input(PROMPT)
        except KeyboardInterrupt:
            """Ctrl-C"""
            print ("^C")
            continue
        except EOFError:
            """Ctrl-D"""
            # print ("^D")
            # continue
            print("quit")
            do_quit()

        # Determine if command is empty
        if not command.strip():
            continue

        # Classify the commands, and run them by different wrapper
        command = command.strip()
        try:
            l1cmd = command.split()[0]
            if l1cmd in cli.clear_comp:
                do_clear()
            elif l1cmd in cli.help_comp:
                do_help()
            elif l1cmd in cli.log_comp:
                do_log(command)
            elif l1cmd in cli.quit_comp:
                do_quit()
            elif l1cmd in cli.show_comp:
                from cli.show import do_show
                do_show(command)
            elif len(command.split()) >= 1 and l1cmd in cli.log_cmd:
                if len(command.split()) == 1:
                    os.system(command + ' -h')
                    continue
                run_with_log(command)
            elif len(command.split()) >= 1 and l1cmd in cli.nolog_cmd:
                try:
                    run_without_log(command)
                except Exception as e:
                    print(e)
            else:
                if l1cmd in cli.all_cmd:
                    say.not_implemented()

                print("%sBad command:%s %s\n" %
                      (color.RED_BG, color.OFF, command))
                say.available_cmds(sorted(cli.all_cmd),
                                   msg="All available commands:")
        except (KeyboardInterrupt, EOFError):
            continue


if __name__ == "__main__":
    history.load()
    history.save()
    try:
        ttywrapper()
    except (Exception, SystemExit) as e:
        # After ttywrapper() exit, we get SystemExit exception here
        sys.exit(e)
