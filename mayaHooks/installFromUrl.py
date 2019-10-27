from io import BytesIO
import logging
import urllib2
import zipfile

from maya import cmds

from . import installCore
from . import installFromZip

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
    

def run(url):
    '''
    Takes a github.com url, like:
        
        https://github.com/patcorwin/fossil

    Or a url to a zip file.
    '''
    data = readUrlZip(url)

    #with zipfile.ZipFile(BytesIO(data), 'r') as temp:
    #    info, infopath = installCore.readInfoInZip(temp)

    mayaVersion = installCore.ask( BytesIO(data) )
    
    if not mayaVersion:
        return
    
    packageKey = installFromZip.installZip( BytesIO(data), mayaVersion )

    settings = installCore.loadSettings()

    installCore.update(settings, packageKey, mayaVersion,
        source=url,
    )
    cmds.confirmDialog(m='Install complete!')
    
    
def readUrlZip(url):
    
    # Get the package from the url
    if 'github.com' in url:
        log.debug('Received github address')
        if not url.endswith('master.zip'):
            url += '/archive/master.zip'
    
    response = urllib2.urlopen(url)
    log.debug('Respone code: {}'.format(response.code) )
    if response.code != 200:
        raise Exception('Url {} returned code {} instead of 200, aborting'.format(url, response.code))

    # Find and read the info.json file for version info
    data = response.read()
    
    return data