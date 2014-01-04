# -*- coding: utf-8 -*-
import readline
import os


HistoryLength = 1000
HistoryPath = os.path.expanduser('~/' + '.lazycat_history')


def load():
    """Load history on login, and should be saved on exit."""
    try:
        readline.read_history_file(HistoryPath)
    except IOError:
        pass


def save():
    """Register a hook to save command history automatically at exit."""
    try:
        import atexit
        readline.set_history_length(HistoryLength)
        atexit.register(readline.write_history_file, HistoryPath)
    except Exception:
        print("Error on register history file, won't save command history.")
