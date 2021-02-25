from __future__ import absolute_import, division, print_function

from io import BytesIO
from functools import partial
import json
import os
import urllib2
import zipfile

from maya import cmds


from .install import core

from .install import fromUrl
from .install import fromZip


class Zip(object):
    
    def test(self, source):
        if os.path.exists(source) and source.lower().endswith('.zip'):
            return True

    def checkForNewer(self, packageSettings):
        modified = os.path.getmtime(packageSettings['source'])
        if modified > packageSettings['source_data']['modified_time']:
            return True
        
        info, _ = core.readInfoInZip(packageSettings['source'])
        
        return info, fromZip


class ZipURL(object):
    def test(self, source):
        return source.startswith(('http', 'www.')) and source.lower().endswith('.zip')

    def checkForNewer(self, packageSettings):
        res = urllib2.urlopen( packageSettings['source'] )

        if res.code != 200:
            cmds.warning('This is not a valid url for a zip file {}'.format(packageSettings['source']) )
            return False
        
        with zipfile.ZipFile(BytesIO(res.read()), 'r') as temp:
            info, infopath = core.readInfoInZip(temp)
        
        return info, fromUrl

    
class Github(object):
    
    def test(self, source):
        if 'github.com' in source:
            return True
    
    def checkForNewer(self, packageSettings):
        
        jsonFile = packageSettings['source'].replace( 'github.com', 'raw.githubusercontent.com') + '/master/info.json'
        res = urllib2.urlopen( jsonFile )
        
        if res.code != 200:
            cmds.warning('info.json URL {} is not valid'.format(jsonFile) )
            return False
        
        info = json.loads( res.read() )
        
        return info, fromUrl
    
        
def check(settings, packageKey, mayaVersion):
    '''
    
    '''
    
    packageSettings = core.findPackageSettings(settings, packageKey, mayaVersion)
    
    if packageSettings is None:
        return False, False
    
    
    sourceTests = [Zip(), ZipURL(), Github()]
    newerInfo = False
    for tester in sourceTests:
        if tester.test(packageSettings['source']):
            newerInfo, installer = tester.checkForNewer(packageSettings)
            break
            
    if newerInfo:
        if newerInfo['utc_build_time'] > packageSettings['utc_build_time']:
            return installer, packageSettings['source']
            
            
def checkAll():
    settings = core.loadSettings()
    
    update = []
    
    for mayaVersion, packages in settings.items():
        for packageKey in packages:
            installer, source = check(settings, packageKey, mayaVersion)
            if installer:
                update.append( (packageKey, mayaVersion, source, installer) )
    
    
    action = cmds.confirmDialog(
        m='These packages have new builds:\n\n' + '\n'.join( [packageKey + ':' + mayaVersion for packageKey, mayaVersion, _, _ in update] ),
        b=['Update All', 'Choose Individual', 'Cancel']
    )
    
    if action == 'Update All':
        for packageKey, mayaVersion, source, installer in update:
            installer.run(source, promptForOverwrite=False, mayaVersion=mayaVersion)
    elif action == 'Choose Individual':
        IndividualUpdate()


class IndividualUpdate(object):

    NAME = 'mayaHookIndividualUpdate'

    def __init__(self, updates):
        self.updates = updates

        if cmds.window(self.NAME, ex=True):
            cmds.deleteUI(self.NAME)

        cmds.window(self.NAME)
        cmds.columnLayout(adj=1)
        cmds.checkBox(label='All', v=True, onc=partial(self.checkAll, True), onf=partial(self.checkAll, False))
        cmds.separator()

        self.checks = []
        for packageKey, mayaVersion, source, installer in self.updates:
            self.checks.append( cmds.checkBox(label=packageKey, v=True) )
        
        cmds.button(label='Update', c=self.update)
        cmds.showWindow()


    def checkAll(self, val):
        for cb in self.checks:
            cmds.checkBox(cb, e=True, v=val)


    def update(self):
        for cb, (packageKey, mayaVersion, source, installer) in zip(self.checks, self.updates):
            if cmds.checkBox(cb, q=True, v=True):
                installer.run(source, promptForOverwrite=False, mayaVersion=mayaVersion)