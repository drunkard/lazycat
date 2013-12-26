#!/usr/bin/env python3
import logging
import sys
sys.path = sys.path + ['..']
from etc import dev

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

for ht in dev.supported_class:
    print(ht, end=' = ')
    print(dev.__dict__['hosts_' + ht].keys())
    print('')
