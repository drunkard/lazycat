# from dm.model import bell
# from dm.model import cisco
# from dm.model import dowslake
from dm.model import greenway
from dm.model import h3c
# from dm.model import hillstone
from dm.model import huawei
# from dm.model import juniper
# from dm.model import linux
from dm.model import raisecom
# from dm.model import redback
# from dm.model import routeos
from dm.model import zte

raisecom_sy = raisecom
raisecom_switch = raisecom


all_vendor = [
    "bell",
    "cisco",
    "dowslake",
    "greenway",
    "h3c",
    "hillstone",
    "huawei",
    "juniper",
    "linux",
    "raisecom",
    "redback",
    "routeos",
    "zte",
]


# dm.fix_commands() will replace variables listed list
has_vars = [
    'upload_config_command',
    'upload_config_command2',
    'upload_filename',
]
should_be_replaced = [
    'FTP_SERVER_ADDR',
    'FTP_USER',
    'FTP_PASSWORD',
    'IP',       # device.ip
    'NAME',     # device.name_en
]
