from __future__ import absolute_import, division, print_function

import base64
import json
import os
import textwrap
import zlib

from . import installCore

def makeMelInstaller():
    files = [
        'mayaHooks/info.json',
        'mayaHooks/mayaHooks/__init__.py',
        'mayaHooks/mayaHooks/_util.py',
        'mayaHooks/mayaHooks/checkForUpdates.py',
        'mayaHooks/mayaHooks/dagMenuProc.py',
        'mayaHooks/mayaHooks/installCore.py',
        'mayaHooks/mayaHooks/installFromUrl.py',
        'mayaHooks/mayaHooks/installFromZip.py',
        'mayaHooks/mayaHooks/gui.py',
        'mayaHooks/mayaHooks/selfInstaller.py',
        
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
    
    if exists:
        cmds.confirmDialog(m='mayaHooks already exists')
        raise Exception('mayaHooks already exists')
    
    
    scriptFolder = os.environ['maya_app_dir'] + '/scripts'
    
    #if not os.path.exists(scriptFolder + '/mayaHooks'):
    #    os.makedirs(scriptFolder + '/mayaHooks')
    
    
    # write files to scriptFolder + '/mayaHooks'
    ''')]
    
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
            
            ## info.json is a special case
            #if name.endswith('info.json'):
            #    dirname += '-info'
            #    filepath = os.path.join(dirname, 'info.json')
            ## The rest of the files need to have the top dir stripped out
            #else:
            #    dirname = dirname.split('/', 1)[-1]
            #    filepath = filepath.split('/', 1)[-1]
            
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            
            with open(filepath, 'w') as fid:
                fid.write(text)
        '''
    ) )


    code.append( textwrap.dedent('''
    import mayaHooks.installCore
    import mayaHooks.selfInstaller
    settings = mayaHooks.installCore.loadSettings()
    mayaHooks.installCore.update(settings, 'mayaHooks', 'common',
        utc_install_time=str(datetime.datetime.utcnow()),
        utc_build_time=mayaHooks.selfInstaller.getBuildTime(),
    )
    
    import mayaHooksCore
    mayaHooks.installCore.update(settings, 'mayaHooksCore', 'common',
        utc_install_time=str(datetime.datetime.utcnow()),
        utc_build_time=mayaHooksCore.getBuildTime(),
    )
    
    cmds.confirmDialog(m='mayaHooks successfully installed!')
    
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
    
        
def getBuildTime():
    
    with open(os.path.dirname(__file__) + '-info/info.json', 'r') as fid:
        info = json.load(fid)
    
    return info.get('utc_build_time', installCore.UTC_BUILD_DEFAULT)