=======
lazycat
=======

A pseudo shell with restricted capability for AAA purpose.

This program is a pseudo-shell that gives the user interactive control.
The entire ssh/telnet session is logged to a file, others won't be logged.


Main Feature
============

It depends on system user account, and HOME directory is needed to store log files.

Hardware config CLI style interface, which is simple, straight forward.

Log whole ssh/telnet session into a log file.

A lot network diagnosis tools, like {icmp,tcp,udp}-ping, {icmp,tcp,udp}-traceroute, and httping.

Input auto completion by typing TAB.

DNS system diagnosis helper.

[And a lot planned feature in TODO]


Required Python Modules
=======================

See doc/INSTALL


Required System Commands
========================

hping, need root privilege, use nping from nmap instead.

tcping, buggy, can't ping IP address, not used for now.

nmap, with nping installed

httping

traceroute

tcptraceroute


Deployment
==========

1. Add to /etc/shells, eg: echo /home/lazycat.py >> /etc/shells

2. Add a user whose shell is lazycat.py, eg: useradd -m -s /home/lazycat.py testuser
and, set a password for this user.

3. Start your ssh server.

4. Take a try, eg: ssh testuser@localhost, now you got into jail ;)
