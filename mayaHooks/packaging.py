from __future__ import absolute_import, division, print_function

import base64
import json
import os
import textwrap
import zipfile
import zlib

from . import installCore


def makeMelInstaller():
    
    buildTime = getBuildTime(useDevPath=True)
    
    files = [
        'mayaHooks/info.json',
        'mayaHooks/mayaHooks/__init__.py',
        'mayaHooks/mayaHooks/_util.py',
        'mayaHooks/mayaHooks/checkForUpdates.py',
        'mayaHooks/mayaHooks/dagMenuProc.py',
        'mayaHooks/mayaHooks/installCore.py',
        'mayaHooks/mayaHooks/installDev.py',
        'mayaHooks/mayaHooks/installFromUrl.py',
        'mayaHooks/mayaHooks/installFromZip.py',
        'mayaHooks/mayaHooks/gui.py',
        'mayaHooks/mayaHooks/packaging.py',
        'mayaHooks/mayaHooks/startup.py',
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
        
    scriptFolder = os.environ['maya_app_dir'] + '/scripts'
    
    # write files to scriptFolder + '/mayaHooks'
    '''.format(buildTime))]
    
    allFiles = {}
    
    root = os.path.dirname( os.path.dirname( os.path.dirname(__file__) ) )
    
    for f in files:
        with open(root + '/' + f, 'r') as fid:
            if 'info.json' in f:
                # Special munge to put info.json in /<package>-info/
                parts = f.split('/')
                f = parts[0] + '-info/' + parts[1]
            else:
                # Remove the extra parent directory
                f = f.split('/', 1)[-1]
            
            allFiles[f] = fid.read()
    
    code.append( "allFiles = '''" + base64.encodestring(zlib.compress(json.dumps(allFiles), 9)) + "'''")

    code.append( 'allFiles = json.loads(zlib.decompress( base64.decodestring(allFiles) ))' )

    code.append( textwrap.dedent(
        '''
        for name, text in allFiles.items():
            filepath = os.path.join(scriptFolder, name)
            dirname = os.path.dirname(filepath)

            if not os.path.exists(dirname):
                os.makedirs(dirname)
            
            with open(filepath, 'w') as fid:
                fid.write(text)
        '''
    ) )


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
        
    import mayaHooks.installCore
    import mayaHooks.packaging
    settings = mayaHooks.installCore.loadSettings()
    mayaHooks.installCore.update(settings, 'mayaHooks', 'common',
        utc_install_time=str(datetime.datetime.utcnow()),
        utc_build_time=mayaHooks.packaging.getBuildTime(),
        shelf_items=[
            {
                'command': 'import mayaHooks;mayaHooks.main()',
                'image': '',
                'annotation': 'mhg'
            }
        ]
    )
    
    # Remove old overrides so they get updated if needed and don't leave cruft behind
    import mayaHooks.override.baseOverride
    mayaHooks.override.baseOverride.clearAllOverrides()
    
    import mayaHooksCore
    mayaHooks.installCore.update(settings, 'mayaHooksCore', 'common',
        utc_install_time=str(datetime.datetime.utcnow()),
        utc_build_time=mayaHooksCore.getBuildTime(),
    )
    
    # Add a user setup entry to support dev installs (and icon folders)
    mayaHooks.installCore.userSetupEdit('common', 'mayaHooks startup', 'import mayaHooks.startup;mayaHooks.startup.startup()')
    
    if hooksExisted:
        cmds.confirmDialog(m='mayaHooks successfully installed!')
    else:
        cmds.confirmDialog(m='! IMPORTANT !{0}{0}Middle Mouse drag the mayaHooks shelf item to your own to access it again,{0}or see the script editor for the python code to open it.'.format(os.linesep))
    
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
    
    
    '''))
    
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
    
    with open( os.path.dirname(__file__) + '/../mayaHooksInstaller.mel', 'w' ) as fid:
        fid.write( header + allCode )
    
        
def getBuildTime(useDevPath=False):
    
    if useDevPath:
        jsonFile = os.path.dirname(os.path.dirname(__file__)) + '/info.json'
    else:
        jsonFile = os.path.dirname(__file__) + '-info/info.json'
        
    with open(jsonFile, 'r') as fid:
        info = json.load(fid)
    
    return info.get('utc_build_time', installCore.UTC_BUILD_DEFAULT)


def makeZip(package, output=None, keepPyc=False):

    assert os.path.isdir(package), '"{}" is not a folder'.format(package)

    if not output:
        output = package + '.zip'

    container = os.path.dirname(package)
    cutPoint = len( container ) + 1

    info = container + '/info.json'
    userSetup = container + '/userSetup_code.py'

    assert os.path.exists(info), 'info.json must exist adjacent to the package'

    with zipfile.ZipFile( output, 'w', zipfile.ZIP_DEFLATED ) as fid:

        for path, dirs, files in os.walk(package):
            for f in files:
                if not f.lower().endswith( '.pyc' ) or keepPyc:
                    filename = path + '/' + f
                    arcname = filename[cutPoint:].replace('\\', '/')
                    fid.write(filename, arcname)

        fid.write( info, 'info.json' )

        if os.path.exists(userSetup):
            fid.write( userSetup, 'userSetup_code.py' )
