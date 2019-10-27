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