import logging
import os


class server:
    """Custom FTP server used to serve users."""
    def __init__(self):
        """Read config arguments"""
        from etc import lazycat_conf
        from lib import random_char
        self.user = random_char(3)
        self.password = random_char(3)
        self.perm = lazycat_conf.FTP_USER_PERM
        # self.path = lazycat_conf.DEVCONF_BACKUP_PATH + device.vendor
        self.path = lazycat_conf.DEVCONF_BACKUP_PATH
        self.address = lazycat_conf.FTP_SERVER_ADDR
        self.port = lazycat_conf.FTP_PORT
        self.use_custom_server = lazycat_conf.FTP_RANDOMIZE
        self.ftp_server_name = lazycat_conf.FTP_SERVER_NAME

    def custom_server(self, start=1):
        # TODO: finish me
        from pyftpdlib.authorizers import DummyAuthorizer
        from pyftpdlib.handlers import FTPHandler
        from pyftpdlib.servers import FTPServer
        # Generate random username and password for ftp session
        logging.debug('generating arguments')
        if not os.path.isdir(self.path):
            logging.info('%s create directory: %s' %
                         ('device.name', self.path))
            os.makedirs(self.path)
        # Add ftp user
        authorizer = DummyAuthorizer()
        logging.debug('generated args: user=%s password=%s path=%s perm=%s' %
                      (self.user, self.password, self.path, self.password))
        authorizer.add_user(self.user, self.password, self.path,
                            perm=self.perm)
        handler = FTPHandler
        handler.authorizer = authorizer
        # Instantiate FTP server class and listen
        logging.debug('%s ftp server listen on: %s %s' %
                      ('device.name', self.address, self.port))
        addr = (self.address, self.port)
        server = FTPServer(addr, handler)
        # Set a limit for connections
        server.max_cons = 32
        server.max_cons_per_ip = 5
        # Start ftp server
        logging.debug('starting disposable ftp server')
        server.serve_forever(timeout=600, blocking=False)

    def ready_server(self, start=1):
        """start/stop a ready outer FTP server"""
        if start == 0:
            # Server has been stopped
            if os.system('pgrep %s >/dev/null' % self.ftp_server_name) == 256:
                return True
            if os.system('/etc/init.d/%s --nodeps stop &>/dev/null' %
                         self.ftp_server_name):
                logging.error('stop vsftpd failed')
                return False
            else:
                logging.debug('stop vsftpd ok')
                return True
        if start == 1:
            # Server has been started
            if os.system('pgrep %s >/dev/null' % self.ftp_server_name) == 0:
                return True
            if os.system('/etc/init.d/%s --nodeps start &>/dev/null' %
                         self.ftp_server_name):
                logging.error('start vsftpd failed, abort')
                return False
            else:
                logging.debug('start vsftpd ok')
                return True

    def start(self):
        if self.use_custom_server == 1:
            return self.custom_server(start=1)
        elif self.use_custom_server == 0:
            return self.ready_server(start=1)

    def stop(self):
        if self.use_custom_server == 1:
            return self.custom_server(start=0)
        elif self.use_custom_server == 0:
            return self.ready_server(start=0)
