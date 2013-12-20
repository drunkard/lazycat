import os


def git_commit(f):
    """Commit config if there's any changes"""
    if not os.path.isfile(f):
        return False
    # TODO: implement me
    pass
