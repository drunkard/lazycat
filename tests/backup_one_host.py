#!/usr/bin/env python3
import logging
import sys
sys.path = sys.path + ['..']
from dm.backup import roll_on_host

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)


if len(sys.argv) != 3:
    print('backup config of one host')
    sys.exit('usage: %s <vendor> <hostname>' % sys.argv[0])

v = sys.argv[1]
host = sys.argv[2]
roll_on_host(v, host)
