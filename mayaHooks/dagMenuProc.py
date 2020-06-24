from __future__ import print_function, absolute_import


from .override import dagMenuProc

# Redirect to new location
overrideDagMenuProc = dagMenuProc.enable

registerMenu = dagMenuProc.customDagMenu.register

unregisterMenu = dagMenuProc.customDagMenu.unregister
