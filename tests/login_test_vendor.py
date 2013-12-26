#!/usr/bin/env python3
import logging
import sys
sys.path = sys.path + ['..']
from dm import get_host, login
from etc import dev

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO, filename='log')

if len(sys.argv) != 2:
    print('For testing, login test on specific vendor')
    sys.exit('usage: %s <vendor>' % sys.argv[0])

vendor = sys.argv[1]
for host in dev.__dict__['hosts_' + vendor].keys():
    a = get_host(vendor, host)
    s = login.connect(a)
    if s is False:
        print('ERROR: login failed')
    else:
        s.terminate()
