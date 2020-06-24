from __future__ import absolute_import, division, print_function

import logging
import os
import sys

from maya import cmds

from . import installCore

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
    

def run(folder, mayaVersionHint=None, silent=False):
    '''
    `folder` is a python package.
    NOTE: mayaVersionHint is for parity with others but unimplemented, 'common' is forced.
    '''
    
    assert os.path.exists(folder + '/__init__.py'), 'This is not python package, no __init__.py found'
    
    packageKey = os.path.basename(folder)

    settings = installCore.loadSettings()

    mayaVersion = 'common'  # Just use 'common' since it's complicated to test.

    installCore.update(settings, packageKey, mayaVersion,
        source=folder,
    )

    # Immediately make it available instead of waiting for a reboot
    container = os.path.dirname( folder )
    sys.path.append(container)

    # &&& Need to also run userSetup if appropriate.

    if not silent:
        cmds.confirmDialog(m='Install complete!')
