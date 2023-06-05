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
import subprocess
import sys
import tempfile

from maya import cmds

from mayaHooksCore import uninstall

from . import core
from .. import _startup


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


def run(zippath, mayaVersionHint=None, silent=False):
    zippath = os.path.expandvars( os.path.expanduser(zippath) )
    # Strip out quotes if they exist
    if zippath.startswith('"'):
        zippath = zippath[1:]
    if zippath.endswith('"'):
        zippath = zippath[:-1]
    
    mayaVersion = core.ask(zippath, mayaVersionHint)
    
    if not mayaVersion:
        return
    
    packageKey = installZip(zippath, mayaVersion)
    
    settings = core.loadSettings()

    core.update(settings, packageKey, mayaVersion,
        source=os.path.normpath(zippath).replace('\\', '/'),
        source_data={'modified_time': os.path.getmtime(zippath)},
        source_type='zip',
    )
    
    packagePath = core.defaultScriptsPath(mayaVersion) + '/' + packageKey
    _startup.addIconPaths( settings[mayaVersion][packageKey], packagePath)
    
    if not silent:
        cmds.confirmDialog(m='Install complete!')


def installPymel(package):
    
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    mayapy = os.path.dirname(sys.executable) + '/mayapy.exe'
    os.path.exists(mayapy)
    
    asdf = subprocess.run([mayapy, '-m', 'pip', 'install', package], capture_output=True, startupinfo=startupinfo)

    if asdf.returncode != 1:
        return False
        
    return True


def installZip(zipdata, mayaVersion):
    '''
    `zipData` is either a path to a zip file, or a file like objects, just like `ZipFile()`.
    
    Overwrites any existing install.  Use `run()` to prompt the user.
    '''
    
    info, packagekey, userSetupCode, packageContainerFolder = core.extractZipBasicInfo(zipdata)

    uninstall(packagekey, mayaVersion)

    settings = core.loadSettings()
    
    pymelSuccess = True
    if 'pip' in settings:
        for package in settings['pip']:
            if package == 'pymel':
                try:
                    from pymel.core import select  # noqa
                    
                except ModuleNotFoundError:
                    
                    if cmds.about(p=True).count( '2022' ):
                        pymelSuccess = installPymel( 'pymel>=1.2.,<1.3.' )
                    elif cmds.about(p=True).count( '2023' ):
                        pymelSuccess = installPymel( 'pymel>=1.3.*,<1.4.*' )
                
    
    log.debug('PACKAGE KEY {}'.format(packagekey))

    scriptFolder = core.defaultScriptsPath(mayaVersion=mayaVersion)
    
    # Finally, extract to the `mayaVersion`
    if isinstance(zipdata, basestring):
        tempZipPath = zipdata
    else:
        tempZipPath = tempfile.mktemp(suffix='.zip')
        zipdata.seek(0)  # Assumed to have a BytesIO object
        with open(tempZipPath, 'wb') as fid:
            fid.write(zipdata.read())
    
    core.unzip(tempZipPath, scriptFolder, packagekey, subdir=packageContainerFolder)
    
    # Edit usersetup.py as needed.
    if userSetupCode:
        log.debug('Editing userSetup.py')
        core.userSetupEdit(mayaVersion, packagekey, userSetupCode)
    else:
        log.debug('No userSetup_code.py exists top level, no edits to userSetup.py.')

    # write settings of mayaVersion, version etc
    #log.debug('Updating registry: {} {} {}'.format(  ))

    # Add the install time and update the registry with the info
    info['utc_install_time'] = str(datetime.datetime.utcnow())

    core.update(settings, packagekey, mayaVersion, **info)
    
    if not pymelSuccess:
        cmds.warning('Unable to install pymel, which is required.  You will need to manually install pymel for this package to work.')
        cmds.confirmDialog(m='Unable to install pymel, which is required.\n\nYou will need to manually install pymel for this package to work.')
    
    return packagekey
