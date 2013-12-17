"""Methods used to save devices' config.
"""
import logging
import pexpect
import os
from dm import show_terminal
from dm import ftp


# logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)


def git_commit(device):
    """Commit config if there's any changes"""
    # TODO: implement me
    pass


def pre_proc(device):
    """Pre-processes before uploading config file"""
    from etc.lazycat_conf import DEVCONF_BACKUP_PATH, FTP_USER
    fp = os.path.join(DEVCONF_BACKUP_PATH, device.vendor)
    if not os.path.isdir(fp):
        logging.debug("%s mkdir: %s" % (device.name, fp))
        os.makedirs(fp)
        # Fix perms
        from pwd import getpwnam
        uid = getpwnam(FTP_USER).pw_uid
        gid = getpwnam(FTP_USER).pw_gid
        os.chown(fp, uid, gid)
    device.upload_cur_fpath = os.path.join(DEVCONF_BACKUP_PATH,
                                           device.upload_filename)
    device.upload_dst_fpath = os.path.join(fp, device.upload_filename)
    device.upload_path = fp


def post_proc(device):
    """Post-processes after successfully uploaded config"""
    from shutil import move
    # ftp server will delete upload failure files
    if not os.path.isfile(device.upload_cur_fpath):
        logging.error('%s upload failed, file frag removed' % device.name)
        return False
    if move(device.upload_cur_fpath, device.upload_dst_fpath):
        git_commit(device.upload_dst_fpath)
    del device.upload_cur_fpath
    del device.upload_dst_fpath
    del device.upload_path


def show_config(device, session):
    """Backup config from network devices, whose 'show runconfig' like
    feature is reliable.
    """
    # TODO: implement and test me
    session.sendline(device.show_config_command)
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
        i = session.expect([device.show_config_paging_prompt, prompt])
        if i == 0:
            show_terminal(session)
            session.sendline(device.show_config_next_page)
        if i == 1:
            break
    return session


def upload_via_ftp(device, session):
    """Start a FTP server and upload startup.cfg on device"""
    if not hasattr(device, 'upload_config_command'):
        return False

    srv = ftp.server()
    pre_proc(device)
    if not srv.start():
        return False

    # upload now via pexpect session
    upload_command = device.upload_config_command
    logging.error('%s uploading config: %s' % (device.name, upload_command))
    session.sendline(upload_command)
    i = session.expect([device.upload_config_ok_hint,
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

    # post things
    post_proc(device)
    srv.stop()
