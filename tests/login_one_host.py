#!/usr/bin/env python3
import logging
import sys
sys.path = sys.path + ['..']
from dm import get_host, login

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

if len(sys.argv) != 3:
    print('For testing, login to one host')
    sys.exit('usage: %s <vendor> <hostname>' % sys.argv[0])

vendor = sys.argv[1]
host = sys.argv[2]
a = get_host(vendor, host)
s = login.connect(a)
if s is not False:
    s.interact()
