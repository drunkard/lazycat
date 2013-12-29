#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
import sys
# import psycopg2
try:
    from dm import backup_config
    from etc import lazycat_conf
except ImportError as e:
    sys.exit(e)

# Set LANG in shell
os.environ['LANG'] = 'en_US.utf8'

# logging config
if not os.path.isdir(lazycat_conf.LOG_PATH):
    os.makedirs(lazycat_conf.LOG_PATH)
if lazycat_conf.DEBUG_FG == 1:
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=lazycat_conf.DEBUG_LEVEL)
else:
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=lazycat_conf.DEBUG_LEVEL,
                        filename=lazycat_conf.DEVCONF_LOG, encoding='utf-8')


def devconf():
    """Do network device related things.

    Options:
    -b [host]
        backup network device config of host, backup all hosts if no host given
    -c tasklet [host]
        execute check on given host, on all hosts by default, supported checks:
            syslog - syslog server config on network device
    """
    # TODO: implement argument parser
    # TODO: count stats
    # stat_login_fail = []
    # stat_password_wrong = []
    # stat_upload_error = []
    # TODO: try again while escalating_conflicted = 1
    backup_config()


if __name__ == "__main__":
    devconf()
