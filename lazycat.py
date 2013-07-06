#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""This program spawns a pseudo-shell and gives the user interactive control.
The entire ssh/telnet session is logged to a file, others won't be logged.
"""

try:
	import glob, string
	import os, sys, time, getopt
	import signal, fcntl, termios, struct
	import threading
	import pexpect, re
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

prompt = "\033[1;32mjumper\033[0m:"

builtin_level1 = ['autorun', 'autotemplate', 'clear', 'dns', 'help', 'log', 'quit', 'show']
builtin_autorun = ['config', 'enable-password', 'password']
builtin_autotemplate = ['show', 'add', 'del']
builtin_dns = ['resolve', 'arpa', 'trace']
builtin_log = ['list', 'view', 'del']
builtin_show = ['my-permission', 'user']

autorun_comp = ['autorun']
autotemplate_comp = ['autotemplate']
clear_comp = ['c', 'cl', 'cle', 'clear']
dns_comp = ['d', 'dn', 'dns']
help_comp = ['h', 'he', 'hel', 'help']
log_comp = ['l', 'lo', 'log']
log_del_comp = ['d', 'de', 'del']
log_list_comp = ['l', 'li', 'lis', 'list']
log_view_comp = ['v', 'vi', 'vie', 'view']
quit_comp = ['q', 'qu', 'qui', 'quit']
show_comp = ['sh', 'sho', 'show']
show_mypermission_comp = ['m', 'my', 'my-' 'my-p', 'my-permission']
show_user_comp = ['u', 'us', 'use', 'user']

# nolog_cmd = ['ping', 'tcptraceroute', 'traceroute']
nolog_cmd = ['ping', 'traceroute']
log_cmd = ['ssh', 'telnet']
all_cmd = builtin_level1 + log_cmd + nolog_cmd

global path
path = os.environ.get('HOME') + '/%4d%02d%02d' % time.localtime()[:-6]
if not os.path.isdir(path):
	os.makedirs(path)
flush_interval = 10
title = os.getlogin() + "@" + gethostname(); del gethostname
global_pexpect_instance = None # Used by signal handler

PROMPT = '[#$:>] '

def exit_with_usage():

	print globals()['__doc__']
	os._exit(1)

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

def run_with_log():
	global fout
	log_filename = path + '/%4d%02d%02d-%02d%02d%02d-' % time.localtime()[:-3] + \
		os.getlogin() + '-' + command.strip().replace(' ', '-')
	fout = file (log_filename, "ab")

	# Begin log with timestamp
	# fout.write ('%4d-%02d-%02dT%02d:%02d:%02d ' % time.localtime()[:-3] + title + "\n")
	bgrun(flushlog).start()

	try:
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
	thissession.logfile = fout
	global global_pexpect_instance
	global_pexpect_instance = thissession
	signal.signal(signal.SIGWINCH, sigwinch_passthrough)

	fout.write("### First command: %s\n" % command)
	print ("\033[0;31mOperation logging started, have fun :)\033[0m")
	try:
		# thissession.interact(chr(29))
		thissession.interact()
	except OSError:
		pass
	except BaseException, e:
		print("\r" + str(e))
		return 1

	if not thissession.isalive():
		print ("\033[0;31mOperation logging stopped\033[0m")
		print ("Session ended: %s" % command)
		fout.close()
		return 0

	print ("\033[0;31mOperation logging stopped\033[0m")
	fout.close()
	return 0

def run_without_log():
	os.system(command)

def autorun():
	print("""Not implemented yet
			
This function is intended to automatically config device with predefined
template, such as logging, password, etc.
""")
	return True

def autotemplate():
	autorun()

def dns():
	print("Not implemented yet")
	return 1

	sub = command.split()
	sub.reverse()
	# If no sub-command, print usable sub-command and return
	if len(sub) == 1:
		print_cmd(builtin_dns, msg="All available sub-commands:")
		return 1
	else:
		subcmd = sub.pop()	# pop out 'show'

	subcmd = sub.pop()

def log():
	sub = command.split()
	sub.reverse()
	# If no sub-command, print usable sub-command and return
	if len(sub) == 1:
		print_cmd(builtin_log, msg="All available sub-commands:")
		return 1
	else:
		subcmd = sub.pop()	# pop out 'show'

	subcmd = sub.pop()
	if subcmd in log_del_comp:
		"""eg: log del 20130705-110150-mj-telnet-10.0.0.1
		"""
		print ('Permission denied')
	elif subcmd in log_list_comp:
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
	elif subcmd in log_view_comp:
		"""eg: log view 20130705-110150-mj-telnet-10.0.0.1
		"""
		try:
			f = sub.pop()
		except Exception:
			print("Need file name listed by \"log list\".")
			return 1

		f = path + '/' + f
		if os.path.isfile(f):
			os.system("cat " + f)
		else:
			print("log view %s: No such file or directory" % str(f))
			return 1
	else:
		print_cmd(builtin_log, msg="All available sub-commands:")

def print_help():
	"""快捷键:
	?	显示可用命令
	Ctrl-u	删除到行首
	Ctrl-w	删除光标前面一个词
	"""
	# print (print_help.__doc__)
	try:
		print string.replace(print_help.__doc__,'\n\t','\n')
	except Exception, e:
		print(str(e))

	return 0

def show():
	sub = command.split()
	sub.reverse()
	# If no sub-command, print usable sub-command and return
	if len(sub) == 1:
		print_cmd(builtin_show, msg="All available sub-commands:")
		return 1
	else:
		subcmd = sub.pop()	# pop out 'show'

	subcmd = sub.pop()
	if subcmd in show_mypermission_comp:
		"""show my-permission
		"""
		print("Not implemented yet")
	elif subcmd in show_user_comp:
		"""show user
		"""
		os.system('w -f')
	elif subcmd is None:
		print_cmd(builtin_show, msg="All available sub-commands:")
	else:
		print_cmd(builtin_show, msg="All available sub-commands:")

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
	while True:
		print (prompt),	# buggy, add history

		global command
		# Get input, and deal with exceptions
		try:
			command = raw_input()
		except KeyboardInterrupt:
			"""Ignore Ctrl-C"""
			print ("\r")
			continue
		except EOFError:
			"""Ignore Ctrl-D"""
			print ("^D")
			continue

		# Determine if command is empty
		if not command.strip():
			continue

		# Classify the commands, and run them by different wrapper
		try:
			first_cmd = command.split()[0]
			if first_cmd in autorun_comp:
				autorun()
			if first_cmd in autotemplate_comp:
				autotemplate()
			elif first_cmd in clear_comp:
				os.system("clear")
			elif first_cmd in dns_comp:
				dns()
			elif first_cmd in help_comp:
				print_help()
			elif first_cmd in log_comp:
				log()
			elif first_cmd in quit_comp:
				# raise SystemExit
				os.exit()
			elif first_cmd in show_comp:
				show()
			elif len(command.split()) > 1 and first_cmd in log_cmd:
				run_with_log()
			elif len(command.split()) > 1 and first_cmd in nolog_cmd:
				run_without_log()
			else:
				print_cmd(sorted(all_cmd))
		except (KeyboardInterrupt, EOFError):
			continue

if __name__ == "__main__":
	try:
		ttywrapper()
	except (Exception, SystemExit):
		os._exit(1)

# vim: set sw=4 ts=4:
