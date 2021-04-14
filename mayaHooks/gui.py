from __future__ import absolute_import, division, print_function

from functools import partial
import json
import os
import traceback
try: # python 3
    from urllib import request
except ImportError:
    from urllib2 import urlopen as request

from maya.cmds import button, columnLayout, confirmDialog, deleteUI, evalDeferred, fileDialog2, \
    rowLayout, scrollField, scrollLayout, setParent, shelfButton, shelfLayout, showWindow, tabLayout, text, textField, \
    textFieldButtonGrp, textScrollList, window, formLayout

import mayaHooksCore

from . import checkForUpdates
from .install import core
from .install import fromUrl
from .install import fromZip


class Gui(object):
    NAME = 'mayaHooks_installer'
    
    def __init__(self):
        if window(self.NAME, ex=True):
            deleteUI(self.NAME)
        
        window(self.NAME)
        
        mainForm = formLayout()
        
        inputs = columnLayout(adj=True)
        
        if True:
            rowLayout(nc=3, ct3=['left', 'both', 'right'])
            text(label='URL')
            self.urlField = textField(w=300)
            button(l='Install', c=self.urlInstall)
            setParent('..')
        
        text(l='')
        
        if True:
            rowLayout(nc=3, ct3=['left', 'both', 'right'])
            text(label='Zip')
            self.zipField = textFieldButtonGrp(l='', bl='...', bc=self.fileBrowse, w=300, cw3=[1, 250, 50])
            button(l='Install', c=self.zipInstall)
            setParent('..')
        
        text(l='')
        
        button(l='Check for Updates', c=self.checkForUpdates, en=False )
        
        text(l='Middle Mouse drag the shelf icons onto your own shelf.  They will regenerate when you reopen this gui.')
        
        settings = core.loadSettings()
        
        shelfErrors = set()
        setParent('..')
        scroll = scrollLayout(childResizable=True)
        
        formLayout(mainForm, e=True, af=[ (inputs, 'left', 0), (inputs, 'right', 0), (inputs, 'top', 0) ])
        formLayout(mainForm, e=True, af=[ (scroll, 'left', 0), (scroll, 'right', 0), (scroll, 'bottom', 0)],
            ac=[(scroll, 'top', 0, inputs)])
        
        columnLayout(adj=True)
        
        for ver in ['common']:  # ['common', str(about(v=True))]: # For now, always install for all versions

            scriptPath = core.defaultScriptsPath(mayaVersion=ver)

            text(l='')  # Used to show version
            for name, data in settings.get(ver, {}).items():
                if name not in ('mayaHooks', 'mayaHooksCore'):
                    button(l='Uninstall ' + name, c=partial(self.uninstall, name, ver) )
                
                if data.get('source_type', None) == 'dev':
                    info = os.path.dirname( data['source'] ) + '/info.json'
                    if os.path.exists(info):
                        try:
                            with open(info, 'r') as fid:
                                data = json.load(fid)
                        except Exception:
                            pass
                
                if data.get( 'shelf_items' ):

                    if 'local_path' in data:
                        scriptPath = os.path.dirname( data['local_path'] )

                    tabLayout()
                    shelfLayout(name + '_shelf', h=60)
                    
                    for item in data['shelf_items']:

                        #if 'imageOverlayLabel' not in item:
                        #    item['imageOverlayLabel'] = item.get('annotation', '')

                        image = item.get('image', '')
                        if not image:
                            #del item['image']
                            item['image'] = 'pythonFamily.png'
                        else:
                            # Maya forgets backslashes, so go forward
                            iconPath = os.path.normpath( scriptPath + '/' + image ).replace('\\', '/')
                            if os.path.exists( iconPath ):
                                item['image'] = iconPath
                        
                        if 'label' not in item:
                            item['label'] = item.get( 'annotation', '' )

                        #item['style'] = 'iconOnly'
                            
                        item = {str(k): str(v) if isinstance(v, str) else v for k, v in item.items()}  # Commands can't take unicode (in python 2.7)
                        try:
                            shelfButton( **item )
                        except Exception:
                            print( traceback.format_exc() )
                            shelfErrors.add(name)
                            
                    setParent('..')
                    setParent('..')
        
        showWindow()
        
        if shelfErrors:
            confirmDialog(m='The following packages and issues loading their shelf items:\n\n' + '\n'.join(shelfErrors))
    
    
    def uninstall(self, name, ver, *args):
        
        res = confirmDialog(m='Are you sure you want to uninstall {}?'.format(name), b=['Yes', 'Nevermind'])
        
        if res == 'Yes':
            mayaHooksCore.uninstall(name, ver)
            evalDeferred('mayaHooks.main()')
    
        
    def urlInstall(self, arg):
        data = textField(self.urlField, q=True, tx=True)
        fromUrl.run(data)
        evalDeferred('mayaHooks.main()')
    
    def zipInstall(self, arg):
        data = textFieldButtonGrp(self.zipField, q=True, tx=True)
        fromZip.run(data)
        evalDeferred('mayaHooks.main()')
    
    def fileBrowse(self):
        files = fileDialog2(ff='*.zip', fm=1 )
        if files:
            textFieldButtonGrp(self.zipField, e=True, tx=files[0])
    
    def checkForUpdates(self, arg):
        checkForUpdates.checkAll()


_cache_ = {}


def packages():
    global _cache_

    if not _cache_:
        try:
            url = 'https://raw.githubusercontent.com/patcorwin/mayaHooksRepo/master/repository.json'
            response = request(url)
        except Exception:
            return

        try:
            data = response.read()
            _cache_ = json.loads( data )
        except Exception:
            print( "Error Loading\n" + data )

    return _cache_.get('packages', [])


'''def getPackageInfo(name):
    global _cache_

    readme = _cache_[name].get('readme', None)
    if not readme:
'''


class PackageBrowser(object):
    NAME = 'mayaHooks Package Browser'

    def __init__(self):
        if window(self.NAME, ex=True):
            deleteUI(self.NAME)

        self.win = window(self.NAME)
        columnLayout(adj=True)
        self.packageList = textScrollList(nr=10, sc=self.selectPackage)
        button(label='Install', c=self.install)
        self.name = text(label='')

        self.info = scrollField(editable=False)

        self.listPackages()
        showWindow()

    def install(self, arg):
        try:
            name = textScrollList(self.packageList, q=True, si=True)[0]
        except Exception:
            return

        fromUrl.run( packages()[name]['source'] )
        if window(Gui.NAME, ex=True):
            Gui()
        deleteUI(self.NAME)

    def selectPackage(self, *args):
        name = textScrollList(self.packageList, q=True, si=True)[0]

        text(self.name, e=True, label=name)
        scrollField(self.info, e=True, text=packages()[name]["source"] )

    def listPackages(self):
        #settings = core.loadSettings()
        # Need to filter out things already installed
        for packageName, info in packages().items():
            textScrollList(self.packageList, e=True, a=packageName)