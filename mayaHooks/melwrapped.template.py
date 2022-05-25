
import json
import base64
import datetime
import os
import zlib

from maya import cmds

try:
    import mayaHooks
    exists = mayaHooks.__file__ # Somehow mayaHooks can end up as namespace only in 3, investigate later.
except:
    exists = False
buildTime = '{buildTime}'
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
            res = cmds.confirmDialog(m='Update with this newer version of mayaHooks?\\n\\nExisting build time: {{}}\\nThis new build time: {{}}'.format(existingBuildTime, buildTime),
                b=['Upgrade', 'Cancel'])
            if res != 'Upgrade':
                raise Exception('Canceled install')
                
        else:
            res = cmds.confirmDialog(m='Downgrade to this older version of mayaHooks?\\n\\nExisting build time: {{}}\\nThis old build time: {{}}'.format(existingBuildTime, buildTime),
                b=['Downgrade', 'Cancel'])
            if res != 'Downgrade':
                raise Exception('Canceled install')
            
    else:
        res = cmds.confirmDialog(m='An existing mayaHooks was found but the build time could not be determined.\\n\\nUpdate to this version?    {{}}'.format(buildTime),
            b=['Update', 'Cancel'])
        if res != 'Update':
            raise Exception('Canceled install')
    
scriptFolder = os.environ['MAYA_APP_DIR'] + '/scripts'

# write files to scriptFolder + '/mayaHooks'

allFiles = '''{compressedFiles}'''
allFiles = json.loads(zlib.decompress( base64.decodestring(allFiles.encode('utf-8')) ))

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
    
import mayaHooks.install.core # noqa
import mayaHooks.packaging # noqa
settings = mayaHooks.install.core.loadSettings()

info = {info}

mayaHooks.install.core.update(settings, 'mayaHooks', 'common',
    utc_install_time=str(datetime.datetime.utcnow()),
    **info
)

# Remove old overrides so they get updated if needed and don't leave cruft behind
import mayaHooks.override.baseOverride # noqa
mayaHooks.override.baseOverride.clearAllOverrides()

import mayaHooksCore # noqa
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
    cmds.confirmDialog(m='! IMPORTANT !{{0}}{{0}}Middle Mouse drag the mayaHooks shelf item to your own to access it again,{{0}}or see the script editor for the python code to open it.'.format(os.linesep))

hooksPackagePath = mayaHooks.install.core.defaultScriptsPath('common') + '/mayaHooks'
mayaHooks._startup.addIconPaths(info, hooksPackagePath)

print( """# Code to open mayaHooks gui
import mayaHooks
mayaHooks.main()
# End mayaHooks code""")

import inspect

try:
    reload
except NameError:
    from importlib import reload

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

import mayaHooks # noqa
fullReload(mayaHooks)
mayaHooks.main()