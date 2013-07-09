lazycat
=======
A pseudo shell with restricted capability for AAA purpose.

Description
-----------
This program spawns a pseudo-shell and gives the user interactive control.
The entire ssh/telnet session is logged to a file, others won't be logged.

Required Python Modules
-----------------------
This program is using python2, not compatible with python3 yet.

Needed python mods beside builtins:
pexpect

Required System Commands
------------------------
hping, need root privilege, use nping from nmap instead.
tcping, buggy, can't ping IP address, not used for now.
nmap, with nping installed
httping
traceroute
tcptraceroute

Deployment
----------
1. Add to /etc/shells, eg: echo /home/lazycat.py >> /etc/shells

2. Add a user whose shell is lazycat.py, eg: useradd -m -s /home/lazycat.py testuser
and, set a password for this user.

3. Start your ssh server.

4. Take a try, eg: ssh testuser@localhost, now you got into jail ;)
