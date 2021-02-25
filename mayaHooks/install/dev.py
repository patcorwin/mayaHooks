from __future__ import absolute_import, division, print_function

import logging
import os
import sys

from maya import cmds

import mayaHooksCore

from . import core
from .. import _startup

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
    

def run(folder, mayaVersionHint=None, silent=False):
    '''
    `folder` is a python package.
    NOTE: mayaVersionHint is for parity with others but unimplemented, 'common' is forced.
    '''
    folder = os.path.expandvars( os.path.expanduser(folder) )
    assert os.path.exists(folder + '/__init__.py'), 'This is not python package, no __init__.py found'
    
    packageKey = os.path.basename(folder)
    mayaVersion = 'common'  # Just use 'common' since it's complicated to test.
    
    mayaHooksCore.uninstall(packageKey, mayaVersion)

    settings = core.loadSettings()

    core.update(settings, packageKey, mayaVersion,
        source=folder,
        source_type='dev',
    )

    # Immediately make it available instead of waiting for a reboot
    container = os.path.dirname( folder )
    sys.path.append(container)

    # Run the _startup so userSetup and icon paths are applied
    _startup.setupDevFolder(packageKey, folder)

    if not silent:
        cmds.confirmDialog(m='Install complete!')
