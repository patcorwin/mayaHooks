from io import BytesIO
import logging
try: # python 3
    from urllib import request
except ImportError:
    from urllib2 import urlopen as request

from maya import cmds

from . import core
from . import fromZip
from .. import _startup


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
    

def run(url, mayaVersionHint=None, silent=False):
    '''
    Takes a github.com url, like:
        
        https://github.com/patcorwin/fossil

    Or a url to a zip file.
    '''

    # Make sure we have well formatted url
    if not url.lower().startswith( ('http://', 'https://')):
        url = 'http://' + url

    data = readUrlZip(url)

    #with zipfile.ZipFile(BytesIO(data), 'r') as temp:
    #    info, infopath = core.readInfoInZip(temp)

    mayaVersion = core.ask( BytesIO(data), mayaVersionHint)
    
    if not mayaVersion:
        return
    
    packageKey = fromZip.installZip( BytesIO(data), mayaVersion )

    settings = core.loadSettings()

    core.update(settings, packageKey, mayaVersion,
        source=url,
        source_type='url',
    )
    
    packagePath = core.defaultScriptsPath(mayaVersion) + '/' + packageKey
    _startup.addIconPaths( settings[mayaVersion][packageKey], packagePath)
    
    if not silent:
        cmds.confirmDialog(m='Install complete!')
    
    
def readUrlZip(url):
    
    # Get the package from the url
    if 'github.com' in url:
        log.debug('Received github address')
        if not url.endswith('master.zip'):
            url += '/archive/master.zip'
    
    response = request(url)
    log.debug('Respone code: {}'.format(response.code) )
    if response.code != 200:
        raise Exception('Url {} returned code {} instead of 200, aborting'.format(url, response.code))

    # Find and read the info.json file for version info
    data = response.read()
    
    return data