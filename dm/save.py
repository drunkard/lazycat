"""Methods used to save devices' config.
"""
import logging
import pexpect
import os
from dm import show_terminal


def enter_test(device):
    """Just send 'Enter' to device to test if last command has finished"""
    s = device.session
    s.sendline('\r')
    logging.debug('%s enter newline test' % device.name)
    i = s.expect([r'[>#\]]$'])
    if i == 0:
        logging.debug('%s enter newline test ok' % device.name)
        return True
    return False


def fix_paths(device):
    """Fix ftp server side paths"""
    from etc.lazycat_conf import DEVCONF_BACKUP_PATH
    # Update attribute device.upload_abs_path
    device.upload_abs_path = os.path.join(DEVCONF_BACKUP_PATH,
                                          device.upload_filename)
    logging.debug('%s update attribute: device.upload_abs_path = %s' %
                  (device.name, device.upload_abs_path))
    # Prepare the subdir: 'DEVCONF_BACKUP_PATH'/'device.vendor'/
    p = os.path.join(DEVCONF_BACKUP_PATH, device.vendor)
    if not os.path.isdir(p):
        logging.debug("%s mkdir: %s" % (device.name, p))
        if not os.makedirs(p):
            logging.error('%s mkdir failed: %s' % (device.name, p))
    # Update attribute device.upload_path
    device.upload_path = p
    logging.debug('%s update attribute: device.upload_path = %s' %
                  (device.name, p))
    fix_perm(p)
    return True


def fix_perm(f):
    """Fix permission of files in ftp directory"""
    import pwd
    from etc.lazycat_conf import FTP_USER
    # Check if setting exists
    if not FTP_USER:
        logging.error('Empty setting: %s, fix_perm aborted' % (FTP_USER))
        return False
    # Check if already did
    uid = pwd.getpwnam(FTP_USER).pw_uid
    gid = pwd.getpwnam(FTP_USER).pw_gid
    if os.stat(f).st_uid == uid and os.stat(f).st_gid == gid:
        logging.debug('chown already done: %s' % f)
        return True
    # Do it now
    if not os.chown(f, uid, gid):
        logging.debug('chown ok: %s' % f)
        return True
    else:
        logging.error('chown failed: %s' % f)
        return False


def pre_proc(device):
    """Pre-processes before uploading config file"""
    # Don't check save_running_config() return code, it's not realiable
    save_running_config(device)
    fix_paths(device)


def post_proc(device):
    """Post-processes after successfully uploaded config"""
    # Vendor specific actions
    if device.vendor == 'huawei':
        post_proc_huawei(device)
    # Common actions
    if not os.path.isfile(device.upload_abs_path):
        # FTP server will delete upload failure files
        logging.error('%s upload failed, file frag removed' % device.name)
        return False
    from dm import git
    git.git_commit(device.upload_abs_path)


def post_proc_huawei(device):
    """Post-processes on huawei switch's config, it's clear text config
    file in zip archive. Extract it so I can add it into git repository.
    """
    import zipfile
    p = device.upload_path
    uf = device.upload_abs_path
    nameprefix = device.name_en + '--' + device.ip
    # unzip
    if not os.path.isfile(uf):
        logging.error('%s upload failed, skip unzip' % device.name)
        return False
    zf = zipfile.ZipFile(uf, mode='r')
    logging.debug('%s unzip uploaded file: %s' % (device.name, uf))
    zf.extractall(path=p)
    # Rename zip like this: vrpcfg.zip => ZiTeng-5700-1--10.2.25.2.zip
    newname = nameprefix + '.zip'
    newfp = os.path.join(p, newname)
    logging.debug('%s rename %s/{vrpcfg.zip => %s}' %
                  (device.name, p, newname))
    os.rename(uf, newfp)
    # Determine filename in zip
    possible_name = ['_vrpcfgtmp.cfg', 'vrpcfg.cfg']
    if len(zf.namelist()) == 1 and zf.namelist()[0] in possible_name:
        txtconfname = zf.namelist()[0]
    else:
        logging.error('%s ERROR: unknown file in zip, post-process aborted')
        return False
    # Rename like this: {_vrpcfgtmp.cfg, vrpcfg.cfg} =>
    # ZiTeng-5700-1--10.2.25.2.cfg
    newname = nameprefix + '.cfg'
    fp = os.path.join(p, txtconfname)
    newfp = os.path.join(p, newname)
    logging.debug('%s rename %s/{%s => %s}' %
                  (device.name, p, txtconfname, newname))
    os.rename(fp, newfp)

    fix_perm(newfp)
    # Update attribute with new name
    logging.debug('%s update device.upload_abs_path = %s' %
                  (device.name, newfp))
    device.upload_abs_path = newfp


def save_running_config(device):
    """Save running config into device, in case it's not saved by hand"""
    from dm import check_attr
    checks = ['save_config_need_confirm', 'save_config_command',
              'save_config_ok_hint', 'save_config_fail_hint', 'session']
    if not check_attr(device, checks):
        return False
    if device.session is False:
        return False
    if device.save_config_need_confirm == 0:
        return save_without_confirm(device)
    elif device.save_config_need_confirm == 1:
        return save_with_confirm(device)


def save_without_confirm(device):
    """These devices don't need confirm while save running config."""
    s = device.session
    s.sendline(device.save_config_command)
    logging.warn('%s exec command: %s' %
                 (device.name, device.save_config_command))
    i = s.expect([device.save_config_ok_hint,
                  device.save_config_fail_hint, pexpect.TIMEOUT,
                  device.escalated_prompt])
    header = device.name + ' save running config to device'
    if i == 0:
        logging.warn('%s ok' % header)
        return True
    elif i == 1 or i == 2:
        logging.error('%s failed' % header)
        return False
    elif i == 3:
        # If save state is unknown, assume it's OK
        logging.error('%s finished with unknown state' % header)
        return True


def save_with_confirm(device):
    """These devices need manual confirm while save running config."""
    s = device.session
    s.sendline(device.save_config_command)
    logging.warn('%s exec command: %s' % (device.name,
                                          device.save_config_command))
    i = 0
    while i == 0 or i == 1:
        i = s.expect(['Y/N', 'press the enter key',
                      device.save_config_ok_hint,
                      device.save_config_fail_hint])
        if i == 0:
            s.sendline('y')
        elif i == 1:
            s.sendline('\r')
        elif i == 2:
            logging.warn('%s saved running config to device successfully' %
                         device.name)
            return True
        elif i == 3:
            logging.error('%s save running config to device failed' %
                          device.name)
            return False


def show_config(device):
    """Backup config from network devices, whose 'show runconfig' like
    feature is reliable.
    """
    # TODO: implement and test me
    device.session.sendline(device.show_config_command)
    logging.info('%s exec show_config_command: %s' %
                 (device.name, device.show_config_command))
    # determine prompt
    if hasattr(device, 'show_config_need_escalating') and \
       device.show_config_need_escalating == 1:
        prompt = device.escalated_prompt
    else:
        prompt = device.prompt
    logging.info('%s start to roll config' % device.name)
    i = 0
    while i == 0:
        i = device.session.expect([device.show_config_paging_prompt, prompt])
        if i == 0:
            show_terminal(device.session)
            device.session.sendline(device.show_config_next_page)
        if i == 1:
            break
    return device.session


def upload_greenway_onu_profile(device):
    """Upload onu-profile on Greenway OLT"""
    if not hasattr(device, 'upload_config_command2'):
        return False
    s = device.session
    cmd = device.upload_config_command2
    s.sendline(cmd)
    logging.error('%s exec command: %s' % (device.name, cmd))
    i = s.expect([device.upload_config_ok_hint, device.upload_config_fail_hint,
                  device.upload_config_command_wrong, pexpect.TIMEOUT])
    if i == 0:
        logging.warn('%s ftp: upload onu-profile ok' % device.name)
    elif i == 1:
        logging.error('%s ftp: upload onu-profile failed' % device.name)
    elif i == 2:
        logging.error('%s upload onu-profile command is wrong' % device.name)
    elif i == 3:
        logging.error('%s ERROR: upload onu-profile timeout' % device.name)


def upload_h3c_config(device):
    """Upload H3C config interactively, using [ftp] view"""
    return upload_huawei_config(device)


def upload_huawei_config(device):
    """Upload Huawei config interactively, using [ftp] view"""
    from etc.lazycat_conf import FTP_SERVER_ADDR, FTP_USER, FTP_PASSWORD
    s = device.session
    if s is False:
        return False
    # Open ftp
    s.sendline('ftp')
    if s.expect(['[ftp]']) == 0:
        s.sendline('open %s' % FTP_SERVER_ADDR)
        logging.debug('%s sent in ftp view: open %s' % (device.name,
                                                        device.ip))
    # Input ftp username
    i = s.expect([r'User.*:', 'Error: Failed to connect', pexpect.TIMEOUT])
    if i == 0:
        s.sendline(FTP_USER)
        logging.debug('%s sent in ftp view: ftp username' % device.name)
    elif i in [1, 2]:
        logging.error('%s connect ftp server failed' % device.name)
        return False
    # Input ftp password
    if s.expect(['assword:']) == 0:
        s.sendline(FTP_PASSWORD)
        logging.debug('%s sent in ftp view: ftp password' % device.name)
    # Check if ftp password is right
    i = s.expect(['230 Login successful', 'Error:'])
    if i == 0:
        pass
    elif i == 1:
        logging.error('%s ftp login failed' % device.name)
        return False
    # Disable passive mode on H3C switch
    if device.vendor.startswith('h3c'):
        s.sendline('undo passive')
        logging.debug('%s sent in ftp view: undo passive' % device.name)
        if s.expect(['[ftp]']) == 0:
            pass
        else:
            logging.warn('%s ftp: disable passive mode failed' % device.name)
    # ftp is ready, upload now
    s.sendline(device.upload_config_command)
    logging.debug('%s sent in ftp view: %s' % (device.name,
                                               device.upload_config_command))
    i = s.expect(['150 Ok', r'(FTP: Error|FTP: Can\'t connect|Error: Failed)',
                  'Error: Wrong parameter found'])
    if i == 0:
        logging.warn('%s ftp: upload config ok' % device.name)
        r = True
    elif i == 1:
        logging.error('%s ftp: upload config failed' % device.name)
        logging.error('%s error messages: %s' % (device.name,
                                                 str(s.before + s.after)))
        r = False
    elif i == 2:
        logging.error('%s ftp: upload command is wrong' % device.name)
        r = False
    # Quit
    s.sendline('quit')
    logging.debug('%s sent in ftp view: quit' % device.name)
    return r


def upload_using_upload_cmd(device):
    """Upload device config using builtin 'upload ...' command, which
    supports ftp."""
    # upload now via pexpect session
    s = device.session
    cmd = device.upload_config_command
    logging.error('%s exec command: %s' % (device.name, cmd))
    s.sendline(cmd)
    i = s.expect([device.upload_config_ok_hint, device.upload_config_fail_hint,
                 device.upload_config_command_wrong, pexpect.TIMEOUT])
    if i == 0:
        logging.warn('%s ftp: upload config ok' % device.name)
    elif i == 1:
        logging.error('%s ftp: upload config failed' % device.name)
    elif i == 2:
        logging.error('%s upload command is wrong' % device.name)
    elif i == 3:
        logging.error('%s ERROR: upload timeout' % device.name)
    # Also backup onu-profile on greenway OLT
    if device.vendor == 'greenway':
        upload_greenway_onu_profile(device)


def upload_via_ftp(device):
    """Start a FTP server and upload startup.cfg on device"""
    if not hasattr(device, 'upload_config_command'):
        return False
    pre_proc(device)
    if device.vendor == 'huawei':
        upload_huawei_config(device)
    elif device.vendor == 'h3c':
        upload_h3c_config(device)
    else:
        upload_using_upload_cmd(device)
    post_proc(device)
