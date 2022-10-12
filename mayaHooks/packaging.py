from __future__ import absolute_import, division, print_function

import base64
import collections
import datetime
import json
import os
import sys
import textwrap
import zipfile
import zlib


if sys.version_info.major == 2:
    PY2 = True
else:
    PY2 = False


try:
    base64_encodebytes = base64.encodebytes
except AttributeError:
    base64_encodebytes = base64.encodestring # decodestring is a deprecated alias in 3.1


_mayaHooksfiles = [
    'mayaHooks/info.json',
    'mayaHooks/mayaHooks/__init__.py',
    'mayaHooks/mayaHooks/_util.py',
    'mayaHooks/mayaHooks/checkForUpdates.py',
    'mayaHooks/mayaHooks/dagMenuProc.py',
    'mayaHooks/mayaHooks/icons/mayaHooksGui.png',
    'mayaHooks/mayaHooks/install/__init__.py',
    'mayaHooks/mayaHooks/install/core.py',
    'mayaHooks/mayaHooks/install/dev.py',
    'mayaHooks/mayaHooks/install/fromUrl.py',
    'mayaHooks/mayaHooks/install/fromZip.py',
    'mayaHooks/mayaHooks/gui.py',
    'mayaHooks/mayaHooks/packaging.py',
    'mayaHooks/mayaHooks/_startup.py',
    'mayaHooks/mayaHooks/override/__init__.py',
    'mayaHooks/mayaHooks/override/baseOverride.py',
    'mayaHooks/mayaHooks/override/dagMenuProc.py',
    'mayaHooks/mayaHooks/override/FileMenu.py',
    'mayaHooks/mayaHooks/override/gameFbxExporter.py',
    'mayaHooks/mayaHooks/override/incrementalSaveScene.py',
    
    'mayaHooksCore/info.json',
    'mayaHooksCore/mayaHooksCore/__init__.py',
    'mayaHooksCore/mayaHooksCore/vendor/__init__.py',
    'mayaHooksCore/mayaHooksCore/vendor/send2trash/LICENSE',
    'mayaHooksCore/mayaHooksCore/vendor/send2trash/__init__.py',
    'mayaHooksCore/mayaHooksCore/vendor/send2trash/compat.py',
    'mayaHooksCore/mayaHooksCore/vendor/send2trash/exceptions.py',
    'mayaHooksCore/mayaHooksCore/vendor/send2trash/plat_gio.py',
    'mayaHooksCore/mayaHooksCore/vendor/send2trash/plat_osx.py',
    'mayaHooksCore/mayaHooksCore/vendor/send2trash/plat_other.py',
    'mayaHooksCore/mayaHooksCore/vendor/send2trash/plat_win.py',
]

def makeMelInstaller(outputFolder=None, autoUpdateBuildTime=True):
    
    if autoUpdateBuildTime:
        updateBuildTime()
    
    if outputFolder:
        output = outputFolder + '/mayaHooksInstaller.mel'
    else:
        output = os.path.dirname(__file__) + '/../mayaHooksInstaller.mel'
    
    header = textwrap.dedent('''
    /*
    Simplified installation of mayaHooks, just drag this into maya to start the installation.


    All the code for the mayaHooks python module is compressed here with zlib
    and base64.  I tried to have it all as plain text but escaping multiline code
    within multiline code that contained multiline code got too complicated.
    */
    ''')

    # Make a base64 string of all the files so they can be embedded
    allFiles = collectAllFiles()
    
    allFilesStr = base64_encodebytes(zlib.compress( json.dumps(allFiles).encode('utf-8'), 9)).replace(b'\n', b'\\n\\\n')

    if not PY2: # py2 is bytestrings so encoding does nothing, but py3 needs to decode to `str` to be saved properly.
        allFilesStr = allFilesStr.decode()
    
    with open( os.path.dirname(os.path.dirname(__file__)) + '/info.json', 'r' ) as fid:
        info = str(json.load(fid))

    with open( os.path.dirname(__file__) + '/melwrapped.template.py', 'r' ) as fid:
        code = fid.read().replace('"', '\\"') # Escape any quotes to not interfere with the wrapping mel quotes
        allCode = '\\n\\\n'.join( [line if line.strip() else '' for line in code.splitlines()] )

    buildTime = getBuildTime(useDevPath=True)

    allCode = allCode.format(info=info, buildTime=buildTime, compressedFiles=allFilesStr)
    allCode = 'python("' + allCode + '");'

    with open( output, 'w' ) as fid:
        fid.write( header + allCode )
    
    return output


def collectAllFiles():
    allFiles = collections.OrderedDict()
    root = os.path.dirname( os.path.dirname( os.path.dirname(__file__) ) )
    
    for f in _mayaHooksfiles:
        if f.lower().endswith('.png'):
            with open(root + '/' + f, 'rb') as fid:
                # Remove the extra parent directory
                f = f.split('/', 1)[-1]
                #allFiles[f] = fid.read().encode('base64')
                allFiles[f] = base64.b64encode(fid.read()).decode()
        else:
            with open(root + '/' + f, 'r') as fid:
                if 'info.json' in f:
                    # Special munge to put info.json in /<package>-info/
                    parts = f.split('/')
                    f = parts[0] + '-info/' + parts[1]
                else:
                    # Remove the extra parent directory
                    f = f.split('/', 1)[-1]
                
                allFiles[f] = fid.read()
    return allFiles


def makeMelInstaller_old(outputFolder=None):
    ''' Compile everything into a single mel file, optionally specifying the output folder.
    '''
    if outputFolder:
        output = outputFolder + '/mayaHooksInstaller.mel'
    else:
        output = os.path.dirname(__file__) + '/../mayaHooksInstaller.mel'
    
    buildTime = getBuildTime(useDevPath=True)
    
    files = [
        'mayaHooks/info.json',
        'mayaHooks/mayaHooks/__init__.py',
        'mayaHooks/mayaHooks/_util.py',
        'mayaHooks/mayaHooks/checkForUpdates.py',
        'mayaHooks/mayaHooks/dagMenuProc.py',
        'mayaHooks/mayaHooks/icons/mayaHooksGui.png',
        'mayaHooks/mayaHooks/install/__init__.py',
        'mayaHooks/mayaHooks/install/core.py',
        'mayaHooks/mayaHooks/install/dev.py',
        'mayaHooks/mayaHooks/install/fromUrl.py',
        'mayaHooks/mayaHooks/install/fromZip.py',
        'mayaHooks/mayaHooks/gui.py',
        'mayaHooks/mayaHooks/packaging.py',
        'mayaHooks/mayaHooks/_startup.py',
        'mayaHooks/mayaHooks/override/__init__.py',
        'mayaHooks/mayaHooks/override/baseOverride.py',
        'mayaHooks/mayaHooks/override/dagMenuProc.py',
        'mayaHooks/mayaHooks/override/FileMenu.py',
        'mayaHooks/mayaHooks/override/gameFbxExporter.py',
        'mayaHooks/mayaHooks/override/incrementalSaveScene.py',
        
        'mayaHooksCore/info.json',
        'mayaHooksCore/mayaHooksCore/__init__.py',
        'mayaHooksCore/mayaHooksCore/vendor/__init__.py',
        'mayaHooksCore/mayaHooksCore/vendor/send2trash/LICENSE',
        'mayaHooksCore/mayaHooksCore/vendor/send2trash/__init__.py',
        'mayaHooksCore/mayaHooksCore/vendor/send2trash/compat.py',
        'mayaHooksCore/mayaHooksCore/vendor/send2trash/exceptions.py',
        'mayaHooksCore/mayaHooksCore/vendor/send2trash/plat_gio.py',
        'mayaHooksCore/mayaHooksCore/vendor/send2trash/plat_osx.py',
        'mayaHooksCore/mayaHooksCore/vendor/send2trash/plat_other.py',
        'mayaHooksCore/mayaHooksCore/vendor/send2trash/plat_win.py',
    ]

    code = [ textwrap.dedent('''
    import json
    import base64
    import datetime
    import os
    import zlib
    
    from maya import cmds
    
    try:
        import mayaHooks
        exists = True
    except:
        exists = False
    buildTime = '{}'
    if exists:
        existinInfo = os.path.join(os.path.dirname( mayaHooks.__file__ ) + '-info', 'info.json')
        existingBuildTime = None
        if os.path.exists(existinInfo):
            try:
                with open(existinInfo, 'r') as fid:
                    data = json.load(fid)
                
                existingBuildTime = data.get('utc_build_time', None)
            except Exception:
                pass
                
        if existingBuildTime:
            
            if buildTime > existingBuildTime:
                res = cmds.confirmDialog(m='Update with this newer version of mayaHooks?\\\\n\\\\nExisting build time: {{}}\\\\nThis new build time: {{}}'.format(existingBuildTime, buildTime),
                    b=['Upgrade', 'Cancel'])
                if res != 'Upgrade':
                    raise Exception('Canceled install')
                    
            else:
                res = cmds.confirmDialog(m='Downgrade to this older version of mayaHooks?\\\\n\\\\nExisting build time: {{}}\\\\nThis old build time: {{}}'.format(existingBuildTime, buildTime),
                    b=['Downgrade', 'Cancel'])
                if res != 'Downgrade':
                    raise Exception('Canceled install')
                
        else:
            res = cmds.confirmDialog(m='An existing mayaHooks was found but the build time could not be determined.\\\\n\\\\nUpdate to this version?    {{}}'.format(buildTime),
                b=['Update', 'Cancel'])
            if res != 'Update':
                raise Exception('Canceled install')
        
    scriptFolder = os.environ['MAYA_APP_DIR'] + '/scripts'
    
    # write files to scriptFolder + '/mayaHooks'
    '''.format(buildTime))]
    
    allFiles = {}
    
    root = os.path.dirname( os.path.dirname( os.path.dirname(__file__) ) )
    
    for f in files:
        if f.lower().endswith('.png'):
            with open(root + '/' + f, 'rb') as fid:
                # Remove the extra parent directory
                f = f.split('/', 1)[-1]
                allFiles[f] = fid.read().encode('base64')
        else:
            with open(root + '/' + f, 'r') as fid:
                if 'info.json' in f:
                    # Special munge to put info.json in /<package>-info/
                    parts = f.split('/')
                    f = parts[0] + '-info/' + parts[1]
                else:
                    # Remove the extra parent directory
                    f = f.split('/', 1)[-1]
                
                allFiles[f] = fid.read()
    
    code.append( "allFiles = '''" + base64_encodebytes(zlib.compress(json.dumps(allFiles), 9)) + "'''")

    code.append( 'allFiles = json.loads(zlib.decompress( base64.decodestring(allFiles) ))' )

    code.append( textwrap.dedent(
        '''
        import base64
        for name, text in allFiles.items():
            #print('unpacking ' + name)
            filepath = os.path.join(scriptFolder, name)
            dirname = os.path.dirname(filepath)

            if not os.path.exists(dirname):
                os.makedirs(dirname)
                
            if name.lower().endswith('.png'):
                rawBytes = base64.b64decode(text)
                with open(filepath, 'wb') as fid:
                    fid.write(rawBytes)
            else:
                with open(filepath, 'w') as fid:
                    fid.write(text)
        '''
    ) )
    
    with open( os.path.dirname(os.path.dirname(__file__)) + '/info.json', 'r' ) as fid:
        info = json.load(fid)

    code.append( textwrap.dedent('''
    def remPackage(packageName):
        # Remove reference to the given `packageName`
        
        wasRemoved = False
        import sys
        dotName = packageName + '.'
        for name in list(sys.modules.keys()):
            if name.startswith(dotName):
                del sys.modules[name]
                wasRemoved = True
        
        if packageName in sys.modules:
            del sys.modules[packageName]
            wasRemoved = True
        
        return wasRemoved
    
    hooksExisted = remPackage('mayaHooks')
    remPackage('mayaHooksCore')
        
    import mayaHooks.install.core
    import mayaHooks.packaging
    settings = mayaHooks.install.core.loadSettings()
    
    info = %s
    
    mayaHooks.install.core.update(settings, 'mayaHooks', 'common',
        utc_install_time=str(datetime.datetime.utcnow()),
        **info
    )
    
    # Remove old overrides so they get updated if needed and don't leave cruft behind
    import mayaHooks.override.baseOverride
    mayaHooks.override.baseOverride.clearAllOverrides()
    
    import mayaHooksCore
    mayaHooks.install.core.update(settings, 'mayaHooksCore', 'common',
        utc_install_time=str(datetime.datetime.utcnow()),
        utc_build_time=mayaHooksCore.getBuildTime(),
    )
    
    # Add a user setup entry to support dev installs (and icon folders)
    mayaHooks.install.core.userSetupEdit('common', 'mayaHooks startup', 'import mayaHooks;mayaHooks.startup()')
    
    if hooksExisted:
        cmds.confirmDialog(m='mayaHooks successfully installed!')
    else:
        import mayaHooks._startup
        cmds.confirmDialog(m='! IMPORTANT !{0}{0}Middle Mouse drag the mayaHooks shelf item to your own to access it again,{0}or see the script editor for the python code to open it.'.format(os.linesep))
    
    hooksPackagePath = mayaHooks.install.core.defaultScriptsPath('common') + '/mayaHooks'
    mayaHooks._startup.addIconPaths(info, hooksPackagePath)
    
    print( """# Code to open mayaHooks gui
    import mayaHooks
    mayaHooks.main()
    # End mayaHooks code""")
    
    import inspect
    class FullReload(object):

        @staticmethod
        def cleanpath(path):
            return os.path.normcase( os.path.normpath(path) )

        def __call__(self, top):
            
            self.reloaded = set()
            self.src_path = os.path.dirname( self.cleanpath(top.__file__) )
            
            self.reload_module(top)
            print('done', len(self.reloaded))

        def reload_module(self, top):
            self.reloaded.add(top.__file__)
            for name in dir(top):
                sub = getattr(top, name)
                if inspect.ismodule( sub ):
                    if hasattr(sub, '__file__') and sub.__file__ not in self.reloaded:
                        try:
                            if self.cleanpath(sub.__file__).startswith( self.src_path ):
                                self.reload_module(sub)
                        except AttributeError:
                            raise
            reload(top)


    fullReload = FullReload()
    
    import mayaHooks
    fullReload(mayaHooks)
    mayaHooks.main()
    
    
    ''' % str(info)) )
    
    #allCode = '\n'.join(code).replace('\n', '\\n\\\n').replace('"', '\\"')
    
    allCode = '\\n\\\n'.join( [l for l in '\n'.join(code).splitlines()] ).replace('"', '\\"')
    allCode = 'python("' + allCode + '");'
    
    
    header = textwrap.dedent('''
        /*
        Simplified installation of mayaHooks, just drag this into maya to start the installation.
        
        
        All the code for the mayaHooks python module is compressed here with zlib
        and base64.  I tried to have it all as plain text but escaping multiline code
        within multiline code that contained multiline code got too complicated.
        */
        ''')
    
    with open( output, 'w' ) as fid:
        fid.write( header + allCode )
    

def updateBuildTime():
    jsonFile = os.path.dirname(os.path.dirname(__file__)) + '/info.json'

    with open(jsonFile, 'r') as fid:
        info = json.load(fid, object_pairs_hook=collections.OrderedDict)
    
    info['utc_build_time'] = str(datetime.datetime.utcnow())
    
    with open(jsonFile, 'w') as fid:
        json.dump(info, fid, indent=4)


def getBuildTime(useDevPath=False):
    
    if useDevPath:
        jsonFile = os.path.dirname(os.path.dirname(__file__)) + '/info.json'
    else:
        jsonFile = os.path.dirname(__file__) + '-info/info.json'
        
    with open(jsonFile, 'r') as fid:
        info = json.load(fid)
    
    return info.get('utc_build_time', '2000-00-00 00:00:00.000000') # The Y2k time is core.UTC_BUILD_DEFAULT, but not worth the entanglement


def makeZip(package, outputFolder=None, keepPyc=False, autoUpdateBuildTime=True):
    ''' Given a full path to a python package, identifies adjacent info.json and optional userSetup_code.py to make a zip.
    
    info.py is required, *.pyc's are excluded by default.
    
    Args:
        package: Full path to a python package, i.e. a folder with an __init__.py
        outputFolder: Defaults to an adjacent <package>.zip, can be a folder or a full path a *.zip
        keepPyc: Keep *.pyc files, defaults false
    '''
    
    if autoUpdateBuildTime:
        updateBuildTime()
    
    package = os.path.expandvars( os.path.expanduser(package) )
    assert os.path.isdir(package), '"{}" is not a folder'.format(package)

    container = os.path.dirname(package)
    packageName = os.path.basename(package)

    if not outputFolder:
        #outputFolder = package + '.zip'
        outputFolder = container + '/' + packageName + '.zip'
    else:
        outputFolder = os.path.expandvars( os.path.expanduser(outputFolder) )

    if not outputFolder.lower().endswith('.zip'):
        
        outputFolder += '/' + packageName + '.zip'

    
    cutPoint = len( container ) + 1

    info = container + '/info.json'
    userSetup = container + '/userSetup_code.py'

    assert os.path.exists(info), 'info.json must exist adjacent to the package'

    with zipfile.ZipFile( outputFolder, 'w', zipfile.ZIP_DEFLATED ) as fid:

        for path, dirs, files in os.walk(package):
            for f in files:
                if not f.lower().endswith( '.pyc' ) or keepPyc:
                    filename = path + '/' + f
                    arcname = filename[cutPoint:].replace('\\', '/')
                    fid.write(filename, arcname)

        fid.write( info, 'info.json' )

        if os.path.exists(userSetup):
            fid.write( userSetup, 'userSetup_code.py' )


def validateInfo(info_or_path):
    ''' UNTESTED '''
    if isinstance(info_or_path, str):
        with open(info_or_path, 'r') as fid:
            info = json.load(fid.read())
    else:
        info = info_or_path
        
    assert 'utc_build_time' in info, 'info.json must contain "utc_build_time"'
    
    keys = info.keys()
    
    schema = {
        'tests': 'list of strings',
        'icon_paths': 'list of strings',
        'shelf_items': 'list of dicts',
        'utc_build_time': 'string'
    }
    
    datatypeErrors = []
    
    def checkType(value, name, datatype):
        if not isinstance( value, datatype ):
            datatypeErrors.append( '{} is not a {}'.format(name, datatype) )
    
    
    for name, datatype in schema.items():
        if name in info:
            if datatype == 'list of strings':
                checkType(info[name], name, list)
                for entry in info[name]:
                    checkType(entry, '{}|{}'.format(name, entry), str)
                    
            elif datatype == 'list of dicts':
                checkType(info[name], name, list)
                for entry in info[name]:
                    checkType(entry,  '{}|{}'.format(name, entry), dict )
            
            elif datatype == 'string':
                checkType(info[name], name, str)
            
            keys.remove(name)
    
    errors = {}
    if datatypeErrors:
        errors['data'] = datatypeErrors
        
    if keys:
        errors['unknown keys'] = keys
        
    return errors
    
    