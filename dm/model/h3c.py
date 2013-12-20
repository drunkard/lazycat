"""
Default settings for H3C switch
"""
proto = 'telnet'
port = 23
vendor = 'h3c'

username_hint = 'Username:'
username = 'admin'
password_hint = 'Password:'
password = ''   # set in etc/dev.py
password_wrong = 'Wrong password'
prompt = r'<.*>'


# priviledge escalating things
escalating_needed = [
    'show_config_command',
    'upload_config_command'
]
escalating_going = 0        # we are escalating privilege
escalating_command = 'super'
escalating_hint = 'Password:'
escalating_password = ''    # set in etc/dev.py
escalating_password_wrong = 'Password:'
# configuration session is exclusive.
escalating_conflict_hint = 'locked'
escalating_conflicted = 0
escalated_prompt = r'User privilege level is 3.*>'
escalated = 0   # set to 1 while escalated successfully


# exit commands
exit_escalated = 'quit'
exit_os = 'quit'


# save config
save_config_need_confirm = 1
save_config_command = 'save'
save_config_ok_hint = 'saved to device successfully'
save_config_fail_hint = 'to device fail'   # not confirmed


# show config things
show_config_need_escalating = 0
show_config_command = 'display current-configuration'
show_config_paging_prompt = '---- More ----'
show_config_abort = 'q'     # pexpect child.sendcontrol('c')
show_config_next_page = ' '


# upload config file related things
upload_config_need_escalating = 1
upload_filename_on_dev = 'startup.cfg'
upload_filename = 'RC_NAME_RC--RC_IP_RC--startup.cfg'
upload_config_command = 'put startup.cfg RC_NAME_RC--RC_IP_RC--startup.cfg'
"""
upload_config_command = '''ftp
open RC_FTP_SERVER_ADDR_RC
RC_FTP_USER_RC
RC_FTP_PASSWORD_RC
put startup.cfg RC_NAME_RC--RC_IP_RC--startup.cfg
bye
'''
"""
upload_config_command_wrong = 'Unknown command'
upload_config_ok_hint = ''
upload_config_fail_hint = ''
ftp_view_prompt = '[ftp]'
