#!/usr/bin/env python3
import logging
import sys
sys.path = sys.path + ['..']
from dm import git

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

if len(sys.argv) != 2:
    print('For testing, git commit file with firm path')
    sys.exit('eg: %s /data/lazycat/devconf/greenway/ST-1--10.0.0.1.cfg' %
             sys.argv[0])

f = sys.argv[1]
git.commit(f)
git.push2server()
