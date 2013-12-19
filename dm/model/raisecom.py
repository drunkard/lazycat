"""
Default settings for Raisecom
"""
proto = 'telnet'
port = 23
vendor = 'raisecom'

username_hint = 'Login:'
username = 'admin'
password_hint = 'Password:'
password = ''   # set in etc/dev.py
password_wrong = r'(Login:|Bad passwords)'
prompt = '>'


# priviledge escalating things
escalating_needed = [
    'show_config_command',
    'upload_config_command'
]
escalating_going = 0        # we are escalating privilege
escalating_command = 'enable'
escalating_hint = 'Password:'
escalating_password = 'EMPTY'   # set in etc/dev.py
escalating_password_wrong = prompt
# configuration session is exclusive.
escalating_conflict_hint = ''
escalating_conflicted = 0
escalated_prompt = '#'
escalated = 0   # set to 1 while escalated successfully


# exit commands
exit_escalated = 'exit'
exit_os = 'quit'


# save config
save_config_need_confirm = 0
save_config_command = 'write'
save_config_ok_hint = 'Save current configuration successfully'
save_config_fail_hint = 'fail'   # not confirmed


# show config things
show_config_need_escalating = 1
show_config_command = 'show running-config'
show_config_paging_prompt = '--More--'
show_config_abort = 'q'
show_config_next_page = ' '


# upload config file related things
upload_config_need_escalating = 1
# Args: FTP_SERVER_ADDR, FTP_USER, FTP_PASSWORD, device.ip, device.name
upload_filename = 'RC_NAME_RC--RC_IP_RC.cfg'
upload_config_command = 'upload startup-config ftp RC_FTP_SERVER_ADDR_RC \
        RC_FTP_USER_RC RC_FTP_PASSWORD_RC ' + upload_filename
upload_config_command_wrong = 'Unknown command'
upload_config_ok_hint = r'(Upload file ...ok|Success)'
upload_config_fail_hint = r'(Upload file ...failed|Failed)'
