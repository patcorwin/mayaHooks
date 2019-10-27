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
import logging
import os
import tempfile
import zipfile

from maya import cmds


from . import installCore
from mayaHooksCore import uninstall


exampleSetupCode = '''
try:
    import sys
    sys.path.append('{installDir}')
    import mayaHooks.dagMenuProc
    mayaHooks.dagMenuProc.overrideDagMenuProc()
    
    import pdil.tool.animDagMenu
    mayaHooks.dagMenuProc.registerMenu(pdil.tool.animDagMenu.animationSwitchMenu)
    
except:
    import traceback
    print( traceback.format_exc() )
    print( "See above error text, something went wrong in mayaHook's userSetup.py" )
'''


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


try:
    basestring  # noqa
except Exception:
    basestring = str


def run(zippath):
    
    mayaVersion = installCore.ask(zippath)
    
    if not mayaVersion:
        return
    
    packageKey = installZip(zippath, mayaVersion)
    
    settings = installCore.loadSettings()

    installCore.update(settings, packageKey, mayaVersion,
        source=os.path.normpath(zippath).replace('\\', '/'),
        source_data={'modified_time': os.path.getmtime(zippath)},
    )
    cmds.confirmDialog(m='Install complete!')



def installZip(zipdata, mayaVersion):
    '''
    `zipData` is either a path to a zip file, or a file like objects, just like `ZipFile()`.
    
    Overwrites any existing install.  Use `run()` to prompt the user.
    '''
    
    info, packagekey, userSetupCode, packageContainerFolder = installCore.extractZipBasicInfo(zipdata)

    uninstall(packagekey, mayaVersion)

    settings = installCore.loadSettings()
    
    log.debug('PACKAGE KEY {}'.format(packagekey))
    
    newBuildTime = info.get('utc_build_time', installCore.UTC_BUILD_DEFAULT)

    scriptFolder = installCore.defaultScriptsPath(mayaVersion=mayaVersion)
    
    # Finally, extract to the `mayaVersion`
    if isinstance(zipdata, basestring):
        tempZipPath = zipdata
    else:
        tempZipPath = tempfile.mktemp(suffix='.zip')
        zipdata.seek(0) # Assumed to have a BytesIO object
        with open(tempZipPath, 'wb') as fid:
            fid.write(zipdata.read())
    
    installCore.unzip(tempZipPath, scriptFolder, packagekey, subdir=packageContainerFolder)
    
    # Edit usersetup.py as needed.
    if userSetupCode:
        log.debug('Editing userSetup.py')
        installCore.userSetupEdit(mayaVersion, packagekey, userSetupCode)
    else:
        log.debug('No userSetup_code.py exists top level, no edits to userSetup.py.')

    # write settings of mayaVersion, version etc
    #log.debug('Updating registry: {} {} {}'.format(  ))
    installCore.update(settings, packagekey, mayaVersion,
        utc_install_time=str(datetime.datetime.utcnow()),
        utc_build_time=newBuildTime,
    )
    
    return packagekey

