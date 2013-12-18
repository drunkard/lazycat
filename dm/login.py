#!/usr/bin/env python3
import logging
import pexpect
import dm


def input_username(device):
    """Detect if needs username, input if need, or just return"""
    s = device.session
    # Check attributes will use
    checks = ['username', 'username_hint', 'password_hint']
    if not dm.check_attr(device, checks):
        return False
    # Check prompt
    i = s.expect([device.username_hint, device.password_hint,
                  pexpect.TIMEOUT, 'No route to host'])
    logging.debug('%s expecting: username_hint=%s or password_hint=%s' %
                  (device.name, device.username_hint, device.password_hint))
    if i == 0:
        pass
    elif i == 1:
        logging.info('%s dont need username' % device.name)
        return s
    elif i == 2 or i == 3:
        logging.error('%s input_username: abort on errors, ip: %s' %
                      (device.name, device.ip))
        return False
    # Input username
    s.sendline(device.username)
    i = s.expect([device.password_hint])
    logging.debug('%s expecting: password_hint=%s' %
                  (device.name, device.password_hint))
    if i == 0:
        return s
    logging.warning("%s input_username failed" % device.name)
    return False


def input_password(device):
    """Generic password inputing function

    Set "device.escalated = 1" if got escalated_prompt after input.
    """
    s = device.session
    # Check attributes will use
    checks = ['password', 'password_wrong', 'prompt', 'escalated_prompt']
    if not dm.check_attr(device, checks):
        return False

    s.sendline(device.password)
    logging.debug('%s sent password: %s' % (device.name, device.password))
    i = s.expect([device.escalated_prompt, device.prompt,
                  device.password_wrong])
    logging.debug('%s expecting: prompt=%s password_wrong=%s' %
                  (device.name, device.prompt, device.password_wrong))
    if i == 0:
        logging.debug('%s got escalated_prompt, dont need escalating anymore' %
                      device.name)
        device.escalated = 1
    elif i == 1:
        pass
    elif i == 2:
        logging.error('%s ERROR: wrong password' % device.name)
        return False
    return s


def input_escalate_command(device):
    """Input escalating command
    Set input_escalate_command_done attribute on device after finished, and it
    should be removed after successfully escalated.
    """
    s = device.session
    # Check if already escalated, some device dont have to escalating.
    if hasattr(device, 'escalated') and device.escalated == 1:
        return s
    # Check attributes will use
    checks = ['escalating_command', 'escalating_hint', 'escalated_prompt',
              'escalating_conflict_hint']
    if not dm.check_attr(device, checks):
        return False

    s.sendline(device.escalating_command)
    logging.warning('%s exec escalate command: %s' %
                    (device.name, device.escalating_command))
    if device.escalating_conflict_hint == '':
        i = s.expect([device.escalating_hint, device.escalated_prompt])
    else:
        i = s.expect([device.escalating_hint, device.escalated_prompt,
                      device.escalating_conflict_hint])
    if i == 0:
        pass
    elif i == 1:
        logging.info('%s no password for escalating command' % device.name)
    elif i == 2:
        logging.error("%s escalate conflicted, try again later" % device.name)
        device.escalating_conflicted = 1
        return False
    else:
        logging.error("%s unknown hint after input escalating_command"
                      % device.name)
    device.input_escalate_command_done = 1
    return s


def input_escalate_password(device):
    """Type in escalating password
    Set "device.escalated = 1" after successfully escalated privilege.
    """
    s = device.session
    if hasattr(device, 'input_escalate_command_done') and \
       device.input_escalate_command_done == 1:
        pass
    else:
        return s
    # Check if already escalated
    if hasattr(device, 'escalated') and device.escalated == 1:
        return s
    # Check attributes will use
    checks = ['escalating_command', 'escalating_hint',
              'escalating_conflict_hint',
              'escalating_password', 'escalating_password_wrong']
    if not dm.check_attr(device, checks):
        return False

    logging.debug('%s input escalate password: pwd=%s prompt=%s pwd_wrong=%s' %
                  (device.name, device.escalating_password,
                   device.escalated_prompt, device.escalating_password_wrong))
    s.sendline(device.escalating_password)
    logging.debug('%s sent password: %s' %
                  (device.name, device.escalating_password))
    # Some device wont check if conflicted
    if device.escalating_conflict_hint == '':
        i = s.expect([device.escalated_prompt,
                      device.escalating_password_wrong])
    else:
        i = s.expect([device.escalated_prompt, device.escalating_conflict_hint,
                      device.escalating_password_wrong])
    if i == 0:
        logging.debug('%s input_escalate_password ok, returning' % device.name)
        device.escalated = 1
        del device.input_escalate_command_done
        return s
    elif i == 1:
        logging.error('%s ERROR: escalating conflicted' % device.name)
    elif i == 2:
        logging.error('%s ERROR: wrong password' % device.name)
    return False


def ssh(device):
    """login using ssh"""
    return False


def telnet(device):
    """login using telnet
    Returns a pexpect session.
    """
    cmd = ' '.join([device.proto, device.ip, str(device.port)])
    logging.warn('%s spawn session: %s' % (device.name, cmd))
    s = pexpect.spawn(cmd)
    device.session = s
    # Try to detect what got, want username or password ?
    s = input_username(device)
    if s is False:
        return False
    # Input password
    s = input_password(device)
    if s is False:
        return False
    # Escalate privilege
    s = input_escalate_command(device)
    if s is False:
        return False
    # Input password
    s = input_escalate_password(device)
    if s is False:
        return False
    logging.debug('%s telnet ok, returning live session' % device.name)
    return s


def connect(device):
    """Generic login frontend interface, auto determine protocol"""
    if device.proto is 'telnet':
        return telnet(device)
    if device.proto is 'ssh':
        return ssh(device)
