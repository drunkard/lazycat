# -*- coding: utf-8 -*-
import logging
import os
import readline
try:
    from lib import color, say
    from lib import get_local_ip, maxlen, syscmd_stdout
except ImportError as e:
    raise e
try:
    from etc.mydns import servers, views
    cache_server_list = [k for k, v in servers.items()
                         if v.get('class').startswith('cache')]
    iterate_server_list = [k for k, v in servers.items()
                           if v.get('class') == 'iterator']
    nonpub_server_list = [k for k, v in servers.items()
                          if v.get('class') != 'public']
    public_server_list = [k for k, v in servers.items()
                          if v.get('class') == 'public']
except ImportError:
    # This warn message will be shown only once.
    msg = """
    WARNING: can not retrieve config in etc/mydns.py, use builtin DNS
    servers instead."""
    print(color.yellow_bold(' '.join(msg.split())))
    # Define builtin servers
    builtin_servers = {
        'dns8': {'ip': '211.161.192.67',
                 'class': 'iterator',
                 'loc': 'China Shanghai'},
        'idcns1': {'ip': '211.161.192.68',
                   'class': 'cache',
                   'loc': 'China Shanghai'},
        'bas-1-primary': {'ip': '10.2.1.26',
                          'class': 'cache-cluster',
                          'loc': 'China'},
        'bas-1-secondary': {'ip': '10.2.1.27',
                            'class': 'cache-cluster',
                            'loc': 'China'},
        'level3-a': {'ip': '4.2.2.1',
                     'class': 'public',
                     'loc': 'United States',
                     'owner': 'level3'},
        'google-a': {'ip': '8.8.8.8',
                     'class': 'public',
                     'loc': 'United States',
                     'owner': 'google'},
        'ru-SkyDNS': {'ip': '195.46.39.39',
                      'class': 'public',
                      'loc': 'Россия Екатеринбург',
                      'owner': 'SkyDNS'},
    }
    servers = builtin_servers
    cache_server_list = [k for k, v in servers.items()
                         if v.get('class').startswith('cache')]
    iterate_server_list = [k for k, v in servers.items()
                           if v.get('class') == 'iterator']
    nonpub_server_list = [k for k, v in servers.items()
                          if v.get('class') != 'public']
    public_server_list = [k for k, v in servers.items()
                          if v.get('class') == 'public']
    # Define builtin views
    views = {
        'default': {'desc': 'Default view, this is builtin config',
                    'match-ip': ['0.0.0.0/0'],
                    # Source IP used to query on this view
                    'source-ip': ['192.168.0.2'],
                    # rndc config, source IP for rndc to execute rndc commands
                    'rndc-ip': ['192.168.0.2'],
                    # 'rndc-port': 953,  # read from rndc-conf
                    'rndc-conf': '/chroot/etc/rndc.conf',
                    },
    }

dig2 = 'dig +time=1 +tries=1 +nocmd +multiline +noall +answer +stats '
rndc2 = '/usr/sbin/rndc '
rndc_conf = '/chroot/etc/rndc.conf'
init_ShuTong = {  # 诸葛亮身边的书童？
    'server_list': [],
    'server': '',
    'server_ip': '',
    'name_list': [],
    'name': '',
    'view_list': [],  # views to flush, servers.get('dns1').get('view-list')
    'view': 'no view',
    'source-ip': '',
    'arpa-opt': '',  # Set to '-x' if doing arpa lookup
    'cmd': dig2,
    'rndc_conf': rndc_conf,
    # 'rdata' changes while processing, 'rdata_final' holds final results
    'rdata': [],
    'rdata_final': [],
    'rdata_fail_reason': '',
    'time': 'Not counted',
}
# rdata_final array format
SERVER = 0
VIEW = 1
TTL = 2
RDATATYPE = 3
RDATA = 4
TIME = 5
# The number of usable IP addresses must be more than views installed.
view_supported = True

myip = [i.split('/')[0] for i in get_local_ip() if i.split('/')[0]]
if myip == []:
    msg = """WARNING: Failed to get IP addresses on this host, "view" feature
        feature will be disabled."""
    print(color.yellow_bold(' '.join(msg.split())))
    view_supported = False

if len(views.keys()) > len(myip):
    msg = """Got IP addresses are lesser than view number, "view"
        feature will be disabled."""
    print(color.yellow_bold(' '.join(msg.split())))
    view_supported = False


class complete(list):
    def arpa():
        """Same as complete.resolve()"""
        return complete.resolve()

    def list():
        """Return a list of servers' name which starts with user's input,
        in this situation, user want to list servers with specific name."""
        origcmd = readline.get_line_buffer()
        begin = readline.get_begidx()
        end = readline.get_endidx()
        being_completed = origcmd[begin:end]
        return [x for x in servers.keys() if x.startswith(being_completed)]

    def resolve():
        """Returns a dict of file name, used for auto completion.
        Usage:
            complete.resolve()
        """
        logging.debug('dns complete: resolve: working')
        spec_name = ['all', 'public']
        spec_name += [x for x in servers.keys()]
        return spec_name


class do_dns(str):
    """While do resolving, initialize a dict that contains all informations
    will use, and fill the result into the dict while finished.

    The rdata dict is init_ShuTong.
    """
    def __init__(self, rawcmd):
        from cli import dns_l2
        self.rawcmd = rawcmd
        self.rawcmd_list = self.rawcmd.split()
        # self.doing_server is used to control result printing
        self.doing_server = 'EMPTY'
        self.view_supported = view_supported
        try:
            l2cmd = self.rawcmd_list[1].replace('-', '_')
        except IndexError:
            say.available_cmds(dns_l2)
            return
        # Start execution
        try:
            func = getattr(self, 'do_' + l2cmd)
            logging.info('do_dns: routed to do_' + l2cmd)
            func()
        except AttributeError:
            logging.info('do_dns: function not found: do_' + l2cmd)
            say.no_cmd(rawcmd)
            prefix_matches = [c for c in dns_l2.keys()
                              if c and c.startswith(l2cmd.replace('_', '-'))]
            say.available_cmds(dns_l2, justshow=prefix_matches)
            return

    def array_init(self, il):
        ol = []
        if not il:
            return ol
        for i in il:
            if i:
                ol.append(i.split())
        return ol

    def update_resolve_query_time(self, ShuTong):
        rdata = ShuTong.get('rdata')
        for i in rdata:
            try:
                if i[1] == 'Query' and i[2] == 'time:':
                    ShuTong.update({'time': ' '.join(i[3:])})
                    break
            except IndexError:
                pass

    def check_result(self, ShuTong):
        """Check output of dig, identify these results:
            timeout
            refused
            NXDOMAIN
        """
        response = ShuTong.get('rdata')
        msg_timeout = 'connection timed out'
        if response.find(msg_timeout) >= 0:
            ShuTong.update({'rdata': ''})
            ShuTong.update({'rdata_fail_reason': msg_timeout})
        else:
            ShuTong.update({'rdata': response.split('\n')})
            ShuTong.update({'rdata_fail_reason': ''})

    def do_arpa(self):
        """Roll the resolve progress in this order:
            roll names to resolve
            roll name on servers
            roll name on view on one server
            real resolve
        """
        ShuTong = init_ShuTong.copy()
        ShuTong = self.read_resolve_args(ShuTong)
        # TODO: check if got valid IP
        name_list = ShuTong.get('name_list')
        if name_list == []:
            self.print_help_resolve(cmd='dns arpa', name='8.8.8.8')
            return
        ShuTong.update({'arpa-opt': ' -x '})
        for ip in sorted(name_list):
            ShuTong = self.init_ShuTong(ShuTong)
            ShuTong.update({'name': ip})
            self.roll_resolve_by_server(ShuTong)
            self.print_result(ShuTong)
        del ShuTong

    def do_flush(self):
        """Roll the resolve progress in this order:
            roll names to flush
            roll name on servers
            roll name on view on one server
            real flush
        """
        ShuTong = init_ShuTong.copy()
        name_list = self.read_arg3()
        server_list = [k for k, v in servers.items()
                       if v.get('class') == 'iterator']
        ShuTong.update({'name_list': name_list})
        ShuTong.update({'server_list': server_list})
        if name_list == []:
            print('Need name to process with, example:')
            print('  %s www.google.com' % (color.cyan('dns flush')))
            return
        for n in name_list:
            ShuTong.update({'name': n})
            self.roll_flush_by_server(ShuTong)
        del ShuTong

    def do_list(self):
        """This is a router to route sub-commands to right commands."""
        from cli import dns_list_l3
        try:
            l3cmd = self.rawcmd_list[2].replace('-', '_')
        except IndexError:
            say.available_cmds(dns_list_l3)
            return
        # Start execution
        try:
            func = getattr(self, 'do_list_' + l3cmd)
            logging.info('do_dns: routed to do_list_' + l3cmd)
            func()
        except AttributeError:
            # List possible single server
            logging.info('do_dns: function not found: do_' + l3cmd)
            self.list_filter_by_name(showName=l3cmd)
            return

    def do_list_all(self):
        self.list_filter_by_class()

    def do_list_cache(self):
        self.list_filter_by_class(showClass='cache')

    def do_list_cache_cluster(self):
        self.list_filter_by_class(showClass='cache-cluster')

    def do_list_iterator(self):
        self.list_filter_by_class(showClass='iterator')

    def do_list_public(self):
        self.list_filter_by_class(showClass='public')

    def do_list_view(self):
        for k, v in sorted(views.items()):
            print('View name: %s (%s)' % (color.green(k), v.get('desc')))
            if not v:
                print('    None')
                continue
            for i in v.get('match-ip'):
                print('   ', i)

    def do_one_key_diag(self):
        """All in one diag
        Final killer of DNS problem.
        """
        # FIXME: implement me
        say.not_implemented()

    def do_resolve(self):
        """Roll the resolve progress in this order:
            roll names to resolve
            roll name on servers
            roll name on view on one server
            real resolve
        """
        ShuTong = init_ShuTong.copy()
        ShuTong = self.read_resolve_args(ShuTong)
        name_list = ShuTong.get('name_list')
        if name_list == []:
            self.print_help_resolve(cmd='dns resolve', name='www.google.com')
            return
        ShuTong.update({'arpa-opt': ''})
        for n in name_list:
            ShuTong = self.init_ShuTong(ShuTong)
            ShuTong.update({'name': n})
            self.roll_resolve_by_server(ShuTong)
            self.print_result(ShuTong)
        del ShuTong

    def do_trace(self):
        """Do: dig +trace ..."""
        # FIXME: implement me
        say.not_implemented()

    def init_ShuTong(self, ST):
        """All cumulated keys need to be initialized before reuse."""
        l = ['rdata', 'rdata_final', 'rdata_fail_reason']
        for i in l:
            ST.update({i: []})
        return ST

    def list_filter_by_class(self, showClass=''):
        """General purpose filter while print various classes of DNS
        servers."""
        if showClass:
            toshow = {x: y for x, y in servers.items()
                      if y.get('class').startswith(showClass)}
        else:
            toshow = servers
        if not toshow:
            print('Nothing matched to: %s' % showClass)
            return
        name_max = maxlen([x for x in toshow.keys()] + ['Name'])
        ip_max = maxlen([i.get('ip')
                         for i in toshow.values()] + ['IP'])
        class_max = maxlen([i.get('class')
                            for i in toshow.values()] + ['Class'])
        loc_max = maxlen([i.get('loc')
                          for i in toshow.values()
                          if i.get('loc') is not None] + ['Location'])
        fmt = '%s  %s  %s  %s'
        # Print header
        print(fmt % ('Name'.ljust(name_max), 'IP'.ljust(ip_max),
                     'Class'.ljust(class_max), 'Location'))
        print(fmt % ('-' * name_max, '-' * ip_max,
                     '-' * class_max, '-' * loc_max))
        for k, v in sorted(toshow.items()):
            if k == 'Name':  # skip header hint
                continue
            classname = v.get('class')
            name = k
            ip = v.get('ip')
            loc = v.get('loc')
            if loc is None:
                # loc = color.red(str(loc))
                loc = ''
            print(fmt % (name.ljust(name_max), ip.ljust(ip_max),
                         classname.ljust(class_max), loc))

    def list_filter_by_name(self, showName=''):
        """General purpose filter while print various classes of DNS
        servers."""
        if showName:
            toshow = {x: y for x, y in servers.items()
                      if x.startswith(showName)}
        else:
            toshow = servers
        if not toshow:
            print('Nothing matched to: %s' % showName)
            return
        name_max = maxlen([x for x in toshow.keys()] + ['Name'])
        ip_max = maxlen([i.get('ip')
                         for i in toshow.values()] + ['IP'])
        class_max = maxlen([i.get('class')
                            for i in toshow.values()] + ['Class'])
        loc_max = maxlen([i.get('loc')
                          for i in toshow.values()
                          if i.get('loc') is not None] + ['Location'])
        fmt = '%s  %s  %s  %s'
        fmt_hdr = color.white(fmt)
        # Print header
        print(fmt_hdr % ('Name'.ljust(name_max), 'IP'.ljust(ip_max),
                         'Class'.ljust(class_max), 'Location'))
        print(fmt % ('-' * name_max, '-' * ip_max,
                     '-' * class_max, '-' * loc_max))
        for k, v in sorted(toshow.items()):
            if k == 'Name':  # skip header hint
                continue
            classname = v.get('class')
            name = k
            ip = v.get('ip')
            loc = v.get('loc')
            if loc is None:
                # loc = color.red(str(loc))
                loc = ''
            print(fmt % (name.ljust(name_max), ip.ljust(ip_max),
                         classname.ljust(class_max), loc))

    def print_help_resolve(self, cmd='', name=''):
        help_info = """Need name to process with, examples:

        Resolve on our non-cache DNS:
            CMD NAME [...]
        Resolve on all our non-cache and cache DNS:
            CMD <GREEN>all<OFF> NAME
        Resolve on all famous public DNS:
            CMD <GREEN>public<OFF> NAME
        Resolve on specific DNS:
            CMD <GREEN>dns1<OFF> NAME
        """
        help_info = help_info.replace('        ', '')
        help_info = help_info.replace('CMD', color.cyan(cmd))
        help_info = help_info.replace('NAME', name)
        help_info = help_info.replace('<GREEN>', color.GREEN)
        help_info = help_info.replace('<OFF>', color.OFF)
        print(help_info)

    def print_result(self, ShuTong):
        print('\nName: %s' % (color.green(ShuTong.get('name'))))
        r = ShuTong.get('rdata_final')
        ShuTong.update({'rdata_final': []})
        # Get max values for alignment
        # server_max = maxlen(ShuTong.get('server_list') + ['SERVER'])
        view_max = maxlen([x for x in views.keys() if x] + ['VIEW'])
        ttl_max = maxlen([x[TTL] for x in r if x] + ['TTL'])
        rdatatype_max = maxlen([x[RDATATYPE] for x in r if x] + ['TYPE'])
        rdata_max = maxlen([x[RDATA] for x in r if x] + ['RESULT'])
        time_max = maxlen([x[TIME] for x in r if x] + ['TIME'])
        fmt = '%s   %s   %s   %s   %s'
        fmt_hdr = color.white(fmt)
        d = view_max + ttl_max + rdatatype_max + rdata_max + time_max + 12
        print(fmt_hdr % ('VIEW'.ljust(view_max),
                         'TTL'.ljust(ttl_max),
                         'TYPE'.ljust(rdatatype_max),
                         'RESULT'.ljust(rdata_max),
                         'TIME'.ljust(time_max)))
        # Print rdata
        last_server = 'firstRun'
        last_view = 'firstRun'
        for i in r:
            pserver = i[SERVER]
            pview = i[VIEW]
            if pserver and pserver != last_server:
                pserver_rbar = ' /' + '='.ljust((d - 6 - len(pserver)), '=')
                print(color.white_bold('==/ %s%s') %
                      (color.green_bold(pserver),
                       color.white_bold(pserver_rbar)))
                last_server = pserver
            else:
                if pview and not last_view:
                    print('-' * d)
                else:
                    last_view = pview
            if i[TTL] == 'FAIL_MARK':
                msg = color.red_bold(i[RDATA])
                print('%s   %s' % (pview.ljust(view_max), msg.ljust(ttl_max)))
                continue
            prdatatype = i[RDATATYPE]
            if prdatatype == 'CNAME':
                prdatatype = color.magenta(prdatatype)
            print(fmt % (pview.ljust(view_max),
                         i[TTL].ljust(ttl_max),
                         prdatatype.ljust(rdatatype_max),
                         i[RDATA].ljust(rdata_max),
                         i[TIME].ljust(time_max)))

    def read_arg3(self):
        try:
            return [self.rawcmd_list[2]]
        except IndexError:
            return []

    def read_arg3_to_end(self):
        try:
            return self.rawcmd_list[2:]
        except IndexError:
            return []

    def read_arg4(self):
        try:
            return [self.rawcmd_list[3]]
        except IndexError:
            return []

    def read_arg4_to_end(self):
        try:
            return self.rawcmd_list[3:]
        except IndexError:
            return []

    def read_resolve_args(self, holder):
        """DNS servers should be defined starts with @..., so multiple
        servers or multiple sets are supported, all others are treated
        as names."""
        # TODO __doc__
        server_list = []
        name_list = []
        # Determine server_list, match and reassign a value
        server_list = self.read_arg3()
        if server_list == ['all']:
            server_list = nonpub_server_list
        elif server_list == ['public']:
            self.view_supported = False
            server_list = public_server_list
        elif server_list == [] or server_list[0] in servers.keys():
            pass
        else:
            server_list = []
        logging.info('read_resolve_args: server_list is: %s' %
                     ' '.join(server_list))
        # Determine name_list
        if server_list == []:
            # No arg as server_list, or it's domain name
            name_list = self.read_arg3_to_end()
            server_list = iterate_server_list
        else:
            name_list = self.read_arg4_to_end()
        logging.info('read_resolve_args: name_list is: %s' %
                     ' '.join(name_list))
        holder.update({'server_list': server_list})
        holder.update({'name_list': name_list})
        return holder

    def roll_flush_by_server(self, ShuTong):
        server_list = ShuTong.get('server_list')
        if server_list == []:
            say.internal_error()
            return
        for s in sorted(server_list):
            sc = servers.get(s)
            server_ip = sc.get('ip')
            ShuTong.update({'server': s})
            ShuTong.update({'server_ip': server_ip})
            ShuTong.update({'view_list': sc.get('view_list')})
            self.roll_flush_by_view(ShuTong)

    def roll_flush_by_view(self, ShuTong):
        """If view is supported, roll flushing by view;
        if not, call roll_flush_final() directly."""
        view_list = ShuTong.get('view_list')
        # Determine if view is supported
        if not self.view_supported or view_list is None or view_list == []:
            self.view_supported = False
            ShuTong.update({'view': ''})
            self.roll_flush_final(ShuTong)
        else:
            self.view_supported = True
            for vn in sorted(view_list):
                ShuTong.update({'view': vn})
                self.roll_flush_final(ShuTong)

    def roll_flush_final(self, ShuTong):
        # Print header
        server = ShuTong.get('server')
        if self.doing_server != server:
            print('Flushing %s on %s => %s' %
                  (ShuTong.get('name'), color.green(ShuTong.get('server')),
                   color.green(ShuTong.get('server_ip'))))
        # Determine rndc config
        rc = servers.get(server).get('rndc-conf')
        if rc is not None:
            ShuTong.update({'rndc_conf': rc})
            # else: default not changed
        rndc_conf = ShuTong.get('rndc_conf')
        if not os.path.isfile(rndc_conf):
            say.nofile(rndc_conf, prefix="rndc config")
        self.update_flush_cmd(ShuTong)
        cmd = ShuTong.get('cmd')
        if self.view_supported:
            self.update_flush_view(ShuTong)
            fmt = '  from view ' + ShuTong.get('view') + ' %s'
            cmd += ' ' + ShuTong.get('view')
        else:
            fmt = '  no view, %s'
        # Execute command
        cmd = ' '.join(cmd.split())  # reshape
        logging.info('exec system command: %s' % cmd)
        if os.system(cmd) == 0:
            print(fmt % (say.ok))
        else:
            print(fmt % (say.fail))

    def roll_resolve_by_server(self, ShuTong):
        """If view is supported, call roll_resolve_by_view() to roll on,
        if not, call roll_resolve_final() directly."""
        logging.debug('enter roll_resolve_by_server')
        server_list = ShuTong.get('server_list')
        if server_list == []:
            say.internal_error()
            return
        for s in sorted(server_list):
            ShuTong.update({'server': s})
            ShuTong.update({'server_ip': servers.get(s).get('ip')})
            if s in nonpub_server_list and self.view_supported:
                # view is supported
                self.view_supported = True
                self.roll_resolve_by_view(ShuTong)
            else:
                # view is not supported
                self.view_supported = False
                ShuTong.update({'source-ip': ''})
                ShuTong.update({'view': 'no view'})
                self.roll_resolve_final(ShuTong)

    def roll_resolve_by_view(self, ShuTong):
        """Next chain to roll_resolve_by_view()"""
        logging.debug('enter roll_resolve_by_view')
        if isinstance(views, dict) and views:
            pass
        else:
            logging.error('ERROR: view is not defined or is wrongly defined.')
            return
        for vn, vv in sorted(views.items()):
            ShuTong.update({'view': vn})
            if self.view_supported:
                src_ip = [ip for ip in myip if ip in vv.get('source-ip')]
                if len(src_ip) > 0:
                    pickone = src_ip[0]
                else:
                    pickone = ''
                ShuTong.update({'source-ip': pickone})
            else:
                ShuTong.update({'source-ip': myip[0]})
            self.roll_resolve_final(ShuTong)

    def roll_resolve_final(self, ShuTong):
        # Resolve started
        self.update_resolve_cmd(ShuTong)
        cmd = ShuTong.get('cmd')
        try:
            logging.info('exec: %s' % cmd)
            ShuTong.update({'rdata': syscmd_stdout(cmd)})
            self.check_result(ShuTong)
            if ShuTong.get('rdata_fail_reason'):
                array = []
            else:
                array = self.array_init(ShuTong.get('rdata'))
        except (KeyboardInterrupt, EOFError, SystemExit):
            # User interrupted via Ctrl-C
            array = []
        ShuTong.update({'rdata': array})
        self.update_resolve_query_time(ShuTong)
        self.update_rdata(ShuTong)
        self.update_rdata_final(ShuTong)

    def update_rdata(self, ShuTong):
        if ShuTong.get('rdata_fail_reason'):
            logging.debug('update_rdata: fill with rdata_fail_reason')
            newa = [[ShuTong.get('server'), ShuTong.get('view'),
                    'FAIL_MARK', '', ShuTong.get('rdata_fail_reason'), '']]
            ShuTong.update({'rdata': newa})
            return
        logging.debug('update_rdata: fill with rdata')
        a = ShuTong.get('rdata')
        view = ShuTong.get('view')
        if not a or not view:
            return
        newa = []
        done = False
        for i in a:
            if i and i[0] == ';;':  # ignore comment lines from dig output
                continue
            i.pop(2)  # remove 'class', IN
            if done:
                i[0] = ''  # add view name, just for first line
                i.insert(0, '')  # add server name
                i.append('')  # add time count, just for first line
            else:
                i[0] = view
                i.insert(0, ShuTong.get('server'))
                i.append(ShuTong.get('time'))
                done = True
            newa.append(i)
        # TODO fill what if resolve failed ?
        ShuTong.update({'rdata': newa})

    def update_rdata_final(self, ShuTong):
        logging.debug('enter update_rdata_final')
        newrdata = ShuTong.get('rdata_final')
        for i in ShuTong.get('rdata'):
            newrdata.append(i)
        ShuTong.update({'rdata_final': newrdata})
        ShuTong.update({'rdata': ''})

    def update_resolve_cmd(self, ShuTong):
        cmd = dig2
        server_ip = ShuTong.get('server_ip')
        cmd += ' @' + server_ip.strip()
        src_ip = ShuTong.get('source-ip')
        if src_ip:
            cmd += ' -b ' + src_ip
        cmd += ' ' + ShuTong.get('arpa-opt')
        cmd += ' ' + ShuTong.get('name')
        cmd = ' '.join(cmd.split())  # reshape
        ShuTong.update({'cmd': cmd})

    def update_flush_cmd(self, ShuTong):
        cmd = rndc2
        src_ip = ShuTong.get('source-ip')
        if self.view_supported and src_ip:
            cmd += ' -b ' + src_ip
        cmd += ' -s ' + ShuTong.get('server_ip')
        cmd += ' -c ' + ShuTong.get('rndc_conf')
        cmd += ' flush ' + ShuTong.get('name') + '&>/dev/null'
        ShuTong.update({'cmd': cmd})

    def update_flush_view(self, ShuTong):
        view = ShuTong.get('view')
        view_data = views.get(view)
        if view_data is None:
            ShuTong.update({'source-ip': ''})
            return
        try:
            src_ip = [i for i in myip if i in view_data.get('source-ip')][0]
        except Exception:
            print('Cannot determine source IP, run rndc without "-b" option')
            src_ip = ''
        ShuTong.update({'source-ip': src_ip})
