'''

info.json contents:

{
    // Generated from str( datetime.utcnow() )
    "utc_build_time": "2019-10-04 17:20:00.327000",
    "maya_version": "2019" # If present, only allows installation to that version
}



mayaHookSettings.json

{
    "common": {
        "pdil": {
            "source": "a url or zip file",
            "source_data": {"modified": str(os.path.getmtime()) } # Only exists if it's a file
            "utc_install_time": "2019-10-04 17:20:00.327000",
            "utc_build_time": "2019-10-04 17:20:00.327000",
        }
    },
    "2019": {
    }

}

'''
from __future__ import absolute_import, division, print_function

import collections
import json
import logging
import os
import re
import shutil
import tempfile
import zipfile

from maya import cmds

from mayaHooksCore import defaultScriptsPath, loadSettings, writeJson, UTC_BUILD_DEFAULT

log = logging.getLogger(__name__)
#log.setLevel(logging.DEBUG)


def findPackageSettings(settings, packageKey, mayaVersion=None):
    '''
    Return the dict of the packageKey or None if it doesn't exist.  Optionally
    specify the mayaVersion instead of searching.
    '''
    if mayaVersion:
        try:
            return settings[mayaVersion][packageKey]
        except Exception:
            return None
    
    for mayaVersion, packages in settings.items():
        if packageKey in packages:
            return packages[packageKey]
    
    return None


def checkInstalledBuiltTime(settings, packageKey, mayaVersion=None):
    '''
    If the package is installed, returns it's utc_build_time, else None.
    '''
    packageSettings = findPackageSettings(settings, packageKey, mayaVersion)
    
    if packageSettings is None:
        return None
    
    return packageSettings.get('utc_build_time', UTC_BUILD_DEFAULT)


def update(settings, packageKey, mayaVersion, **kwargs):
    '''
    test: fake writing a file, then update a setting
    '''
    
    assert mayaVersion is not None
    
    packages = settings.setdefault(mayaVersion, collections.OrderedDict())
    
    package = packages.setdefault(packageKey, collections.OrderedDict())
    
    package.update(kwargs)
    
    writeJson(settings)


def readInfoInZip(zipobj):
    # Takes a `ZipFile`, finding and returning the highest level info.json and it's path in the zip.
    depth = collections.defaultdict(list)
    for fname in zipobj.namelist():
        parts = fname.split('/')
        if parts[-1].lower() == 'info.json':
            depth[ len(parts) ] .append(fname)


    for d, f in sorted(depth.items()):
        if len(f) > 1:
            raise Exception('Too many info.json found, unable to determine top level package')

        info = json.loads( zipobj.read(f[0]) )
        return info, f[0]
    
    raise Exception('No info.json was found, unable to proceed')


def readUserSetupCode(zipobj):
    
    for name in zipobj.namelist():
        if name.lower().endswith('usersetup_code.py'):
            return zipobj.read(name)
    
    return ''


def unzip(zipPath, dest, rootname, subdir=''):
    '''
    Unzips `zipPath` into dest.  Github adds in intermediate directory, which
    is passed into `subdir` so the correct folder gets installed.
    
    Extra files, licence, readme, are put under folder "<dest>/<rootname>-info/".
    '''
    
    packageFolder = dest + '/' + rootname
    infoFolder = packageFolder + '-info'
    
    if os.path.exists(infoFolder):
        shutil.rmtree(infoFolder)
    
    if os.path.exists(packageFolder):
        shutil.rmtree(packageFolder)
    
    
    log.debug('Unzipping {} to {} subdir="{}"'.format(zipPath, dest, subdir) )
    tempDir = tempfile.mkdtemp()
    with zipfile.ZipFile(zipPath, 'r') as fid:
        fid.extractall(tempDir)
        
    if subdir:
        root = os.path.join(tempDir + '/' + subdir)
    else:
        root = tempDir
    
    deleteQueue = []
    

    for f in os.listdir(root):
        path = os.path.join(root, f)
        if os.path.isdir(path):
            newDest = os.path.join(dest, f)
            # &&& Don't think this is needed since the package is deleted at the start
            if os.path.exists(newDest):
                toDelete = newDest + '.delete'
                os.rename(newDest, toDelete)
                deleteQueue.append(toDelete)
            #os.rename(path, newDest)
            shutil.copytree(path, newDest)
        else:
            if not os.path.exists(infoFolder):
                os.makedirs(infoFolder)
            
            shutil.move(path, infoFolder)
            
    for path in deleteQueue:
        os.remove(path)
    
    try:
        shutil.rmtree(tempDir)
    except Exception:
        print('UNABLE TO DELETE', tempDir)
        pass


BEGIN_HOOK = '# BEGIN_MAYA_HOOKS'
END_HOOK = '# END_MAYA_HOOKS'


def userSetupEdit(locversion, key, newText):
    if locversion.startswith('custom:'):
        raise Exception('Custom locations not supported yet')

    elif locversion == 'common':
        path = os.environ['maya_app_dir'] + '/scripts/userSetup.py'
    else:
        path = os.environ['maya_app_dir'] + '/' + locversion + '/scripts/userSetup.py'
    
    log.debug('maya_app_dir:' + os.environ['maya_app_dir'])
    log.debug('locversion ' + locversion)
    log.debug('userSetup.py location: ' + path)

    if not os.path.exists(path):
        userSetupCode = ''
        log.debug('userSetup.py does not exist, creating it')
    else:
        with open(path, 'r') as fid:
            userSetupCode = fid.read()
    
    userSetupCode = modifyUserSetup(userSetupCode, key, newText)
    
    if userSetupCode is None:
        cmds.confirmDialog(m='Unable to find the right place to edit userSetup.py\n\nYou will need to manually edit it, see the script editor')
        print( 'Make sure the `# BEGIN_MAYA_HOOKS...` and `# END_MAYA_HOOKS` blocks match.  Paste in the following code:' )
        print( newText )
        raise Exception('Unable to edit userSetup.py')
    
    with open(path, 'w') as fid:
        fid.write( userSetupCode )
        

def modifyUserSetup(fullpath_or_text, key, newText):
    ''' If successful, returns the text for a modified userSetup.py, or None if unable to edit.
    Args:
        fullpath: String path to userSetup.py, eg "C:/maya/2019/scripts/userSetup.py"
        key: The maya hooks key
        newText: Block of text to insert into the file or `None` to clear the entry, if it exists.
    '''
    if os.path.exists(fullpath_or_text):
        with open(fullpath_or_text, 'r') as fid:
            lines = fid.readlines()
    else:
        lines = fullpath_or_text.splitlines(True)
    
    startRE = re.compile( '^' + BEGIN_HOOK + ' ' + key + r'\s*', flags=re.I )
    endRE = re.compile( '^' + END_HOOK + r'\s*$', flags=re.I )
    
    start = None
    end = None
    
    if newText is not None:
        if isinstance(newText, bytes):
            newText = newText.decode('utf-8')
        
        newLines = (BEGIN_HOOK + ' ' + key + '\n' + newText + '\n' + END_HOOK + '\n').splitlines(True)
    else:
        newLines = []

    for i, line in enumerate(lines):
        if startRE.search(line):
            start = i
        elif start is not None and endRE.search(line):
            end = i + 1
            break

    # A start and end tag were found so replace the code.
    if start is not None and end is not None:
        lines[start:end] = newLines
    
    # No blocks were found so append the code to the end of the file.
    elif start is None and end is None:
        if newText is not None:
            lines += ['\n'] + newLines
    
    # A start was found but no end so don't do anything to prevent accidental code deletion.
    else:
        return False
    
    return ''.join(lines)


def packageIsRegistered(packageKey):
    
    commonPath = defaultScriptsPath('common') + '/' + packageKey
    common = os.path.exists( commonPath )
    versionedPath = defaultScriptsPath( str(cmds.about(v=True)) ) + '/' + packageKey
    versioned = os.path.exists( versionedPath )
    
    log.debug('Common exists: {}\n{}\nversioned exists: {}\n{}'.format(commonPath, common, versionedPath, versioned) )
    return (common or versioned)


def isTest(name, info):
    package = os.path.basename( os.path.dirname(name) )
    res = re.search(r'(?<![a-z])tests?(?![a-z])', package)
    if res or package in info.get('tests', []):
        return True
    
    return False


def extractZipBasicInfo(zipdata):
    with zipfile.ZipFile( zipdata, 'r') as temp:
        info, infopath = readInfoInZip(temp)

        packageContainerFolder = os.path.dirname(infopath)
        log.debug( 'infoPath:{}  packageContainerFolder:{}'.format(infopath, packageContainerFolder) )
        if not packageContainerFolder:
            log.debug( 'NO container' )
            packagekeys = [name.split('/')[0] for name in temp.namelist()
                if name.endswith('/__init__.py') and name.count('/') == 1 and not isTest(os.path.dirname(name), info)]
            
        else:
            log.debug( 'YES container' )
            slashCount = packageContainerFolder.count('/')
            if slashCount == 0:
                targetCount = 2
            else:
                slashCount + 1
            
            packagekeys = [name for name in temp.namelist()
                if name.endswith('/') and name.count('/') == targetCount and not isTest(name, info)]
        
        assert len(packagekeys) == 1, 'The only folder adjacent to info.json is supposed to be the package, found\n{}'.format(packagekeys)

        if packagekeys[0].endswith('/'):
            packagekey = packagekeys[0][:-1].split('/')[-1]
        else:
            packagekey = packagekeys[0]
        
        
        userSetupCode = readUserSetupCode(temp)

    return info, packagekey, userSetupCode, packageContainerFolder



def ask(zipdata, mayaVersionHint=None):
    ''' CURRENTLY IGNORED - Always install to common version, it's just a confusing question.
    Prompt the user as needed to overwrite if the package exists or get where to
    install to.
    
    Returns: mayaVersion, either 'common' or something like '2019'
    '''
    return ALL_VERSION
    
    global HERE
    info, packagekey, userSetupCode, packageContainerFolder = extractZipBasicInfo(zipdata)
    
    settings = loadSettings()
    
    newBuildTime = info.get('utc_build_time', UTC_BUILD_DEFAULT)
    
    # Figure out the existing build time and mayaVersion, if there is one.
    installedBuildTime = checkInstalledBuiltTime(settings, packagekey, ALL_VERSION)
    if installedBuildTime:
        mayaVersion = ALL_VERSION
    else:
        installedBuildTime = checkInstalledBuiltTime(settings, packagekey, HERE)
        if installedBuildTime:
            mayaVersion = HERE
        else:
            mayaVersion = None
    
    # Figure out if the package is registered at all
    isRegistered = packageIsRegistered(packagekey)
    
    log.debug('Existing build Time {}  :: package exists in registry {}'.format(installedBuildTime, isRegistered))
    
    # Confirm overwriting if the package is already installed
    if installedBuildTime is not None or isRegistered:
        action = cmds.confirmDialog(
            m='An existing install build time\n{}\n\nNew build time\n{}\n\nOverwrite?'.format(
                installedBuildTime, newBuildTime
            ),
            b=['Proceed', 'Cancel'],
        )
        
        if action == 'Cancel':
            return False
    
    # Otherwise ask where to install
    else:
        #'(Advanced) "Custom" lets you choose anywhere by editing userSetup.\n'
        
        if mayaVersionHint:
            assert mayaVersionHint in [ALL_VERSION, HERE], 'mayaVersionHint was {} but does not match {} or {}'.format(mayaVersionHint, ALL_VERSION, HERE)
            return mayaVersionHint
        
        action = cmds.confirmDialog(m=VERSION_MSG, button=[ALL_VERSION, HERE, 'Cancel'])
        
        if action == ALL_VERSION:
            mayaVersion = ALL_VERSION
        elif action == HERE:
            mayaVersion = HERE
        else:
            return False
    
    return mayaVersion


ALL_VERSION = 'common'
HERE = str(cmds.about(q=True, v=True))

VERSION_MSG = 'Where do you want to install?\n\n' + '"' + ALL_VERSION + '" will install to the scripts folder for all Maya versions.\n\n' + '"' + HERE + '" will install to this version of Maya.\n\n'