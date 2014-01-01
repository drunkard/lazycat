# -*- coding: utf-8 -*-


# These commands' output to ncurses like window, which is hard to strip
OMIT_OUTPUT = ['atop', 'htop', 'iotop', 'iftop', 'dnstop']


# Command enumerate
nolog_cmd = [
    # {'KEY': ('showed cmd', 'real cmd, maybe system cmd', 'Description')},
    # Single module functions
    'clear',
    'config',
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


l1_map = [
    # ('CMD name', 'Real Linux CMD', 'Description'),
    ('password', 'passwd', 'Change password'),
    ('time', 'cal -3; date', 'Show local date and time'),
    # hping need root privilege
    # ('tcp-ping', 'hping -p 80 --syn ',
    #  'Ping using TCP protocol, default 80 port'),
    # ('udp-ping', 'hping --udp -p 53 ',
    #  'Ping using UDP protocol, default 53 port')
    ('tcp-ping', 'nping --tcp-connect -p 80 ',
     'Ping using TCP protocol, using port 80'),
    ('udp-ping', 'nping --udp -p 53 ',
     'Ping using UDP protocol, using port 53'),
    ('tcp-traceroute', 'tcptraceroute ',
     'traceroute using TCP protocol, using port 80'),
    # ('tcp-traceroute', 'traceroute -M tcp -p 80 ',
    #  'traceroute using TCP protocol, using port 80'),
    ('udp-traceroute', 'traceroute -U -p 53 ',
     'traceroute using UDP protocol, using port 53')]


# Level 2 commands definations
log_l2 = [
    'list',
    'view']
show_l2 = [
    'all-jumper',
    'history',
    'my-permission',
    'user',
    'this-server',
    'time']


# Partial command definations
clear_comp = ['cl', 'cle', 'clear']
help_comp = ['he', 'hel', 'help']
log_comp = ['l', 'lo', 'log']
log_list_comp = ['l', 'li', 'lis', 'list']
log_view_comp = ['v', 'vi', 'vie', 'view']
quit_comp = ['q', 'qu', 'qui', 'quit']
show_comp = ['sh', 'sho', 'show']
show_history_comp = ['h', 'history']
show_my_permission_comp = ['m', 'my', 'my-' 'my-p', 'my-permission']
show_user_comp = ['u', 'us', 'use', 'user']
show_this_server_comp = ['th', 'this-server']
show_time_comp = ['ti', 'tim', 'time']
