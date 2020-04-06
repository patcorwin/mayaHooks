from __future__ import absolute_import, division, print_function

from functools import partial
import os

from maya.cmds import about, button, columnLayout, confirmDialog, deleteUI, evalDeferred, fileDialog2, \
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
        
        text(l='Middle Mouse drag the shelf icons onto your own shelf.  They will regenerate when you reopen this gui.')
        
        settings = installCore.loadSettings()
        
        for ver in ['common', str(about(v=True))]:

            scriptPath = installCore.defaultScriptsPath(mayaVersion=ver)

            text(l=ver)
            for name, data in settings.get(ver, {}).items():
                if name not in ('mayaHooks', 'mayaHooksCore'):
                    button(l='Uninstall ' + name, c=partial(self.uninstall, name, ver) )
                
                if data.get( 'shelf_items' ):

                    if 'local_path' in data:
                        scriptPath = os.path.dirname( data['local_path'] )

                    tabLayout()
                    shelfLayout(name + '_shelf', h=100)
                    
                    for item in data['shelf_items']:

                        if 'imageOverlayLabel' not in item:
                            item['imageOverlayLabel'] = item.get('annotation', '')

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
        evalDeferred('mayaHooks.main()')
    
    def zipInstall(self, arg):
        data = textFieldButtonGrp(self.zipField, q=True, tx=True)
        installFromZip.run(data)
        evalDeferred('mayaHooks.main()')
    
    def fileBrowse(self):
        files = fileDialog2(ff='*.zip', fm=1 )
        if files:
            textFieldButtonGrp(self.zipField, e=True, tx=files[0])
    
    def checkForUpdates(self, arg):
        checkForUpdates.checkAll()
