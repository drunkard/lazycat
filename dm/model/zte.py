"""
Default settings for ZTE OLT
"""
proto = 'telnet'
port = 23
vendor = 'zte'

username_hint = 'Username:'
username = 'admin'
password_hint = 'Password:'
password = ''   # set in etc/dev.py
password_wrong = 'No username or bad password'
prompt = '#'

# priviledge escalating things
escalating_needed = [
]
escalating_going = 0        # we are escalating privilege
escalating_command = ''
# escalating_hint = 'Password:'
escalating_password = ''    # set in etc/dev.py
escalating_password_wrong = ''
# configuration session is exclusive.
escalating_conflict_hint = ''
escalating_conflicted = 0
escalated_prompt = '#'
escalated = 1   # set to 1 while escalated successfully

# exit commands
exit_escalated = 'exit'
exit_os = 'quit'

# show config things
show_config_need_escalating = 0
show_config_command = 'show running-config'
show_config_paging_prompt = '--More--'
show_config_abort = 'q'    # pexpect child.sendcontrol('c')
show_config_next_page = ' '

# upload config file related things
upload_config_need_escalating = 0
# Args: FTP_SERVER_ADDR, FTP_USER, FTP_PASSWORD, device.ip, device.name
upload_filename = 'RC_IP_RC--RC_NAME_RC.cfg'
upload_config_command = 'copy flash: //cfg/startrun.dat ftp: \
        //RC_FTP_SERVER_ADDR_RC/' + upload_filename + '@RC_FTP_USER_RC:RC_FTP_PASSWORD_RC'
upload_config_command_wrong = 'Incomplete command'
upload_config_ok_hint = 'file copied successfully'
upload_config_fail_hint = r'(Login incorrect|Transmission aborted)'
