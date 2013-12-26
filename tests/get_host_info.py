#!/usr/bin/env python3
import logging
import sys
sys.path = sys.path + ['..']
from etc import dev
from dm import get_host

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

if len(sys.argv) != 3:
    print('Get all predefined host info, but no runtime info')
    sys.exit('usage: %s <vendor> <hostname>' % sys.argv[0])

vendor = sys.argv[1]
h = sys.argv[2]

hosts = dev.__dict__['hosts_' + vendor].keys()
dev = get_host(vendor, h)
print('')
width = 34
for attr in dir(dev):
    if not attr.startswith('__'):
        print('%s = "%s"' % (attr.rjust(width, ' '), str(dev.__dict__[attr])))
