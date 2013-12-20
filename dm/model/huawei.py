"""
Default settings for Huawei
"""
import os


proto = 'telnet'
port = 23
vendor = 'huawei'

username_hint = 'Username:'
username = 'admin'
password_hint = 'Password:'
password = ''   # set in etc/dev.py
password_wrong = r'(Error: Failed|rejected)'
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
escalating_password_wrong = 'Access Denied'
# configuration session is exclusive.
escalating_conflict_hint = 'locked'
escalating_conflicted = 0
escalated_prompt = '>'
escalated = 0   # set to 1 while escalated successfully


# exit commands
exit_escalated = 'quit'
exit_os = 'quit'


# save config
save_config_need_confirm = 1
save_config_command = 'save'
# For S9306: Succeeded in saving the current configuration to the device.
# For S5700: Save the configuration successfully
# For S5300: The current configuration was saved to the device successfully.
save_config_ok_hint = r'(successfully|Succeeded in saving)'
save_config_fail_hint = 'fail'   # not confirmed


# show config things
show_config_need_escalating = 0
show_config_command = 'display current-configuration'
show_config_paging_prompt = '---- More ----'
show_config_abort = 'q'    # pexpect child.sendcontrol('c')
show_config_next_page = ' '


# upload config file related things
upload_config_need_escalating = 1
upload_config_in_ftp_view = 1
upload_filename_on_dev = 'vrpcfg.zip'
upload_filename = os.path.join(vendor, upload_filename_on_dev)
upload_config_command = 'put vrpcfg.zip ' + upload_filename
# upload_filename = 'RC_NAME_RC--RC_IP_RC--vrpcfg.zip'
# upload_config_command = 'put vrpcfg.zip RC_NAME_RC--RC_IP_RC--vrpcfg.zip'
"""
upload_config_command = '''ftp
open RC_FTP_SERVER_ADDR_RC
RC_FTP_USER_RC
RC_FTP_PASSWORD_RC
put vrpcfg.zip RC_NAME_RC--RC_IP_RC--vrpcfg.zip
bye
'''
"""
upload_config_command_wrong = ''
upload_config_ok_hint = ''
upload_config_fail_hint = ''
ftp_view_prompt = '[ftp]'
