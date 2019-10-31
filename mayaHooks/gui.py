from __future__ import absolute_import, division, print_function

from functools import partial

from maya.cmds import about, button, columnLayout, confirmDialog, deleteUI, fileDialog2, \
    setParent, shelfButton, shelfLayout, showWindow, tabLayout, text, textField, textFieldButtonGrp, window

import mayaHooksCore

from . import checkForUpdates
from . import installCore
from . import installFromUrl
from . import installFromZip


class Gui(object):
    NAME = 'mayaHooks_installer'
    
    def __init__(self):
        if window(self.NAME, ex=True):
            deleteUI(self.NAME)
        
        window(self.NAME)
        columnLayout(adj=True)
        
        button(l='Install from URL', c=self.urlInstall)
        self.urlField = textField()
        
        text(l='')
        
        button(l='Install from Zip', c=self.zipInstall)
        self.zipField = textFieldButtonGrp(l='', bl='...', bc=self.fileBrowse)
        
        text(l='')
        
        button(l='Check for Updates', c=self.checkForUpdates, en=False )
        
        settings = installCore.loadSettings()
        
        for ver in ['common', str(about(v=True))]:
            text(l=ver)
            for name, data in settings.get(ver, {}).items():
                button(l='Uninstall ' + name, c=partial(self.uninstall, name, ver) )
                
                if data.get( 'shelf_items' ):
                    tabLayout()
                    shelfLayout(name + '_shelf', h=100)
                    
                    for item in data['shelf_items']:
                        if item.get('image', ''):
                            del item['image']
                            #item['imageOverlayLabel'] = item.get('annotation', '')
                            #item['image'] = 'pythonFamily.png'
                            #item['style'] = 'iconOnly'
                            
                        item = {str(k): str(v) for k, v in item.items()}  # Commands can't take unicode (in python 2.7)
                        shelfButton( **item )
                    setParent('..')
                    setParent('..')
        
        showWindow()
    
    
    def uninstall(self, name, ver, *args):
        
        res = confirmDialog(m='Are you sure you want to uninstall {}?'.format(name), b=['Yes', 'Nevermind'])
        
        if res == 'Yes':
            mayaHooksCore.uninstall(name, ver)
    
        
    def urlInstall(self, arg):
        data = textField(self.urlField, q=True, tx=True)
        installFromUrl.run(data)
    
    def zipInstall(self, arg):
        data = textFieldButtonGrp(self.zipField, q=True, tx=True)
        installFromZip.run(data)
    
    def fileBrowse(self):
        files = fileDialog2(ff='*.zip', fm=1 )
        if files:
            textField(self.zipField, e=True, tx=files[0])
    
    def checkForUpdates(self, arg):
        checkForUpdates.checkAll()
    