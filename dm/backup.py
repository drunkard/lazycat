import logging
from dm import get_host, login


def roll_one_class(vendor, hosts, defaults):
    for host in hosts.keys():
        roll_one_host(vendor, hosts, defaults, host)


def roll_one_host(vendor, hosts, defaults, host):
    device = get_host(vendor, hosts, defaults, host)
    # Get a connected pexpect session of host
    s = login.connect(device)
    if s is False:
        logging.error('%s login failed' % device.name)
        return False
    # Determine how to backup config, prefer upload via ftp
    from dm import save
    if hasattr(device, 'upload_config_command'):
        save.upload_via_ftp(device, s)
    elif hasattr(device, 'show_config_command'):
        save.show_config(device, s)
    else:
        logging.fatal('%s don\'t know how to save config')
        return False
