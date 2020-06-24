'''

info.json spec

{
    "utc_build_time": <generally str(datetime.utcnow() required>,
    "icon_paths": Optional list of paths with icons, ex
        [ 'icons', # A  'icons' folder exists underneath the package, ex somePackage/icons
        ]
    "shelf_items": Optional list of dicts to become shelf buttons displayed in the mayaHooks gui.
        Dict are kwargs for shelfButton
}

'''

from __future__ import absolute_import, division, print_function

#import time

#from . import checkForUpdates
#from . import installFromUrl # noqa
#from . import installFromZip # noqa

#from maya import cmds

from .gui import Gui as main # noqa


'''
if cmds.optionVar(ex='mayaHooks_updateCheckTime'):
    lastUpdated = cmds.optionVar(q='mayaHooks_updateCheckTime')
else:
    lastUpdated = 0.0

if time.time() - lastUpdated > 60 * 60 * 24:  # Only check once a day

    cmds.optionVar(fv=('mayaHooks_updateCheckTime', time.time()) )
    checkForUpdates.checkAll()
'''