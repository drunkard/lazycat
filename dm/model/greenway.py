"""
Default settings for Greenway
"""
proto = 'telnet'
port = 23
vendor = 'greenway'

username_hint = 'Login:'
username = 'admin'
password_hint = 'Password:'
password = ''   # set in etc/dev.py
password_wrong = 'Invalid user name or password'
prompt = '>'

# priviledge escalating things
escalating_needed = [
    'show_config_command',
    'upload_config_command'
]
escalating_going = 0        # we are escalating privilege
escalating_command = 'enable'
escalating_hint = 'Password:'
escalating_password = ''    # set in etc/dev.py
escalating_password_wrong = 'Invalid password'
# configuration session is exclusive.
escalating_conflict_hint = 'configuration is locked by other user'
escalating_conflicted = 0
escalated_prompt = '#'
escalated = 0   # set to 1 while escalated successfully

# exit commands
exit_escalated = 'exit'
exit_os = 'quit'

# show config things
show_config_need_escalating = 1
show_config_command = 'show running-config'
show_config_paging_prompt = '--Press any key to continue'
show_config_abort = ''    # pexpect child.sendcontrol('c')
show_config_next_page = 'n'

# upload config file related things
upload_config_need_escalating = 1
# Args: FTP_SERVER_ADDR, FTP_USER, FTP_PASSWORD, device.ip, device.name
upload_filename = 'RC_IP_RC--RC_NAME_RC.cfg'
upload_config_command = 'upload ftp config RC_FTP_SERVER_ADDR_RC \
        RC_FTP_USER_RC RC_FTP_PASSWORD_RC ' + upload_filename
upload_config_command_wrong = 'Unknown command'
upload_config_ok_hint = 'Upload file ...ok'
upload_config_fail_hint = 'Upload file ...failed'
