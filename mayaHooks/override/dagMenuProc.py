'''
Provides an easy hook for appending menus to the dag right click menu.

This can be ran in userSetup.py or the script editor.

An example of a hook (you can run this in the script editor and it will only be active for this session):

    import mayaHooks.override.dagMenuProc
    mayaHooks.override.dagMenuProc.enable()
    
    from pymel.core import Callback, menuItem, setParent
    
    def showMessage(msg):
        print( msg )
    
    def cubeFriend(objName):
        if 'cube' in objName.lower():
            menuItem(l='I love being a cube!')
        else:
            menuItem(l='Dang, I wish I was a cube', sm=True)
            menuItem(l='But I still keep it real', c=Callback(showMessage, 'True story'))
            menuItem(l='But I could become a cube if I really wanted to', c=Callback(showMessage, "Mighty Morphin' Targets!"))
            setParent('..', m=True)
            
    mayaHooks.override.dagMenuProc.customDagMenu(cubeFriend)

'''

from __future__ import absolute_import, division, print_function

from .baseOverride import baseOverride, insertLine, CustomCallbacks


if 'customDagMenu' not in globals():
    customDagMenu = CustomCallbacks('object')


def enable():
    global customDagMenu

    with baseOverride('dagMenuProc.mel', source=True) as (filename, overrideFilename):

        if filename:
            insertLine(
                filename,
                overrideFilename,
                '"m_dagMenuProc.kSelect"',
                [ customDagMenu.callString(indent=3) ],
                lineOffset=0
            )
