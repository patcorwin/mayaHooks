'''
Provides an easy hook for appening menus to the dag right click menu.

But is it safe?  Will I bork maya?  Nope!  This does not alter existing maya files
but does tricker described later if you're interesting in the details.


Usage:

Put mayaHooks anywhere that python scripts are found.

In userSetup.py, add the lines:

    import mayaHooks.dagMenuProc
    mayaHooks.dagMenuProc.overrideDagMenuProc()

    import <your_python>
    
    mayaHooks.dagMenuProc.registerMenu( <your_python>.<your_menu_function> )


An example of a hook (you can run this in the script editor and it will only be active for this session):

    import mayaHooks.dagMenuProc
    mayaHooks.dagMenuProc.overrideDagMenuProc()
    
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
        
    
    mayaHooks.dagMenuProc.registerMenu(cubeFriend)


How does this work?  dagMenuProc.mel is called to build the right click menu when an object is selected.
`overrideDagMenuProc()` finds it, duplicates it, inserts a small bit of python, and sources this new file so stock
maya is unaltered.

'''
from __future__ import print_function, absolute_import

from collections import OrderedDict

import os
import re

from pymel.core import mel, warning


from . import _util as util


# Create the variable this way so not clear it during reloads during development.
if '_menus' not in globals():
    _menus = OrderedDict()


def overrideDagMenuProc():
    '''
    Builds `dagMenuProc.<maya version#>.mel` in this folder if it doesn't exist.
    
    '''
    folder = os.path.dirname(__file__).replace('\\', '/') + '/' + str(util.version())
    overrideFilename = folder + '/dagMenuProc.mel'
        
    if not os.path.exists(overrideFilename):
        if not os.path.exists(folder):
            os.makedirs(folder)

        filename = find_dagMenuProcMel()
        
        if not filename:
            warning( 'dagMenuProc.mel not found so unable to create custom override' )
            return
        else:
            print('Making dagMenuProc.mel override')

            with open(filename, 'r') as fid:
                lines = fid.readlines()
            
            newline = re.search('[\r\n]+$', lines[0]).group(0)
            
            for i, line in enumerate(lines):
                if '"m_dagMenuProc.kSelect"' in line:
                    lines[i:i] = ['''            python("try:mayaHooks.dagMenuProc.customMenu('" + $object + "')\\nexcept Exception as ex:print(ex)");''' + newline]
                    break
            
            with open(overrideFilename, 'w') as fid:
                fid.write( ''.join(lines) )
    
    print('Sourced override ' + overrideFilename)
    
    # Prepend so it supercedes maya's dagMenuProc
    if folder not in os.environ['maya_script_path']:
        os.environ['maya_script_path'] = folder + ';' + os.environ['maya_script_path']
    mel.rehash()
    mel.source(overrideFilename)
    mel.source('dagMenuProc')


def registerMenu(createMenu):
    '''
    `createMenu(str objName)` will be called during dag menu creation.
    '''
    
    funcName = util.getCallableAsStr(createMenu)
    
    _menus[funcName] = createMenu


def unregisterMenu(createMenu):
    _menus.pop( util.getCallableAsStr(createMenu), None )


def customMenu(objectName):
    for name, func in _menus.items():
        try:
            func(objectName)
        except Exception as ex:
            print(ex)
            warning('Error in function {}'.format(name) )
        
    
def find_dagMenuProcMel():
    for path in os.environ['maya_script_path'].split(';'):
        if not os.path.isdir(path):
            continue
        
        for f in os.listdir(path):
            if f.lower() == 'dagmenuproc.mel':
                return path + '/' + f
    
    return ''


''' Excerpt from 2017 version, search for the >>>> uiRes call and insert a line above it
            // label the object
            string $shortName = `substitute ".*|" $object ""`;
            menuItem -label ($shortName + "...") -c ("showEditor "+$object);
            menuItem -divider true;
            menuItem -divider true;

            // Create the list of selection masks
            createSelectMenuItems($parent, $object);

            menuItem -d true;
        
>>>>        menuItem -label (uiRes("m_dagMenuProc.kSelect"))  -c ("select -r " + $object);
            menuItem -version "2014" -label (uiRes("m_dagMenuProc.kSelectAll"))  -c ("SelectAll");
            menuItem -version "2014" -label (uiRes("m_dagMenuProc.kDeselect"))  -c ("SelectNone;");
            menuItem -label (uiRes("m_dagMenuProc.kSelectHierarchy"))  -c ("select -hierarchy " + $object);
            menuItem -version "2014" -label (uiRes("m_dagMenuProc.kInverseSelection"))  -c ("InvertSelection");
            string $container = `container -q -fc $object`;
            if( $container != "" ){
'''