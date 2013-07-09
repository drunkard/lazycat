#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""This program is a pseudo-shell and gives the user interactive control.
The entire ssh/telnet session is logged to a file, others won't be logged.
"""

try:
	import atexit
	import glob, string
	import os, sys, time, getopt
	import signal, fcntl, termios, struct
	# import ANSI
	import threading
	import pexpect, re
	import rlcompleter, readline
	# import rlcompleter2
	# import IPython.core.completer as completer
	from socket import gethostname
except ImportError, e:
	raise ImportError (str(e) + """

A critical module was not found. Probably this operating system does not
support it. Pexpect is intended for UNIX-like operating systems.""")

__author__ = "Drunkard Zhang"
__email__ = "gongfan193@gmail.com"
__version__ = "0.1"
__productname__ = "lazycat"
__description__ = "A pseudo shell with restricted capability for AAA purpose."

# Color defines
OFF = '\033[0m'
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
BLINK = '\033[5m'
BLUE = '\033[0;34m'
BLUE_BOLD = '\033[1;34m'
MAGENTA = '\033[0;35m'
MAGENTA_BOLD = '\033[1;35m'
CYAN = '\033[0;36m'
CYAN_BOLD = '\033[1;36m'
WHITE = '\033[0;37m'
WHITE_BOLD = '\033[1;37m'

DEBUG = 0
PATH = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
historyPath = os.path.expanduser('~/.' + __productname__ + '_history')
prompts = GREEN_BOLD + "jumper" + OFF + ":"
PROMPT = '[#$:>] '

# Command enumerate
builtin_l1 = ['auto', 'clear', 'config', 'dns', 'help', 'log', 'quit', 'show']
nolog_cmd = ['httping', 'ping', 'ping6', 'tcp-ping', 'udp-ping',
	'traceroute', 'traceroute6', 'tcp-traceroute', 'udp-traceroute',
	'password']
log_cmd = ['ssh', 'telnet']
all_cmd = builtin_l1 + log_cmd + nolog_cmd

builtin_l2_auto = ['list', 'add', 'del',
	'config', 'enable-password', 'password']
builtin_l2_config = ['user', 'permission', 'tui']
builtin_l2_dns = ['resolve', 'arpa', 'trace']
builtin_l2_log = ['list-today', 'search', 'view', 'del']
builtin_l2_show = ['my-permission', 'user', 'this-server', 'time']

builtin_l3_log_search = ['by-date', 'by-time', 'by-device-ip', 'by-device-name']

auto_comp = ['auto']
clear_comp = ['cl', 'cle', 'clear']
dns_comp = ['d', 'dn', 'dns']
help_comp = ['h', 'he', 'hel', 'help']
log_comp = ['l', 'lo', 'log']
log_del_comp = ['d', 'de', 'del']
log_list_comp = ['l', 'li', 'lis', 'list']
log_view_comp = ['v', 'vi', 'vie', 'view']
quit_comp = ['q', 'qu', 'qui', 'quit']
show_comp = ['sh', 'sho', 'show']
show_my_permission_comp = ['m', 'my', 'my-' 'my-p', 'my-permission']
show_user_comp = ['u', 'us', 'use', 'user']
show_this_server_comp = ['th', 'this-server']
show_time_comp = ['ti', 'tim', 'time']

map_resolver = {'name':0, 'cmd':1, 'desc':2}
l1_map = [
	('CMD name', 'Real Linux CMD', 'Description'),
	('password', 'passwd', 'Change password'),
	('time', 'cal -3; date', 'Show local date and time'),
	# hping need root privilege
	# ('tcp-ping', 'hping -p 80 --syn ', 'Ping using TCP protocol, default 80 port'),
	# ('udp-ping', 'hping --udp -p 53 ', 'Ping using UDP protocol, default 53 port')
	('tcp-ping', 'nping --tcp-connect -p 80 ', 'Ping using TCP protocol, using port 80'),
	('udp-ping', 'nping --udp -p 53 ', 'Ping using UDP protocol, using port 53'),
	('tcp-traceroute', 'tcptraceroute ', 'traceroute using TCP protocol, using port 80'),
	# ('tcp-traceroute', 'traceroute -M tcp -p 80 ', 'traceroute using TCP protocol, using port 80'),
	('udp-traceroute', 'traceroute -U -p 53 ', 'traceroute using UDP protocol, using port 53')
	]
dns_srcip_map = [
	('1.1.1.1', '42.196.0.0/16, 49.221.128.0/17, 101.244.0.0/15, 118.205.1.0/17'),
	('default', 'default')
	]

os.putenv('PATH', PATH)
global path
path = os.environ.get('HOME') + '/%4d%02d%02d' % time.localtime()[:-6]
if not os.path.isdir(path):
	os.makedirs(path)
flush_interval = 10
title = os.getlogin() + "@" + gethostname(); del gethostname
global_pexpect_instance = None # Used by signal handler

def debug_interactive():
	"""Insert IPython interact terminal, and make debug simpler."""

	if DEBUG == 1:
		from IPython import embed
		embed()
	else:
		return True

def exit_with_usage():

	print globals()['__doc__']
	os._exit(1)

class MLCompleter(object):  # Custom completer
	"""Means Multi-Level Completer, will be used to complete multi level commands
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
		# cursor_pos = readline.get_begidx()
		# self.complete(text, text, cursor_pos)
		if state == 0:	# on first trigger, build possible matches
			if text:	# cache matches (entries that start with entered text)
				self.matches = [s for s in self.options
						if s and s.startswith(text)]
				# print("\ntext value: %s" % self.matches)	# debug
			else:	# no text entered, all matches possible
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
			fout.write ('\n### %4d-%02d-%02dT%02d:%02d:%02d ' % time.localtime()[:-3] + title + "\n")
			# log_filename.flush()
			time.sleep(flush_interval)
		except ValueError:
			break
			# for debug
			print("flushlog(): I/O operation failed, maybe lost some log")
			time.sleep(10)	# To avoid dead lock
			return 127

def print_cmd(cmdlist, msg="All available commands:"):
		print (msg)
		if len(cmdlist) > 0:
			for c in sorted(cmdlist):
				print ("  " + str(c))

def print_not_implemented():
	print("%sThis is planned, but not implemented yet.%s\n" % (CYAN_BOLD, OFF))

def save_history(historyPath=historyPath):
	print 'Olla, save_history'

	f = open(historyPath)
	try:
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
	if find_executable(command, path=PATH) == None:
		return False
	else:
		return True

def run_with_log():
	global fout
	log_filename = path + '/%4d%02d%02d-%02d%02d%02d-' % time.localtime()[:-3] + \
		os.getlogin() + '-' + command.strip().replace(' ', '-')
	fout = file (log_filename, "ab")

	# Begin log with timestamp
	# fout.write ('%4d-%02d-%02dT%02d:%02d:%02d ' % time.localtime()[:-3] + title + "\n")
	bgrun(flushlog).start()

	try:
		if which(command.split()[0]):
			pass
		else:
			print("The command %s%s%s is not usable, please notify your administrator." % (RED_BLINK, command.split()[0], OFF))
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
	print ("%sOperation logging started, have fun :)%s" % (RED, OFF))
	try:
		# thissession.interact(chr(29))
		thissession.interact()
	except OSError:
		pass
	except BaseException, e:
		print("\r" + str(e))
		return 1

	if not thissession.isalive():
		print ("\n%sOperation logging stopped%s" % (RED, OFF))
		print ("Session ended: %s" % command)
		fout.close()
		return 0

	print ("%sOperation logging stopped%s" % (RED, OFF))
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
		pass	# goto try: part
	elif FOUND_IN_MAP == True:
		pass
	else:
		print("This function is not usable, please check it in PATH or l1_map: %s" % command)
		return 1

	# Run the command, this should be OK
	try:
		print("Full command executed: %s" % command)
		os.system(command)
	except BaseException, e:
		print(str(e))
		print("\r")
		return 0

def auto():
	print_not_implemented()
	print("""This function is intended to automatically config device with predefined
template, such as logging, password, etc.
""")
	return True

def dns():
	print("Not implemented yet")
	return 1

	sub = command.split()
	sub.reverse()
	# If no sub-command, print usable sub-command and return
	if len(sub) == 1:
		print_cmd(builtin_l2_dns, msg="All available sub-commands:")
		return 1
	else:
		l2cmd = sub.pop()	# pop out 'show'

	l2cmd = sub.pop()

def log():
	sub = command.split()
	sub.reverse()
	# If no sub-command, print usable sub-command and return
	if len(sub) == 1:
		print_cmd(builtin_l2_log, msg="All available sub-commands:")
		return 1
	else:
		l2cmd = sub.pop()	# pop out 'show'

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
			print("  Date  - Time - User - CMD - Host")
			for f in files:
				print(str(os.path.basename(f)))
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
			os.system("less -r %s" % f)
		else:
			print("log view %s: No such file or directory" % str(f))
			return 1
	else:
		print_cmd(builtin_l2_log, msg="All available sub-commands:")

def print_help():
	"""终端快捷键：
	?		显示可用命令

	Ctrl-A		光标移到行首
	Ctrl-E		光标移到行尾
	Ctrl-B | Left	左移光标
	Ctrl-F | Right	右移光标
	Ctrl-P | Up	前一个命令
	Ctrl-N | Down	后一个命令

	Backspace	删除左边一个字符
	Ctrl-D		删除右边一个字符

	Ctrl-U		剪切光标到行首之间的字符
	Ctrl-K		剪切光标到行尾之间的字符
	Ctrl-W		剪切光标左边一个词
	Alt-D		剪切光标右边一个词

	Ctrl-R		向前搜索历史命令
	Return		把命令发给终端
	"""
	# print (print_help.__doc__)
	try:
		print string.replace(print_help.__doc__,'\n\t','\n')
	except Exception, e:
		print(str(e))

	return 0

def quit():
	print ("%s%sSee you next time ;)%s" % (BLINK, CYAN_BOLD, OFF))
	# raise SystemExit
	os.exit()

def show():
	sub = command.split()
	sub.reverse()
	# If no sub-command, print usable sub-command and return
	if len(sub) == 1:
		print_cmd(builtin_l2_show, msg="All available sub-commands:")
		return 1
	else:
		l2cmd = sub.pop()	# pop out 'show'

	l2cmd = sub.pop()
	if l2cmd in show_my_permission_comp:
		"""show my-permission
		"""
		print("Not implemented yet")
	elif l2cmd in show_user_comp:
		"""show user
		"""
		os.system('w -f')
	elif l2cmd in show_this_server_comp:
		"""show this-server
		"""
		print("IP address configs on this jumper:")
		os.system('ip addr')

		print("\nRoutes on this jumper:")
		os.system('ip route')
	elif l2cmd in show_time_comp:
		"""show time
		"""
		os.system('cal -3; echo; date')
	elif l2cmd is None:
		print_cmd(builtin_l2_show, msg="All available sub-commands:")
	else:
		print_cmd(builtin_l2_show, msg="All available sub-commands:")

def sigwinch_passthrough (sig, data):
	# Check for buggy platforms (see pexpect.setwinsize()).
	if 'TIOCGWINSZ' in dir(termios):
		TIOCGWINSZ = termios.TIOCGWINSZ
	else:
		TIOCGWINSZ = 1074295912 # assume
	s = struct.pack ("HHHH", 0, 0, 0, 0)
	a = struct.unpack ('HHHH', fcntl.ioctl(sys.stdout.fileno(), TIOCGWINSZ , s))
	global global_pexpect_instance
	global_pexpect_instance.setwinsize(a[0],a[1])

def ttywrapper():
	# t = ANSI.term()

	if os.path.exists(historyPath):
		readline.read_history_file(historyPath)

	try:
		# l1_completer = MLCompleter(all_cmd)
		# readline.set_completer(l1_completer.complete)
		readline.parse_and_bind('tab: complete')
		readline.set_completer_delims(' ')
	except Exception, e:
		print(str(e))

	while 1:
		readline.set_completer( MLCompleter(all_cmd).complete )
		print (prompts),	# buggy, catch cursor position

		global command
		# Get input, and deal with exceptions
		try:
			command = raw_input()
		except KeyboardInterrupt:
			"""Ctrl-C"""
			print ("^C")
			continue
		except EOFError:
			"""Ctrl-D"""
			# print ("^D")
			# continue
			print("quit")
			quit()

		# Determine if command is empty
		if not command.strip():
			continue

		# Classify the commands, and run them by different wrapper
		command = command.strip()
		try:
			l1cmd = command.split()[0]
			if l1cmd in auto_comp:
				auto()
			elif l1cmd in clear_comp:
				os.system("clear")
			elif l1cmd in help_comp:
				print_help()
			elif l1cmd in log_comp:
				log()
			elif l1cmd in quit_comp:
				quit()
			elif l1cmd in show_comp:
				debug_interactive()
				show()
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
#			elif l1cmd in builtin_l1:
#				try:
#					s = command.replace(' ', '.')
#					s = str_to_class(s)
#					print type(s)
#					s
#				except Exception, e:
#					print(str(e))
			else:
				if l1cmd in all_cmd:
					print_not_implemented()

				print("%sBad command:%s %s\n" % (RED_BG, OFF, command))
				print_cmd(sorted(all_cmd))
		except (KeyboardInterrupt, EOFError):
			continue

if __name__ == "__main__":
	# buggy, this is not working
	atexit.register(save_history)

	try:
		ttywrapper()
	except (Exception, SystemExit):
		os._exit(1)

# vim: set sw=4 ts=4:
