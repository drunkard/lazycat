#!/usr/bin/env python3


def pexpect_session(session):
    """show on going message of pexpect session.
    Usage:
    from dm.debug import pexpect_session; pexpect_session(session)
    """
    o = session.before + session.after
    for line in o.decode().splitlines():
        print(line)
