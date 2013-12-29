#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from dm import get_host, login


def roll_on_vendor(vendor):
    from etc import dev
    hosts_set_name = 'hosts_' + vendor
    hosts = dev.__dict__[hosts_set_name]
    for host in sorted(hosts.keys()):
        try:
            roll_on_host(vendor, host)
        except Exception as e:
            logging.fatal('%s caught exception while rolling: %s' % (host, e))


def roll_on_host(vendor, host):
    device = get_host(vendor, host)
    r = True
    # Get a connected pexpect session of host
    device.session = login.connect(device)
    if device.session is False:
        logging.error('%s login failed' % device.name)
        return False
    # Determine how to backup config, prefer upload via ftp
    from dm import save
    if hasattr(device, 'upload_config_command'):
        save.upload_via_ftp(device)
    elif hasattr(device, 'show_config_command'):
        save.show_config(device)
    else:
        logging.fatal('%s don\'t know how to save config')
        r = False
    # Terminate telnet session
    if device.session is False:
        r = False
    else:
        device.session.terminate()
        r = True
    return r
