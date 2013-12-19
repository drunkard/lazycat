#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""This program is a pseudo-shell and gives the user interactive control.
The entire ssh/telnet session is logged to a file, others won't be logged.
"""

import glob
import os
import readline
import string
import sys
import threading
import time
from socket import gethostname

import signal
import fcntl
import termios
import struct

try:
    # import ANSI
    import pexpect
    # import rlcompleter2
    # import IPython.core.completer as completer
    from lib import color
except ImportError, e:
    raise ImportError(str(e) + """\033[05;37;41m

A critical module was not found. Probably this operating system does not
support it. Pexpect is intended for UNIX-like operating systems.\033[0m""")

__author__ = "Drunkard Zhang"
__email__ = "gongfan193@gmail.com"
__version__ = "0.1"
__productname__ = "lazycat"
__description__ = "A pseudo shell with restricted capability for AAA purpose."

PATH = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
historyLength = 1000
historyPath = os.path.expanduser('~/.' + __productname__ + '_history')
PROMPT = color.GREEN_BOLD + "jumper" + color.OFF + "> "
SHOW_WARN = 0

# Command enumerate
nolog_cmd = [
    # {'KEY': ('showed cmd', 'real cmd, maybe system cmd', 'Description')},
    # Single module functions
    'auto',
    'clear',
    'config',
    'dns',
    'help',
    'log',
    'password',
    'quit',
    'show',
    # These tools mapped to system commands
    'httping',
    'ping',
    'ping6',
    'tcp-ping',
    'udp-ping',
    'traceroute',
    'traceroute6',
    'tcp-traceroute',
    'udp-traceroute']
log_cmd = [
    'ssh',
    'telnet']
all_cmd = log_cmd + nolog_cmd

# Level 2 commands definations
auto_l2 = [
    'list',
    'add',
    'del',
    'config',
    'enable-password',
    'password']
config_l2 = [
    'user',
    'password',
    'permission',
    'tui']
dns_l2 = [
    'arpa',
    'resolve',
    'trace']
log_l2 = [
    'list',
    'search',
    'view',
    'del']
show_l2 = [
    'all-jumper',
    'history',
    'my-permission',
    'user',
    'this-server',
    'time']

# Level 3 commands definations
log_search_l3 = [
    'by-date',
    'by-time',
    'by-device-ip',
    'by-device-name']

# These commands' output to ncurses like window, which is hard to strip
OMIT_OUTPUT = ['atop', 'htop', 'iotop', 'iftop', 'dnstop']

# Partial command definations
auto_comp = ['auto']
clear_comp = ['cl', 'cle', 'clear']
dns_comp = ['d', 'dn', 'dns']
help_comp = ['he', 'hel', 'help']
log_comp = ['l', 'lo', 'log']
log_del_comp = ['d', 'de', 'del']
log_list_comp = ['l', 'li', 'lis', 'list']
log_view_comp = ['v', 'vi', 'vie', 'view']
quit_comp = ['q', 'qu', 'qui', 'quit']
show_comp = ['sh', 'sho', 'show']
show_history_comp = ['h', 'history']
show_my_permission_comp = ['m', 'my', 'my-' 'my-p', 'my-permission']
show_user_comp = ['u', 'us', 'use', 'user']
show_this_server_comp = ['th', 'this-server']
show_time_comp = ['ti', 'tim', 'time']

map_resolver = {'name': 0, 'cmd': 1, 'desc': 2}
l1_map = [
    # ('CMD name', 'Real Linux CMD', 'Description'),
    ('password', 'passwd', 'Change password'),
    ('time', 'cal -3; date', 'Show local date and time'),
    # hping need root privilege
    # ('tcp-ping', 'hping -p 80 --syn ', 'Ping using TCP protocol, default 80 port'),
    # ('udp-ping', 'hping --udp -p 53 ', 'Ping using UDP protocol, default 53 port')
    ('tcp-ping', 'nping --tcp-connect -p 80 ', 'Ping using TCP protocol, using port 80'),
    ('udp-ping', 'nping --udp -p 53 ', 'Ping using UDP protocol, using port 53'),
    ('tcp-traceroute', 'tcptraceroute ', 'traceroute using TCP protocol, using port 80'),
    # ('tcp-traceroute', 'traceroute -M tcp -p 80 ', 'traceroute using TCP protocol, using port 80'),
    ('udp-traceroute', 'traceroute -U -p 53 ', 'traceroute using UDP protocol, using port 53')]
dns_srcip_map = [
    ('1.1.1.1', '42.196.0.0/16, 49.221.128.0/17, 101.244.0.0/15, 118.205.1.0/17'),
    ('default', 'default')]

os.putenv('PATH', PATH)
global path
path = os.environ.get('HOME') + '/%4d%02d%02d' % time.localtime()[:-6]
if not os.path.isdir(path):
    os.makedirs(path)
flush_interval = 10
title = os.getlogin() + "@" + gethostname()
del gethostname
global_pexpect_instance = None  # Used by signal handler


def exit_with_usage():
    print globals()['__doc__']
    os._exit(1)


class MLCompleter(object):  # Custom completer
    """Means Multi-Level Completer, used to complete multi level commands
    Usage:
    completer = MLCompleter(["hello", "hi", "how are you", "goodbye", "great"])
    readline.set_completer(completer.complete)
    readline.parse_and_bind('tab: complete')

    input = raw_input("Input: ")
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
    while True:
        try:
            # Add timestamp
            fout.write('\n### %4d-%02d-%02dT%02d:%02d:%02d ' % time.localtime()[:-3] + title + "\n")
            fout.flush()  # flush back to file
            time.sleep(flush_interval)
        except ValueError:
            break
            # for debug
            print("flushlog(): I/O operation failed, maybe lost some log")
            time.sleep(10)  # To avoid dead lock
            return 127


def human_readable_size(nbytes):
    try:
        import math
    except ImportError:
        print("Python module import error in human_readable_size()")

    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

    if nbytes == 0:
        return '0 B'

    rank = int((math.log10(nbytes)) / 3)
    rank = min(rank, len(suffixes) - 1)
    human = nbytes / (1024.0 ** rank)
    f = ('%.1f' % human).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[rank])


def say_cmd(cmdlist, msg="All available commands:"):
        print (msg)
        if len(cmdlist) > 0:
            for c in sorted(cmdlist):
                print ("  " + str(c))


def say_not_implemented():
    print("%sThis is planned, but not implemented yet.%s\n" %
          (color.CYAN_BOLD, color.OFF))


def save_history(historyPath=historyPath):
    f = open(historyPath, 'w')
    try:
        readline.set_history_length(1000)
        readline.write_history_file(historyPath)
    except Exception, e:
        print(str(e))
    f.close()


def str_to_class(s):
    import types
    if s in globals() and isinstance(globals()[s], types.ClassType):
        return globals()[s]
    return None


def which(command):
    from distutils.spawn import find_executable
    if find_executable(command, path=PATH) is None:
        return False
    else:
        return True


def run_with_log():
    global fout
    log_filename = path + '/%4d%02d%02d-%02d%02d%02d-' % \
            time.localtime()[:-3] + os.getlogin() + '-' + \
            command.strip().replace(' ', '-')
    fout = file(log_filename, "ab")

    # Begin log with timestamp
    # fout.write ('%4d-%02d-%02dT%02d:%02d:%02d ' % time.localtime()[:-3] + title + "\n")
    bgrun(flushlog).start()

    try:
        if which(command.split()[0]):
            pass
        else:
            print("The command %s%s%s is not usable, please notify your administrator." % (color.RED_BLINK, command.split()[0], color.OFF))
            return 1

        thissession = pexpect.spawn('bash', ['-c', command])
    except pexpect.ExceptionPexpect, e:
        raise e
        return 1
    except SystemExit, e:
        print(str(e))
        return 1
    except (KeyboardInterrupt, EOF, TIMEOUT):
    # except (BaseException, KeyboardInterrupt, EOFError, SystemExit):
        # thissession.sendcontrol('c')
        return 1
    except BaseException, e:
        print(str(e))
        return 1

    thissession.logfile = fout
    global global_pexpect_instance
    global_pexpect_instance = thissession
    signal.signal(signal.SIGWINCH, sigwinch_passthrough)

    fout.write("### First command: %s\n" % command)
    try:
        if SHOW_WARN == 1:
            print ("%sOperation logging started, have fun :)%s" %
                   (color.RED, color.OFF))
    except NameError:
        pass
    try:
        # TODO: rewrite, control on every cmd
        # thissession.interact(chr(29))
        thissession.interact()
    except OSError:
        pass
    except BaseException, e:
        print("\r" + str(e))
        return 1

    try:
        if SHOW_WARN == 1:
            print ("%sOperation logging stopped%s" % (color.RED, color.OFF))
    except NameError:
        pass
    fout.close()
    return 0


def run_without_log(command):
    command_name = command.strip().split()[0]
    command_args = command.strip().split()[1:]

    # First, try to lookup command map
    FOUND_IN_MAP = False
    for entry in l1_map:
        if command_name == entry[0]:
            # debug
            # print type(entry[1])
            # print type(command_args)
            command = entry[1] + ' '.join(command_args)
            FOUND_IN_MAP = True
            break
        else:
            continue

    # Second, test if it's in PATH, return if not
    if which(command_name):
        pass    # goto try: part
    elif FOUND_IN_MAP is True:
        pass
    else:
        print("This function is not usable, please check it in PATH or l1_map: %s" % command)
        return 1

    # Run the command, this should be OK
    try:
        print("Raw command executed: %s" % command)
        os.system(command)
    except BaseException, e:
        print(str(e))
        print("\r")
        return 0


def do_auto():
    say_not_implemented()
    print("""This function is intended to automatically config device with
          predefined template, such as logging, password, etc.
""")
    return True


def do_clear():
    os.system("clear")


def do_dns():
    print("Not implemented yet")
    return True
    sub = command.split()
    sub.reverse()
    # If no sub-command, print usable sub-command and return
    if len(sub) == 1:
        say_cmd(dns_l2, msg="All available sub-commands:")
        return 1
    else:
        l2cmd = sub.pop()   # pop out 'show'
    l2cmd = sub.pop()


def do_log():
    sub = command.split()
    sub.reverse()
    # If no sub-command, print usable sub-command and return
    if len(sub) == 1:
        say_cmd(log_l2, msg="All available sub-commands:")
        return 1
    else:
        l2cmd = sub.pop()   # pop out 'show'

    l2cmd = sub.pop()
    if l2cmd in log_del_comp:
        """eg: log del 20130705-110150-mj-telnet-10.0.0.1
        """
        print ('Permission denied')
    elif l2cmd in log_list_comp:
        """eg: log list
        """

        try:
            files = sorted(glob.glob(path + "/*"))
        except Exception, e:
            print str(e)
            print("Error getting file list !!!")
            return 1

        if len(files) == 0:
            print("You don't have any log file.")
        else:
            print("Log files in %s:" % str(path))
            print("%s Size  -  Date  - Time - User - CMD - Host%s" %
                  (color.WHITE, color.OFF))
            for f in files:
                try:
                    print("%s\t%s" % (human_readable_size(os.path.getsize(f)),
                                      str(os.path.basename(f))))
                except Exception, e:
                    print(str(e))

    elif l2cmd in log_view_comp:
        """eg: log view 20130705-110150-mj-telnet-10.0.0.1
        """
        try:
            f = sub.pop()
        except Exception:
            print("Need file name listed by \"log list\".")
            return 1

        f = path + '/' + f
        if os.path.isfile(f):
            os.system("less -r %s" % f)  # buggy
            return True
            # TODO: need rewrite
            with open(f) as fc:
                for line in fc:
                    print ("%s" % str(line)),
        else:
            print("log view %s: No such file or directory" % str(f))
            return 1
    else:
        say_cmd(log_l2, msg="All available sub-commands:")


def do_help():
    """终端快捷键：
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
    # print (do_help.__doc__)
    try:
        print string.replace(do_help.__doc__, '\n    ', '\n')
    except Exception, e:
        print(str(e))
    return 0


def do_quit():
    print ("%sSee you next time %s;)%s" %
           (color.CYAN_BOLD, color.BLINK, color.OFF))
    os.exit()


def do_shell():
    print("Permission denied")
    return True


def do_show():
    sub = command.split()
    sub.reverse()
    # If no sub-command, print usable sub-command and return
    if len(sub) == 1:
        say_cmd(show_l2, msg="All available sub-commands:")
        return 1
    else:
        l2cmd = sub.pop()   # pop out 'show'

    l2cmd = sub.pop()
    if l2cmd in show_history_comp:
        """show history
        """
        try:
            cnt = 0
            for h in range(readline.get_current_history_length()):
                cnt += 1
                print ("%s\t\b\b\b%s" % (cnt, readline.get_history_item(h)))
        except Exception, e:
            print(str(e))
    elif l2cmd in show_my_permission_comp:
        """show my-permission
        """
        say_not_implemented()
    elif l2cmd in show_user_comp:
        """show user
        """
        os.system('w -f')
    elif l2cmd in show_this_server_comp:
        """show this-server
        """
        print("IP address configs on this host:")
        os.system('ip addr')

        print("\nRoutes on this host:")
        os.system('ip route | grep -e default -e kernel ')
    elif l2cmd in show_time_comp:
        """show time
        """
        os.system('cal -3; echo; date')
    elif l2cmd is None:
        say_cmd(show_l2, msg="All available sub-commands:")
    else:
        say_cmd(show_l2, msg="All available sub-commands:")


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
    # t = ANSI.term()

    try:
        # l1_completer = MLCompleter(all_cmd)
        # readline.set_completer(l1_completer.complete)
        readline.parse_and_bind('tab: complete')
        readline.set_completer_delims(' ')
    except Exception, e:
        print(str(e))

    while 1:
        readline.set_completer(MLCompleter(all_cmd).complete)

        global command
        # Get input, and deal with exceptions
        try:
            command = raw_input(PROMPT)
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
            if l1cmd in auto_comp:
                do_auto()
            elif l1cmd in clear_comp:
                do_clear()
            elif l1cmd in help_comp:
                do_help()
            elif l1cmd in log_comp:
                do_log()
            elif l1cmd in quit_comp:
                do_quit()
            elif l1cmd in show_comp:
                do_show()
            elif len(command.split()) >= 1 and l1cmd in log_cmd:
                if len(command.split()) == 1:
                    os.system(command + ' -h')
                    continue
                run_with_log()
            elif len(command.split()) >= 1 and l1cmd in nolog_cmd:
                try:
                    run_without_log(command)
                except Exception, e:
                    print(str(e))
            else:
                if l1cmd in all_cmd:
                    say_not_implemented()

                print("%sBad command:%s %s\n" %
                      (color.RED_BG, color.OFF, command))
                say_cmd(sorted(all_cmd))
        except (KeyboardInterrupt, EOFError):
            continue


# History, automatically load on login, and save on exit.
try:
    readline.read_history_file(historyPath)
except IOError:
    pass

try:
    import atexit
    readline.set_history_length(historyLength)
    atexit.register(readline.write_history_file, historyPath)
except Exception:
    print("Error on register history file, won't save command history.")

if __name__ == "__main__":
    try:
        ttywrapper()
    except (Exception, SystemExit):
        # After ttywrapper() exit, we get SystemExit exception here
        sys.exit()
