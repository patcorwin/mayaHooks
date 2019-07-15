'''

Users will need to run this code from within maya to install

```
import sys, maya.cmds
files = maya.cmds.fileDialog2(fileMode=1, cap='Locate the zip file to install tools')
if files:
    sys.path.insert(0, files[0])
    import mayaHooks.installFromZip
    mayaHooks.installFromZip.run(files[0])
```

The zip file _MUST_ contain:

* mayaHooks
* info.json with {"version": <an integer>}

Optionally it can contain __userSetup__.py, which will be read in and added to
an existing userSetup.py, or created if needed.


info.json can have anything else you might want to store, but an integer
version for unambiguous comparison is required.


Todo:

* Manage if mayaHooks needs to be updated or not.


'''
from __future__ import absolute_import, division, print_function

import datetime
import json
import logging
import os
import zipfile

from maya import cmds


exampleSetupCode = '''
try:
    import sys
    sys.path.append('{}')
    import mayaHooks.dagMenuProc
    mayaHooks.dagMenuProc.overrideDagMenuProc()
    
    import pdil.tool.animDagMenu
    mayaHooks.dagMenuProc.registerMenu(pdil.tool.animDagMenu.animationSwitchMenu)
    
except:
    import traceback
    print( traceback.format_exc() )
    print( "See above error text, something went wrong in mayaHook\'s userSetup.py" )
'''


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def run(zipPath):
    log.debug('Beginning install...')
    path, filename = os.path.split(zipPath)
    
    settingsFile = os.path.expanduser("~") + '/MayaHookSettings/' + filename + '.settings'
    
    installDir = None
    
    if os.path.exists(settingsFile):
        log.debug('Settings Exist: ' + settingsFile)
        
        # &&& Need to account for corrupted settings
        with open(settingsFile, 'r') as fid:
            existingSettings = json.load(fid)
        
        # ??? check version, confirm upgrade or downgrade
        
        installDir = existingSettings.get('location', None)
        if installDir:
            res = cmds.confirmDialog(m='Upgrade installation at "{}"}'.format(installDir), b=['Yes', 'No'])
            if res == 'No':
                installDir = None
    
    if not installDir:
        folders = cmds.fileDialog2(fileMode=3, cap='Where do you want to install the tools?')
        if not folders:
            cmds.warning('Installation aborted')
        else:
            installDir = folders[0]
        
    log.debug( 'Extracting "{}" into "{}"'.format(zipPath, installDir) )
    with zipfile.ZipFile(zipPath, 'r') as fid:
        fid.extractall(installDir)
        fid.close()
    
    setupCodeFile = installDir + '/__userSetup__.py'
    setupCode = ''
    if os.path.exists(setupCodeFile):
        with open(setupCodeFile, 'r') as fid:
            setupCode = fid.read()
    
    
    # &&& Might want to verify the correct version has been imported
    import mayaHooks.userSetup_setup
    
    if setupCode:
        mayaHooks.userSetup_setup.ManageUserSetup( setupCode.format(installDir), filename )
    
    versionFile = installDir + '/info.json'
    version = -1
    if os.path.isfile(versionFile):
        with open(versionFile) as fid:
            info = json.load(fid)
        
        version = info.get('version', -1)
    
    settings = {
        'version':      version,
        'install_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M.%S.%f'),
        'location':     installDir,
    }
    
    path, filename = os.path.split(settingsFile)
    if not os.path.exists(path):
        os.makedirs(path)
    
    with open( settingsFile, 'w' ) as fid:
        json.dump(settings, fid, indent=4)

    '''
    
    make <name>.upacked.settings in os.path.expanduser("~")
    
    {
        'version': #, build this from p4
        'date':  yyyy.mm.dd.hr.min.sec
        'location': ''
    }
    
    '''