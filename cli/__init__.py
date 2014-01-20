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
    from lib import cmd_exists, color, maxlen, say
except ImportError as e:
    raise e


PROMPT = color.GREEN_BOLD + "jumper" + color.OFF + "> "
# These commands' output to ncurses like window, which is hard to strip
OMIT_OUTPUT = ['atop', 'htop', 'iotop', 'iftop', 'dnstop']


"""Command Defination

Should be write as inverted tree structure, higher level dict includes
lower level dict with 'nextlevel' key.
"""
# Level 3 commands definations
config_debug_l3 = {
    'on':
    {'desc': 'Turn on debugging'},
    'off':
    {'desc': 'Turn off debugging'},
}
dns_list_l3 = {
    '<name>':
    {'desc': 'List all DNS servers starts with <name>'},
    'all':
    {'desc': 'List all DNS servers we know'},
    'cache':
    {'desc': 'List all cache DNS servers we have'},
    'cache-cluster':
    {'desc': 'List all cache cluster DNS servers we have'},
    'iterator':
    {'desc': 'List all iteration DNS servers we have'},
    'public':
    {'desc': 'List all public DNS servers we use for trouble-shooting'},
    'view':
    {'desc': 'Views installed on DNS server'},
}
dns_arpa_l3 = {
    '<ip>':
    {'desc': 'Resolve from non-cache servers'},
    '<ip> @<server name>':
    {'desc': 'Resolve from specific server'},
    '<ip> @all':
    {'desc': 'Resolve from all servers'},
    '<ip> @public':
    {'desc': 'Resolve from famous public DNS'},
}
dns_resolve_l3 = {
    '<domain name>':
    {'desc': 'Resolve from non-cache servers'},
    '<domain name> @<server name>':
    {'desc': 'Resolve from specific server'},
    '<domain name> @all':
    {'desc': 'Resolve from all servers'},
    '<domain name> @public':
    {'desc': 'Resolve from famous public DNS'},
}

# Level 2 commands definations
config_l2 = {
    'debug':
    {'desc': 'Debug configuration about me',
     'nextlevel': config_debug_l3},
}
dns_l2 = {
    'arpa':
    {'desc': 'Resolve IP address to name, so called ARPA',
     'nextlevel': dns_arpa_l3},
    'flush':
    {'desc': 'Flush one name out of cache on our iteration DNS servers'},
    # 'flush-tree':
    # {'desc':
    #  'Flush cache of all names under given name on DNS server, DANGEROUS'},
    'list':
    {'desc': 'List DNS server related information',
     'nextlevel': dns_list_l3},
    'one-key-diag':
    {'desc': 'Super easy trouble locator'},
    'resolve':
    {'desc': 'Resolve name to IP address, more options on sub-commands',
     'nextlevel': dns_resolve_l3},
    'trace':
    {'desc': 'Manually trace resolve progress step by step'},
}
log_l2 = {
    'list':
    {'desc': 'List all operation log files'},
    'view':
    {'desc': 'View operation log file'},
}
show_l2 = {
    'history':
    {'desc': 'Show command history'},
    'hostname':
    {'cmd': 'hostname',
     'desc': 'Show hostname of this host'},
    'ip':
    {'cmd': 'ip addr',
     'desc': 'Show IP address on this host'},
    'route':
    {'cmd': 'ip route | grep -e default -e kernel',
     'desc': 'Show routes on this host'},
    'shortcuts':
    {'desc': 'Show keyboard shortcuts of this system'},
    'user':
    {'cmd': 'w -f',
     'desc': 'Show active users on this host'},
    'time':
    {'cmd': 'cal -3; date',
     'desc': 'Show local date and time'},
}


# Level 1 commands definations
nolog_cmd = {
    # 'CMD name': {'cmd': 'Real Linux CMD', 'desc': 'Description'},
    '?':
    {'desc': 'Print this menu'},
    'clear':
    {'cmd': 'clear ',
     'desc': 'Clear the terminal screen'},
    'config':
    {'desc': 'Config current work enviroment',
     'nextlevel': config_l2},
    'dns':
    {'desc': 'DNS system trouble diagnosing',
     'nextlevel': dns_l2},
    'log':
    {'desc': 'Operation log management',
     'nextlevel': log_l2},
    'password':
    {'cmd': 'passwd',
     'desc': 'Change password'},
    'quit':
    {'desc': 'Quit from current session'},
    'reset':
    {'cmd': 'reset',
     'desc': 'Reset current terminal'},
    'show':
    {'desc': 'Show misc informations',
     'nextlevel': show_l2},
    'tree':
    {'desc': 'Show the whole command tree this system supports'},
    # ping like commands
    'httping':
    {'cmd': 'httping ',
     'desc': 'HTTP protocol ping-like program'},
    'ping':
    {'cmd': 'ping ',
     'desc': 'Send ICMP ECHO_REQUEST to network hosts'},
    'ping6':
    {'cmd': 'ping6 ',
     'desc': 'Send ICMP ECHO_REQUEST to network hosts, IPv6 version'},
    'tcp-ping':
    {'cmd': 'nping --tcp-connect -p 80 ',
     'desc': 'Ping using TCP protocol, using port 80'},
    'udp-ping':
    {'cmd': 'nping --udp -p 53 ',
     'desc': 'Ping using UDP protocol, using port 53'},
    # traceroute commands
    'traceroute':
    {'cmd': 'traceroute',
     'desc': 'Trace route in ICMP protocol'},
    'traceroute6':
    {'cmd': 'traceroute6',
     'desc': 'Trace route in ICMP protocol, IPv6 version'},
    'tcp-traceroute':
    {'cmd': '/usr/sbin/tcptraceroute ',
     'desc': 'Trace route in TCP protocol, using port 80'},
    'udp-traceroute':
    {'cmd': 'traceroute -U -p 53 ',
     'desc': 'Trace route in UDP protocol, using port 53'},
}

log_cmd = {
    'telnet':
    {'cmd': 'telnet',
     'desc': 'Establish a Telnet connection'},
    'ssh':
    {'cmd': 'ssh',
     'desc': 'Establish a ssh client connection'},
}

all_cmd = dict(nolog_cmd, **log_cmd)


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


def complete_cmd(rawcmd, d=all_cmd, level=0):
    """Finish user requested command, it maybe part command, so complete
    it first, then could be passed to real processores. Return as is if
    nothing matched.
    d = all_cmd, level = 0 is for first iteration, these will be override
    in next loop.

    Returns as-is if none matched or multiple matched.
    """
    rawcmd_list = rawcmd.split()
    if (level + 1) > len(rawcmd_list) or not isinstance(d, dict):
        return rawcmd
    """This function is looply invoked, so you can't just walk through
    rawcmd_list. In here, we get the element first, then wrap to
    list again.
    """
    for c in [rawcmd_list[level]]:
        if c in d.keys():
            matched = [c]
        else:
            matched = [x for x in d.keys() if x.startswith(c)]
        if not matched or len(matched) > 1:
            # matched=[]: nothing matched
            # len(matched) > 1: matched too many
            return rawcmd
        if matched and len(matched) == 1:  # matched exactly one
            rawcmd_list[level] = matched[0]
        # Try to get next level dict
        try:
            nextdict = d.get(matched[0]).get('nextlevel')
            newcmd = complete_cmd(' '.join(rawcmd_list),
                                  d=nextdict, level=(level + 1))
        except AttributeError:
            continue
    return newcmd


class MLCompleter(object):  # Custom completer
    """Means Multi-Level Completer, used to complete multi level rawcmds
    Usage:
    completer = MLCompleter(["hello", "hi", "how are you", "goodbye", "great"])
    readline.set_completer(completer.complete)
    readline.parse_and_bind('tab: complete')

    input = input("Input: ")
    print("You entered", input)
    """
    def __init__(self):
        """This variable should not be initialized here, get it on demand and
        in realtime.
            origcmd = readline.get_line_buffer()
        """

    def complete(self, text, state):
        response = None
        options = sorted(self.possible_options())
        if state == 0:  # on first trigger, build possible matches
            if text:    # cache matches (entries that start with entered text)
                self.matches = [s for s in options if s and s.startswith(text)]
                logging.debug('MLCompleter: %s => %s' % (repr(text),
                                                         self.matches))
            else:
                # no text entered, return all possible options.
                # If use 'matches' instead of 'self.matches', all possible
                # options won't be displayed.
                self.matches = options[:]
                logging.debug('MLCompleter: empty input')
        # return match indexed by state
        try:
            response = self.matches[state]
        except IndexError:
            return None
        return response + ' '  # return matched word, plus a space

    def possible_options(self):
        """Parse user requested command, and recursively read nextlevel key
        in command defination.
            idx= follows list index rules, and starts with 0.
        """
        origcmd = readline.get_line_buffer()
        origcmd_list = origcmd.split()
        begin = readline.get_begidx()
        end = readline.get_endidx()
        being_completed = origcmd[begin:end]
        logging.debug('MLCompleter: begin=%d end=%d being_completed=%s' %
                      (begin, end, being_completed,))
        if being_completed == '':  # readline.get_line_buffer().endswith(' ')
            idx = len(origcmd_list)
        else:
            # Match from end to begin
            origcmd_list.reverse()
            ridx = origcmd_list.index(being_completed)
            origcmd_list.reverse()
            idx = len(origcmd_list) - ridx - 1
        logging.debug('MLCompleter: idx=%d' % idx)
        # Complete possible partial commands
        fullcmd = complete_cmd(origcmd)
        fullcmd_list = fullcmd.split()
        d = all_cmd
        for level in range(idx + 1):
            if not isinstance(d, dict):
                r = None
                break
            if level < idx:
                d = d.get(fullcmd_list[level]).get('nextlevel')
            else:
                r = [k for k in d.keys() if not k.startswith('<')]
        if r is None or r == []:
            return self.module_specific_options(fullcmd)
        else:
            logging.debug("possible_options: won't do module_specific_options")
            return r

    def module_specific_options(self, fullcmd):
        import importlib
        cl = fullcmd.split()
        modname = 'cli.' + cl[0]
        logging.debug('MLCompleter: load module named: %s' % modname)
        # importlib.import_module(modname)
        mod = importlib.import_module(modname)
        try:
            complete_class = getattr(mod, 'complete')
            if readline.get_line_buffer().endswith(' '):
                func_name = '_'.join(cl[1:])
            else:
                func_name = '_'.join(cl[1:-1])
            logging.debug('module_specific_options: func=%s' % func_name)
            func = getattr(complete_class, func_name)
            return func()
        except AttributeError:
            return None


def do_config(rawcmd):
    from cli.config import do_config
    do_config(rawcmd)


def do_dns(rawcmd):
    from cli.dns import do_dns
    do_dns(rawcmd)


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


def do_tree(rawcmd, d=all_cmd, level=1):
    desc = ''
    # Determine just, ident more space*4 if not level 1
    if maxlen(d.keys()) > maxlen(all_cmd.keys()):
        just = maxlen(d.keys()) + level
    else:
        just = maxlen(all_cmd.keys())
    # Do not add leading space if it's level 1
    if level == 1:
        space = ''
    else:
        space = ' ' * 4 * (level - 1)
    # Start walking
    for k, v in sorted(d.items()):
        if k != 'nextlevel' and isinstance(v, dict):
            desc = v.get('desc')
            print(space + k.ljust(just + 1), desc)
        if isinstance(v, dict) and v.get('nextlevel') is not None:
            level += 1
            do_tree('', d=v.get('nextlevel'), level=level)
            level -= 1


class route(str):
    """Route user requested command to proper processor or model."""
    def __init__(self, rawcmd):
        rawcmd = rawcmd.strip()
        rawcmd = complete_cmd(rawcmd)
        try:
            l1cmd = rawcmd.split()[0]
        except IndexError:
            return
        # Replace possible partial command with completed command
        logging.debug('completed full command is: ' + rawcmd)
        self.rawcmd = rawcmd
        self.l1cmd = l1cmd
        # Routing to a hook that won't log screen
        if l1cmd == '?':
            say.available_cmds(all_cmd)
        elif l1cmd in all_cmd.keys():
            if all_cmd.get(l1cmd).get('cmd') is None:
                logging.debug('routed to to_unmapped_cmd: ' + l1cmd)
                self.to_unmapped_cmd(rawcmd)
            else:
                logging.debug('routed to to_mapped_cmd: ' + l1cmd)
                self.to_mapped_cmd(rawcmd)
        else:
            say.no_cmd(rawcmd)
            av = [c for c in all_cmd.keys() if c.startswith(self.l1cmd)]
            if av:
                say.available_cmds(all_cmd, justshow=av)
            else:
                say.available_cmds(all_cmd)

    def to_unmapped_cmd(self, rawcmd):
        """Find the function named starts with "do_", and invoke it"""
        import cli
        try:
            func = getattr(cli, 'do_' + self.l1cmd)
            logging.debug('routed to builtin function: do_' + self.l1cmd)
            return func(rawcmd)
        except AttributeError:
            logging.debug('no such function: do_' + self.l1cmd)
            say.no_cmd(rawcmd)
            return

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

    def filter_input(self):
        """Filter out user requested commands, or print WARN messages
        when they do something really dangerous."""
        pass

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

    def start_session(self):
        # Start pexpect session
        try:
            return pexpect.spawn('bash', ['-c', self.rawcmd])
        except (SystemExit, pexpect.ExceptionPexpect) as e:
            print(e)
            return None
        except (KeyboardInterrupt, pexpect.EOF, pexpect.TIMEOUT):
            return None

    def with_log(self):
        from cli.log import get_log_file
        rawcmd = self.rawcmd
        # Check if arguments provided
        if len(self.rawcmd_list) == 1:
            os.system(rawcmd + ' -h')
            return
        log_filename = get_log_file(self.rawcmd.replace(' ', '-'))
        fout = open(log_filename, "wb")
        self.fout = fout
        # Check if command exists
        if not cmd_exists(self.rawcmd_list[0]):
            say.no_sys_cmd(self.rawcmd_list[0])
            return False
        thissession = self.start_session()
        if thissession is None:
            fout.close()
            return None
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
