import logging
from dm import get_host, login


def roll_on_vendor(vendor):
    from etc import dev
    hosts_set_name = 'hosts_' + vendor
    hosts = dev.__dict__[hosts_set_name]
    for host in hosts.keys():
        roll_on_host(vendor, host)


def roll_on_host(vendor, host):
    device = get_host(vendor, host)
    # Get a connected pexpect session of host
    s = login.connect(device)
    if s is False:
        logging.error('%s login failed' % device.name)
        return False
    # Save this session as device attribute
    device.session = s
    # Determine how to backup config, prefer upload via ftp
    from dm import save
    if hasattr(device, 'upload_config_command'):
        save.upload_via_ftp(device, s)
    elif hasattr(device, 'show_config_command'):
        save.show_config(device, s)
    else:
        logging.fatal('%s don\'t know how to save config')
        return False
