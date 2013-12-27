import logging
import pygit2
import os
from os import makedirs, path
from etc import lazycat_conf as conf


datapath = conf.DEVCONF_BACKUP_PATH
repopath = path.join(datapath, '../git')
repopath = path.abspath(repopath)
repo = pygit2.Repository(path.join(repopath, '.git'))
author = pygit2.Signature(conf.MYNAME, conf.EMAIL)
commiter = author
message = "backup system auto committed"


def check_repo_status():
    """Check git repository status, is there's any not commited files"""
    if repo.status() == {}:
        return True
    else:
        logging.warn('WARN: git repository is not clean: %s' % repopath)
        return False


def commit_one_file(f):
    """Do real commit job"""
    from os import path
    logging.debug('git commit: start on %s' % f)
    # Determine message
    vendor = path.basename(path.dirname(f))
    host_name = path.basename(f).split('--')[0]
    newmessage = ': '.join([message, vendor, host_name])
    # Start commit
    f = pre_commit(f)
    relf = path.relpath(f, start=repopath)
    if relf not in repo.status().keys():
        logging.debug('git commit: nothing changed on %s' % f)
        return True
    index = repo.index
    index.read()
    index.add(relf)
    # Determine tree
    treeid = index.write_tree()
    # Determine parents
    if repo.is_empty or repo.head_is_unborn:
        logging.warn('git commit: this empty repository')
        parents = []
    else:
        # latest_commit = repo[repo.head.target]
        latest_commit = repo.revparse_single('HEAD')
        parents = [latest_commit.hex]
    logging.debug('git commit: commiting %s' % f)
    repo.create_commit(
        # 'refs/heads/master',
        'HEAD',
        author, commiter,
        newmessage,
        treeid,
        parents
    )
    index.write()
    post_commit()


def commit(f):
    """Commit config if there's any changes"""
    try:
        # Determine whether track config contents with git
        from etc.lazycat_conf import GIT_TRACK
        if GIT_TRACK is not True:
            logging.debug('track with git is disabled in etc.lazycat_conf')
            return True
    except Exception as e:
        logging.error('%s caught exception while git commit' % e)
        return False

    if not path.isfile(f):
        return False
    # Do commit now
    commit_one_file(f)


def copy_to_repo(f):
    """Copy raw device config file to git working directory.
    Because those config files contains invalid characters to git.
    """
    from shutil import copyfile
    relpath = f.replace(datapath, '')
    newf = path.join(repopath, relpath)
    dir_in_repo = path.dirname(newf)
    if not path.isdir(dir_in_repo):
        makedirs(dir_in_repo)
    logging.debug('copy file: %s -> %s' % (f, newf))
    # copyfile is unreliable, it may cause zero sized file, so do more times.
    # To avoid deadlock, copy 10 times at most.
    cnt = 0
    while True:
        copyfile(f, newf)
        if path.getsize(newf) > 0 or cnt > 10:
            break
        cnt += 1
    return newf


def fix_file_end(f):
    """Two functions:
        Truncate blank lines in end of file;
        Add \n if to end of file there's no one.
    """
    import string
    valid_char = string.printable.strip(string.whitespace)
    oldfile = open(f, mode='r+')
    oldfile.seek(0, os.SEEK_END)
    pos = oldfile.tell()
    orig_pos = pos
    # Lookup '\n' from END to START, while encounter non-\n char, truncate all
    # characters behind this last \n, so truncate should start at (non-\n char
    # + 2).
    while pos > 0:
        pos -= 1
        oldfile.seek(pos, os.SEEK_SET)
        if oldfile.read(1) in valid_char:
            break
    new_pos = pos + 2
    # If there's nothing need to truncate, the last pos will be (size of f -
    # 1), after +2, it's bigger than original file, so use the original pos.
    # Or, truncate() will fill those bytes with \000
    if pos > 0 and new_pos > orig_pos:
        pos = orig_pos
    elif pos > 0:
        pos = new_pos
    oldfile.seek(pos, os.SEEK_SET)
    oldfile.truncate()

    # Add \n in end of file, if there's no one.
    oldfile.seek(0, os.SEEK_END)
    pos = oldfile.tell() - 1
    oldfile.seek(pos, os.SEEK_SET)
    if oldfile.read(1) != '\n':
        logging.debug('add \\n to end of file')
        oldfile.write('\n')
    oldfile.close()


def fix_text(f):
    """Strip non-printable characters (space/TAB in end, Ctrl-@) in config
    file"""
    import re
    from shutil import move
    logging.debug('fix text: %s' % f)
    # This table is generated from str.maketrans('\r': '')
    table = {
        13: '',     # \r => ''
        0: '\n',    # Ctrl-@ => \n
    }
    tmpf = '/dev/shm/devconf-tmp-file'
    newtext = open(tmpf, mode='w')
    re_compiled = re.compile(' +$')
    with open(f, mode='r') as text:
        for line in text:
            line = line.translate(table)
            line = re_compiled.sub('', line)
            newtext.write(line)
    newtext.close()
    move(tmpf, f)


def git_remote_exists(name):
    if len(repo.remotes) == 0:
        return False
    for r in repo.remotes:
        if r.name == name:
            return True
    return False


def post_commit():
    """Post processes after commit"""
    pass


def pre_commit(f):
    """Pre-processes on file to be commited to git repository. Like strip
    these characters (Ctrl-M/Ctrl-@) in config file."""
    f = copy_to_repo(f)
    # Do more process on specific vendor
    dir_in_repo = path.dirname(f)
    logging.debug('dir_in_repo = %s' % dir_in_repo)
    if dir_in_repo.endswith('huawei') and f.endswith('.zip'):
        f = reshape_huawei(f)
    elif dir_in_repo.endswith('raisecom') or \
            dir_in_repo.endswith('raisecom_sy'):
        f = reshape_raisecom(f)
    elif dir_in_repo.endswith('zte'):
        f = reshape_zte(f)
    fix_text(f)
    fix_file_end(f)
    return f


def pre_push():
    """Enviroment prepares before doing git-push"""
    from etc import lazycat_conf as conf
    if hasattr(conf, 'GIT_SERVER_NAME') and hasattr(conf, 'GIT_SERVER_URL'):
        name = conf.GIT_SERVER_NAME
        url = conf.GIT_SERVER_URL
    if git_remote_exists(name):
        # remotes already configed
        pass
    else:
        # add remote from config, and set it as default
        repo.create_remote(name, url)
    return True


def push2server():
    """Push working git repository to remote repo on server.

    Should be invoked at end of backup, or too frequently new connections to
    ssh server maybe rejected.
    """
    try:
        from os import system
        from etc.lazycat_conf import GIT_PUSH_OUT, GIT_SERVER_NAME
        # If push is disabled in conf, just return True
        if GIT_PUSH_OUT is not True:
            return True
    except ImportError as e:
        logging.error('ERROR: can not read config' % e)
        return False
    pre_push()
    # TODO: implement using pygit2 while it's avaiable
    if system('cd %s && git push -f %s master &>/dev/null' %
              (repopath, GIT_SERVER_NAME)) == 0:
        logging.warn('git push succeeded')
    else:
        logging.error('git push failed')
    """This transport isn't implemented in pygit2 yet.
    # Push to every remote
    for r in repo.remotes:
        pygit2.Remote.push(r, 'refs/heads/master')
    """


def reshape_raisecom(f):
    """Strip "DB FILE BEGIN" part in Raisecom config file"""
    logging.debug('reshape_raisecom: %s' % f)
    import re
    oldfile = open(f, mode='r+b')
    re_compiled = re.compile(b'^DB FILE BEGIN')
    pos = 0
    size = oldfile.seek(0, 2)
    oldfile.seek(0)
    while True:
        line = oldfile.readline()
        if re_compiled.match(line):
            # Break at first match
            break
        elif oldfile.tell() >= size:
            # We're at end of file, nothing found
            return f
    pos = oldfile.tell() - 14   # 14 is size of "DB FILE BEGIN"
    oldfile.seek(pos)
    oldfile.truncate()
    oldfile.close()
    return f


def reshape_huawei(f):
    """Huawei config is zipped, you got to unzip it before track contents."""
    from os import remove, rename
    from re import sub
    from zipfile import ZipFile
    p = path.dirname(f)
    # unzip
    logging.debug('unzip file: %s' % f)
    zf = ZipFile(f, mode='r')
    zf.extractall(path=p)
    # Determine filename in zip
    possible_name = ['_vrpcfgtmp.cfg', 'vrpcfg.cfg']
    if len(zf.namelist()) == 1 and zf.namelist()[0] in possible_name:
        cfgfile = zf.namelist()[0]
    else:
        logging.error('ERROR: unknown file in zip, reshape_huawei aborted')
        return False
    # Rename: {_vrpcfgtmp.cfg, vrpcfg.cfg} => ZiTeng-5700-1--10.2.25.2.cfg
    newf = sub('zip$', 'cfg', f)
    logging.debug('rename %s/{%s => %s}' % (p, cfgfile, path.basename(newf)))
    rename(path.join(p, cfgfile), newf)
    remove(f)
    return newf


def reshape_zte(f):
    """Encoding convert, from GB18030 to UTF-8"""
    import codecs
    from shutil import move
    BLOCKSIZE = 65536   # 64KB
    tmpf = '/dev/shm/reshape_zte-tmp'
    logging.debug('convert encoding for ZTE config: %s' % f)
    with codecs.open(f, mode='rb', encoding='gb18030') as oldfile:
        with codecs.open(tmpf, 'w', 'utf-8') as newf:
            while True:
                contents = oldfile.read(BLOCKSIZE)
                if not contents:
                    break
                newf.write(contents)
    move(tmpf, f)
    return f
