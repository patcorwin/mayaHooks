from itertools import chain, izip_longest

import logging
import os
import sys

from . import installCore
from . import _util

log = logging.getLogger(__name__)
log.setLevel( logging.DEBUG )


def startup():
    '''
    mayaHooks runs this in userSetup for a single point to dynimcally load resources.

    It loads icon paths and dynamic loading of dev packages to mimic regular installation.
    '''

    settings = installCore.loadSettings()

    def packages():
        return chain(
            izip_longest(settings.get('common', {}).items(), [], fillvalue='common'),
            izip_longest(settings.get(installCore.HERE, {}).items(), [], fillvalue=installCore.HERE)
        )
    
    # Load dev installs
    for (packageKey, info), mayaVersion in packages():
        folder = info['source']
        if os.path.isdir( folder ):
            log.debug( '-- Dev install: {} -- {}'.format(packageKey, folder) )

            container = os.path.dirname( folder )
            log.debug( '---- path {}'.format(container) )
            sys.path.append( container )

            code = container + '/userSetup_code.py'

            if os.path.exists(code):
                log.debug( '---- user setup: {}'.format(code) )
                # Dynamically load the user setups since they all have the same name
                _util.runFile(code)
            else:
                log.debug( '---- no user setup' )

    # Add any icon paths
    for (packageKey, info), mayaVersion in packages():

        packageRoot = installCore.defaultScriptsPath(mayaVersion) + '/' + packageKey

        paths = info.get('icon_paths', [])
        if paths:
            os.environ['XBMLANGPATH'] += ';' + ';'.join( [packageRoot + '/' + p for p in paths] )
