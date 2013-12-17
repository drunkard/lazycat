"""
Device management
"""
import logging
from functools import partial
from dm import model
from lib import hanzi2pinyin


def backup_config():
    """backup config from network devices"""
    from etc import dev
    from dm.backup import roll_one_class
    if not hasattr(dev, 'supported_class'):
        return False
    # Roll all supported classes
    for c in dev.supported_class:
        hosts_set_name = 'hosts_' + c
        defaults_set_name = 'default_' + c
        defaults = dev.__dict__[defaults_set_name]
        hosts = dev.__dict__[hosts_set_name]
        vendor = c
        roll_one_class(vendor, hosts, defaults)


def check_attr(device, attrlist):
    """Check if all attributes in list exists"""
    for i in attrlist:
        if not hasattr(device, i):
            logging.error('%s lacks setting: %s' % (device.name, i))
            return False
    return True


def fix_commands(device_dict):
    """Replace variable names with settings in etc/.
    RC(replace command)

    The variables to be replaced should fulfill these conditions:
        - command key in list 'has_vars' in dm.model
        - variable to be replaced in list 'should_be_replaced' in dm.model
        - variable to be replaced must named as RC_*_RC, like: replace
            'RC_FTP_SERVER_ADDR_RC' with FTP_SERVER_ADDR
    """
    from dm.model import has_vars
    # Convert Chinese characters to PinYin
    device_dict['name_lingus'] = device_dict['name']
    device_dict['name_en'] = hanzi2pinyin(device_dict['name'])
    # Replace variables with settings
    for k in has_vars:
        device_dict[k] = replace_var_in_cmd(device_dict, k)
        logging.debug('%s fix_commands %s="%s"' %
                      (device_dict['name'], k, device_dict[k]))
    return device_dict


def get_host(vendor, hosts, defaults, host_name):
    """Get all information of a host by host_name, the information comes from:
        etc.dev.default_"vendor"
        etc.dev.hosts_"vendor"
        dm.model."vendor"
    merge them, then convert this dict to a host object.
    """
    host_info = hosts.get(host_name)
    # Add vendor key
    host_info = dict(host_info, **{'vendor': vendor})
    # Retrieve per host settings
    if host_info is None:
        logging.error('%s no such host in hosts_%s' % (host_name, vendor))
        return None
    logging.debug("%s got per host setting" % (host_name))

    # Retrieve vendor defaults in etc.dev, then merge to host_info
    host_info = dict(defaults, **host_info)
    logging.debug("%s applied default config from etc.dev with name: %s" %
                  (host_name, 'default_' + vendor))

    # Retrieve vendor defaults im dm.model, then merge to host_info
    for i in dir(model):
        if i == vendor:
            host_info = dict(model.__dict__[vendor].__dict__, **host_info)
            break
    logging.debug("%s applied default config from dm.model with name: %s" %
                  (host_name, vendor))

    # TODO: update device.admin with config in etc.admin
    # Replace variables with setting in etc.lazycat_conf
    host_info = fix_commands(host_info)
    # Convert merged device info dict into device object
    dict2dev = partial(type, 'dict2dev', ())
    dev = dict2dev(host_info)
    return dev


def random_char(y):
    import string
    from random import choice
    return ''.join(choice(string.ascii_letters) for x in range(y))


def replace_var_in_cmd(device_dict, cmdname):
    """Replace those variables (named RC_*_RC) with settings in
    etc.lazycat_conf or host attribute.
    """
    from etc import lazycat_conf
    from dm.model import should_be_replaced
    for var in should_be_replaced:
        v = device_dict[cmdname]
        vinc = 'RC_' + var + '_RC'
        logging.debug('  replacing %s' % var)
        if var == 'NAME':
            device_dict[cmdname] = v.replace(vinc, device_dict['name_en'])
            continue
        elif var == 'IP':
            device_dict[cmdname] = v.replace(vinc, device_dict['ip'])
            continue
        elif hasattr(lazycat_conf, var):
            device_dict[cmdname] = v.replace(vinc,
                                             lazycat_conf.__dict__[var])
        else:
            # If dont raise exception, may mis-operate network device, so do it
            # carefully.
            raise KeyError
    return ' '.join(device_dict[cmdname].split())


def show_terminal(session):
    """show all contents of session.before in pexpect session"""
    for line in session.before.decode().splitlines():
        print(line)
