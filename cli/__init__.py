# -*- coding: utf-8 -*-
import logging
import os
import readline
import socket
import sys
import threading
import time

import signal
import fcntl
import termios
import struct

try:
    import pexpect
    from lib import cmd_exists, color, say
except ImportError as e:
    raise e


PROMPT = color.GREEN_BOLD + "jumper" + color.OFF + "> "
# These commands' output to ncurses like window, which is hard to strip
OMIT_OUTPUT = ['atop', 'htop', 'iotop', 'iftop', 'dnstop']


# Command enumerate
nolog_cmd = {
    # 'CMD name': {'cmd': 'Real Linux CMD', 'desc': 'Description'},
    'clear': {'cmd': 'clear ',
              'desc': 'Clear the terminal screen'},
    'reset': {'cmd': 'reset',
              'desc': 'Reset current terminal'},
    'config': {'desc': 'Config current work enviroment'},
    'log': {'desc': 'Operation log management'},
    'quit': {'desc': 'Quit from current session'},
    'show': {'desc': 'Show misc informations'},
    'password': {'cmd': 'passwd',
                 'desc': 'Change password'},
    # ping like commands
    'httping': {'cmd': 'httping ',
                'desc': 'HTTP protocol ping-like program'},
    'ping': {'cmd': 'ping ',
             'desc': 'Send ICMP ECHO_REQUEST to network hosts'},
    'ping6': {'cmd': 'ping6 ',
              'desc': 'Send ICMP ECHO_REQUEST to network hosts, IPv6 version'},
    # hping need root privilege
    # 'tcp-ping': {'cmd': 'hping -p 80 --syn ',
    #              'desc': 'Ping using TCP protocol, default 80 port'},
    # 'udp-ping': {'cmd': 'hping --udp -p 53 ',
    #              'desc': 'Ping using UDP protocol, default 53 port'},
    'tcp-ping': {'cmd': 'nping --tcp-connect -p 80 ',
                 'desc': 'Ping using TCP protocol, using port 80'},
    'udp-ping': {'cmd': 'nping --udp -p 53 ',
                 'desc': 'Ping using UDP protocol, using port 53'},
    # traceroute commands
    'traceroute': {'cmd': 'traceroute',
                   'desc': 'Trace route in ICMP protocol'},
    'traceroute6': {'cmd': 'traceroute6',
                    'desc': 'Trace route in ICMP protocol, IPv6 version'},
    'tcp-traceroute': {'cmd': '/usr/sbin/tcptraceroute ',
                       'desc': 'Trace route in TCP protocol, using port 80'},
    'udp-traceroute': {'cmd': 'traceroute -U -p 53 ',
                       'desc': 'Trace route in UDP protocol, using port 53'},
}

log_cmd = {
    'telnet': {'cmd': 'telnet', 'desc': 'Establish a Telnet connection'},
    'ssh': {'cmd': 'ssh', 'desc': 'Establish a ssh client connection'},
}

all_cmd = dict(nolog_cmd, **log_cmd)


# Level 2 commands definations
log_l2 = {
    'list': {'desc': 'List all operation log files'},
    'view': {'desc': 'View operation log file'},
}
show_l2 = {
    'history': {'desc': 'Show command history'},
    'hostname': {'cmd': 'hostname',
                 'desc': 'Show hostname of this host'},
    'ip': {'cmd': 'ip addr',
           'desc': 'Show IP address on this host'},
    'route': {'cmd': 'ip route | grep -e default -e kernel',
              'desc': 'Show routes on this host'},
    'shortcuts': {'desc': 'Show keyboard shortcuts of this system'},
    'user': {'cmd': 'w -f',
             'desc': 'Show active users on this host'},
    'time': {'cmd': 'cal -3; date',
             'desc': 'Show local date and time'},
}


def bh():
    print('%sbeen here%s' % (color.CYAN_BOLD, color.OFF))


class bgrun(threading.Thread):
    """Run something in background"""
    def __init__(self, flushlog):
        threading.Thread.__init__(self)
        self.runnable = flushlog
        self.daemon = True

    def run(self):
        self.runnable()


class MLCompleter(object):  # Custom completer
    """Means Multi-Level Completer, used to complete multi level rawcmds
    Usage:
    completer = MLCompleter(["hello", "hi", "how are you", "goodbye", "great"])
    readline.set_completer(completer.complete)
    readline.parse_and_bind('tab: complete')

    input = input("Input: ")
    print "You entered", input
    """
    # TODO: finish multiple level complete
    def __init__(self):
        """This variable should not be initialized here, get it on demand and
        in realtime.
            origcmd = readline.get_line_buffer()
        """

    def complete(self, text, state):
        options = sorted(self.possible_options())
        if state == 0:  # on first trigger, build possible matches
            if text:    # cache matches (entries that start with entered text)
                self.matches = [s
                                for s in options
                                if s and s.startswith(text)]
            else:  # no text entered, all matches possible
                self.matches = options[:]
        # return match indexed by state
        try:
            # return matched word, plus a space
            return self.matches[state] + ' '
        except IndexError:
            return None

    def possible_options(self):
        """Parse user requested command, determine what next level command
        dict.keys() is and return to completer.
        """
        origcmd = readline.get_line_buffer()
        cmdlist = origcmd.split()
        # Return possible command list from all_cmd by default, user didn't
        # input anything yet.
        if len(cmdlist) == 0:
            return all_cmd.keys()
        elif len(cmdlist) == 1 and not origcmd.endswith(' '):
            return all_cmd.keys()
        return self.level2_options()

    def level2_options(self):
        """Return next level list, user already input some command"""
        origcmd = readline.get_line_buffer()
        cmdlist = origcmd.split()
        l1cmd = complete_cmd(cmdlist[0], all_cmd)
        # Ends with space identifies user has confirmed previous command,
        # do next level
        if origcmd.endswith(' '):
            nextlevel = len(cmdlist) + 1
        else:
            nextlevel = len(cmdlist)
        nextlevel_dict_name = l1cmd + '_l' + str(nextlevel)
        logging.debug('expect next level dict name: ' + nextlevel_dict_name)
        try:
            import cli
            d = getattr(cli, nextlevel_dict_name)
            return d.keys()
        except AttributeError:
            logging.debug('no next level command to complete for: ' + l1cmd)
            # FIXME: rewrite this with general completer
            # Special process on "log view ..."
            if complete_cmd(cmdlist[1], log_l2) == 'view':
                from cli.log import complete
                files = complete().view()
                return sorted(files)
            else:
                return []


def do_config(rawcmd):
    say.not_implemented()


def do_log(rawcmd):
    from cli.log import do_log
    do_log(rawcmd)


def do_quit(rawcmd):
    print("%sSee you next time %s;)%s" %
          (color.CYAN_BOLD, color.BLINK, color.OFF))
    sys.exit()


def do_show(rawcmd):
    from cli.show import do_show
    do_show(rawcmd)


def complete_cmd(cmd, predefined):
    """Finish user requested command, it maybe part command, so complete
    it first.

        cmd = complete_cmd(str_partial_cmd, dict_defined_cmd)

    Returns None if none matched or multiple matched, returns str if only
    one successfully matched.
    """
    matched = []
    if predefined.get(cmd):
        matched.append(cmd)
    else:
        for c in predefined.keys():
            if c.startswith(cmd):
                matched.append(c)
    if len(matched) == 0:
        say.no_cmd(cmd)
        say.available_cmds(predefined)
        return None
    elif len(matched) == 1:
        return matched[0]
    else:
        say.available_cmds(matched)
        return None


class route(str):
    """Route user requested command to proper processor or model."""
    def __init__(self, rawcmd):
        rawcmd = rawcmd.strip()
        cmd_list = rawcmd.split()
        l1cmd = complete_cmd(cmd_list[0], all_cmd)
        if l1cmd is None:
            return
        # Replace possible partial command with completed command
        cmd_list[0] = l1cmd
        rawcmd = ' '.join(cmd_list)
        logging.debug('completed full command is: ' + rawcmd)
        # Define internal variables
        self.rawcmd = rawcmd
        self.l1cmd = rawcmd.split()[0]
        # Routing to a hook that won't log screen
        if all_cmd.get(l1cmd).get('cmd') is None:
            logging.debug('routed to to_unmapped_cmd: ' + l1cmd)
            self.to_unmapped_cmd(rawcmd)
        else:
            logging.debug('routed to to_mapped_cmd: ' + l1cmd)
            self.to_mapped_cmd(rawcmd)

    def to_unmapped_cmd(self, rawcmd):
        # Try to match functions named starts with "do_"
        import cli
        try:
            func = getattr(cli, 'do_' + self.l1cmd)
        except AttributeError:
            logging.debug('no such function: do_' + self.l1cmd)
            func = None
        if func is None:
            say.no_cmd(rawcmd)
        else:
            logging.debug('routed to builtin function: do_' + self.l1cmd)
            return func(rawcmd)

    def to_mapped_cmd(self, rawcmd):
        if rawcmd.split()[0] in log_cmd.keys():
            logging.debug('routed to run(rawcmd).with_log()')
            run(rawcmd).with_log()
        else:
            logging.debug('routed to run(rawcmd).without_log()')
            run(rawcmd).without_log()


class run(str):
    def __init__(self, rawcmd):
        self.flush_interval = 10
        self.global_pexpect_instance = None  # Used by signal handler
        self.rawcmd = rawcmd
        self.rawcmd_list = rawcmd.split()

    def flushlog(self):
        fout = self.fout
        title = os.getlogin() + "@" + socket.gethostname()
        while True:
            ts = '\n### %4d-%02d-%02dT%02d:%02d:%02d' % time.localtime()[:-3]
            line = ' '.join([ts, title, '\n'])
            line = bytes(line, 'utf-8')
            if not fout.closed:
                # Add timestamp
                fout.write(line)
                fout.flush()  # flush back to file
            else:
                return
            time.sleep(self.flush_interval)  # To avoid dead lock

    def sigwinch_passthrough(self, sig, data):
        # Check for buggy platforms (see pexpect.setwinsize()).
        if 'TIOCGWINSZ' in dir(termios):
            TIOCGWINSZ = termios.TIOCGWINSZ
        else:
            TIOCGWINSZ = 1074295912     # assume
        s = struct.pack("HHHH", 0, 0, 0, 0)
        a = struct.unpack('HHHH',
                          fcntl.ioctl(sys.stdout.fileno(), TIOCGWINSZ, s))
        # print ("Windows size: %s x %s" % (a[0], a[1])) # debug
        self.global_pexpect_instance.setwinsize(a[0], a[1])

    def with_log(self):
        from cli.log import get_log_file
        log_filename = get_log_file(self.rawcmd.replace(' ', '-'))
        fout = open(log_filename, "wb")
        self.fout = fout
        # Check if command exists
        rawcmd = self.rawcmd
        if not cmd_exists(self.rawcmd_list[0]):
            say.no_sys_cmd(self.rawcmd_list[0])
            return False
        # Start pexpect session
        try:
            thissession = pexpect.spawn('bash', ['-c', rawcmd])
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
        self.global_pexpect_instance = thissession
        signal.signal(signal.SIGWINCH, self.sigwinch_passthrough)
        fout.write(bytes('### First command: %s\n' % rawcmd, 'utf-8'))
        # Begin log with timestamp
        bgrun(self.flushlog).start()
        # TODO: rewrite, control on every cmd
        """
        while True:
            output = os.popen(line).read()
            print(output)
        """
        thissession.interact()
        fout.close()
        return

    def without_log(self):
        """Run commands without log the output.
        self.rawcmd must be processed by complete_cmd() first, or recheck
        may fails.
        """
        rawcmd_list = self.rawcmd_list
        req_cmd = rawcmd_list[0]
        # First lookup command map, get real command in system
        if req_cmd not in all_cmd.keys():
            say.no_cmd(req_cmd)
            return
        real_cmd = all_cmd.get(req_cmd).get('cmd')
        if real_cmd is None:
            say.internal_error()
            return
        logging.debug('run.without_log, got real_cmd = "%s"' % real_cmd)
        # Check if got real command exists
        scmd = real_cmd.split()[0]
        if not cmd_exists(scmd):
            say.no_sys_cmd(scmd)
            return
        # Restruct new command, replace requested command with system command
        rawcmd_list[0] = real_cmd
        newcmd = ' '.join(rawcmd_list)
        # Run the command, this should be OK
        try:
            print("Raw command executed: %s" % newcmd)
            os.system(newcmd)
        except BaseException as e:
            print(e)
            print("\r")
            return
