#!/usr/bin/env python
""" This script cleans the COMPU directories.
"""

# standard library
import shutil
import glob
import os

# module-wide variables
SAVE_FILES = ['modules', 'clean', 'create', 'model.robupy.ini', 'acropolis.pbs']

''' Auxiliary functions
'''
def cleanup():

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
    cleanup()
