#!/usr/bin/env python
""" This script cleans the directories.
"""

# standard library
import shutil
import glob
import os

''' Auxiliary functions
'''


def cleanup(all_=True):
    """ Cleanup during development.
    """
    SAVE_FILES = ['full', 'approximate', 'create', 'model.robupy.ini',
                  'data_one', 'data_two', 'data_three', 'clean',
                  'acropolis.pbs', 'modules', 'clean', 'create', 'clean.py',
                  'create.py']

    for name in glob.glob('*'):
        if name in SAVE_FILES:
            pass
        else:
            remove(name)


def remove(names):
    """ Remove files or directories.
    """
    if not isinstance(names, list):
        names = [names]

    for name in names:
        try:
            os.remove(name)
        except IsADirectoryError:
            shutil.rmtree(name)

''' Main
'''
if __name__ =='__main__':


    root_dir = os.getcwd()

    for subdir, _, _ in os.walk('.'):

        os.chdir(subdir)
        cleanup()
        os.chdir(root_dir)
