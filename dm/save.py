"""Methods used to save devices' config.
"""
import logging
import pexpect
import os
from dm import show_terminal


# logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)


def fix_paths(device):
    """Fix ftp server side paths"""
    from etc.lazycat_conf import DEVCONF_BACKUP_PATH, FTP_USER
    fp = os.path.join(DEVCONF_BACKUP_PATH, device.vendor)
    if os.path.isdir(fp):
        pass
    else:
        logging.debug("%s mkdir: %s" % (device.name, fp))
        if not os.makedirs(fp):
            logging.error('%s mkdir failed: %s' % (device.name, fp))
            return False
        # Fix perms
        from pwd import getpwnam
        uid = getpwnam(FTP_USER).pw_uid
        gid = getpwnam(FTP_USER).pw_gid
        if not os.chown(fp, uid, gid):
            logging.error('%s chown failed: %s' % (device.name, fp))
            return False
    device.upload_cur_fpath = os.path.join(DEVCONF_BACKUP_PATH,
                                           device.upload_filename)
    device.upload_dst_fpath = os.path.join(fp, device.upload_filename)
    device.upload_path = fp
    return True


def git_commit(device):
    """Commit config if there's any changes"""
    # TODO: implement me
    pass


def pre_proc(device):
    """Pre-processes before uploading config file"""
    if not save_running_config(device):
        return False
    if not fix_paths(device):
        return False


def post_proc(device):
    """Post-processes after successfully uploaded config"""
    from shutil import move
    # FTP server will delete upload failure files
    if not os.path.isfile(device.upload_cur_fpath):
        logging.error('%s upload failed, file frag removed' % device.name)
        return False
    if move(device.upload_cur_fpath, device.upload_dst_fpath):
        git_commit(device.upload_dst_fpath)
    del device.upload_cur_fpath
    del device.upload_dst_fpath
    del device.upload_path


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
                  device.save_config_fail_hint, pexpect.TIMEOUT])
    if i == 0:
        logging.warn('%s saved running config to device successfully' %
                     device.name)
        return True
    elif i == 1 or i == 2:
        logging.error('%s save running config to device failed' %
                      device.name)
        return False


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


def upload_via_ftp(device):
    """Start a FTP server and upload startup.cfg on device"""
    if not hasattr(device, 'upload_config_command'):
        return False
    pre_proc(device)
    # upload now via pexpect session
    upload_command = device.upload_config_command
    logging.error('%s uploading config: %s' % (device.name, upload_command))
    device.session.sendline(upload_command)
    i = device.session.expect([device.upload_config_ok_hint,
                               device.upload_config_fail_hint,
                               device.upload_config_command_wrong,
                               pexpect.TIMEOUT])
    if i == 0:
        logging.warn('%s ftp: uploaded config successfully' % device.name)
    elif i == 1:
        logging.error('%s ftp: upload config failed' % device.name)
    elif i == 2:
        logging.error('%s upload command is wrong' % device.name)
    elif i == 3:
        logging.error('%s ERROR: upload timeout' % device.name)
    post_proc(device)
