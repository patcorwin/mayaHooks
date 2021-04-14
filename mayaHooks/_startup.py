from itertools import chain

try: # python 3
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

import json
import logging
import os
import sys

from .install import core
from . import _util

log = logging.getLogger(__name__)
log.setLevel( logging.DEBUG )


def startup():
    '''
    mayaHooks runs this in userSetup for a single point to dynimcally load resources.

    It loads icon paths and dynamic loading of dev packages to mimic regular installation.
    '''

    settings = core.loadSettings()

    def packages():
        ''' Returns list of [
            ((packageKeyA, infoDict), 'common'),
            ((packageKeyB, infoDict), 'common'),
            ...
            ((packageKeyY, infoDict), '2019'),
            ((packageKeyZ, infoDict), '2019'),
        ]
        '''
        return chain(
            zip_longest(settings.get('common', {}).items(), [], fillvalue='common'),
            zip_longest(settings.get(core.HERE, {}).items(), [], fillvalue=core.HERE)
        )
    
    # Load extra info from packages as needed
    for (packageKey, info), mayaVersion in packages():
        folder = info.get('source', '')
        # Dev installs are just a stub pointing to a folder, so inspection is needed
        # to load the icon paths, as well as any additional userSetup.py
        if os.path.isdir( folder ):
            setupDevFolder(packageKey, folder)
        # Regular installs just need their icon paths appended
        else:
            log.debug( '-- {} :Normal install: -- {}'.format(packageKey, folder) )
            packagePath = core.defaultScriptsPath(mayaVersion) + '/' + packageKey
            addIconPaths(info, packagePath)


    scriptFolder = core.defaultScriptsPath(mayaVersion=core.ALL_VERSION)
    # Run dev usersetup at the end since everything else is now loaded
    for (packageKey, info), mayaVersion in packages():
        folder = info.get('source', '')
        if os.path.isdir( folder ):
            runUserSetup(packageKey, folder)
        else:
            userSetup = scriptFolder + '/' + packageKey + '/userSetup.txt'
            if os.path.exists(userSetup):
                log.debug( '---- user setup: {}'.format(userSetup) )
                _util.runFile(userSetup)


def runUserSetup(packageKey, folder):
    packageRoot = os.path.dirname( folder )
    code = packageRoot + '/userSetup_code.py'

    if os.path.exists(code):
        log.debug( '---- user setup: {}'.format(code) )
        # Dynamically load the user setups since they all have the same name
        _util.runFile(code)
    else:
        log.debug( '---- no user setup' )


def setupDevFolder(packageKey, folder):
    log.debug( '-- {} :Dev install: -- {}'.format(packageKey, folder) )

    if not os.path.exists(folder):
        log.error( '---- Cannot load {} because folder does not exist: {}'.format(packageKey, folder) )
        return

    packageRoot = os.path.dirname( folder )
    
    log.debug( '---- path {}'.format(packageRoot) )
    sys.path.insert(0, packageRoot )

    # Load up the real info.json since the mayaHooks entry is just a stub to the folder
    info = {}
    infoPath = packageRoot + '/info.json'

    if os.path.exists(infoPath):
        try:
            with open(infoPath, 'r') as fid:
                info = json.load(fid)
        except Exception:
            Warning('Error loading json', infoPath)
            return
    
    addIconPaths(info, folder)
    

def addIconPaths(info, packageFolder):
    # Add any icon paths
    paths = info.get('icon_paths', [])
    if paths:
        log.debug( '---- icon paths ' + ' '.join(paths) )
        os.environ['XBMLANGPATH'] += ';' + ';'.join( [_util.concretePath(packageFolder + '/' + p) for p in paths] )
    else:
        log.debug( '---- no icon paths' )
