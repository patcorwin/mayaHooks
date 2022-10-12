'''
Utility to help identify and create, add or edit code to userSetup.py

Usage:

Call `ManageUserSetup('code to insert', 'identifying key')`

A gui will ask where to create/edit userSetup.py  The given code will be wrapped
in with comments, and the `key`, like so:

`ManageUserSetup('from pymel.core import *', 'allPymel')`

produces

```
# BEGIN_MAYA_HOOKS allPymel
from pymel.core import *
# END_MAYA_HOOKS
```

'''

from __future__ import absolute_import, division, print_function

from functools import partial
import itertools
import os
import re
import sys


from maya.cmds import about, button, columnLayout, confirmDialog, deleteUI, text, textScrollList, showWindow, window

from ._util import nicePath, ENV_SEP


BEGIN_HOOK = '# BEGIN_MAYA_HOOKS'
END_HOOK = '# END_MAYA_HOOKS'

HAS_FILE_TEXT = '   (has userSetup.py)'

__all__ = ['ManageUserSetup']


def begin_hook_text(key):
    return BEGIN_HOOK + ' ' + key


def discoverPythonPaths():
    ''' Returns a list of paths, that exist, where maya searches for python code. '''
    sys_path = { nicePath(p): p for p in sys.path if os.path.exists(p) }
    
    maya_script_path = { nicePath(p): p for p in os.environ['MAYA_SCRIPT_PATH'].split(ENV_SEP) if os.path.exists(p) }
    
    shared = set(sys_path).intersection(maya_script_path)
    
    return [maya_script_path[p] for p in shared ]
       
        
class ManageUserSetup(object):
    ''' Main entry point for creating or editing a userSetup.py file
    
    Args:
        newText: The code to be inserted
        key: A string used to identify that block to make editing possible.
        silentUpdate: If true, existing userSetups are scanned an the firest one
            matching the key is edited
    
    '''
    TITLE = 'ManageUserSetup'
    
    def __init__(self, newText, key, silentUpdate=True):
        ''' See class docstring '''
        self.text = BEGIN_HOOK + ' ' + key + '\n' + newText + '\n' + END_HOOK + '\n'
        self.key = key
        
        paths = discoverPythonPaths()
        
        paths.sort()
        
        ideal       = ['Ideal -------']
        notIdeal    = ['Not Ideal ---']
        maybe       = ['Maybe -------']
        
        '''
        If I can determine these, I can also have an easy mode for all maya's or just this year
        ideal c:/MAYA_APP_DIR/2019/scripts
        ideal c:/MAYA_APP_DIR/scripts
        
        c:/MAYA_APP_DIR/2019/prefs/scripts
        '''
        
        
        best = '/' + about(q=True, v=True) + '/scripts'
        
        for path in paths:
            path_lowered = path.lower()
            if ('plug-ins' in path
                or 'allegorithmic' in path_lowered
                or 'solidangle' in path_lowered
                or 'bifrost' in path_lowered):
                notIdeal.append( path )
                
            elif path.endswith(best):
                ideal.append(path)
                
            else:
                if 'users' in path.lower():
                    ideal.append(path)
                else:
                    maybe.append(path)
                
        exisingFiles = [path + '/userSetup.py' for path in paths if os.path.exists( path + '/userSetup.py' )]
        
        if silentUpdate:
            findSectionRE = re.compile(re.escape(begin_hook_text(key)))
            for f in exisingFiles:
                with open(f, 'r') as fid:
                    if findSectionRE.search(fid.read()):
                        self.editUserSetup(f)
                        return
        
        if window(self.TITLE, ex=True):
            deleteUI(self.TITLE)
                
        self.win = window(w=450)
        columnLayout(adj=True)
        text( l='The top paths are probably good for userSetup.py\n' +
                'userSetup.py gets run when maya start, and you can have several\n' +
                'obviously in different locations.')
        self.choices = textScrollList(nr=20)
        
        
        for path in itertools.chain(ideal, maybe, notIdeal):
            
            if path + '/userSetup.py' in exisingFiles:
                textScrollList(self.choices, e=True, append=path + HAS_FILE_TEXT )
            else:
                textScrollList(self.choices, e=True, append=path)
        
        #textScrollList(self.choices, selectIndexedItem=1)
                
        button(l='Add/Edit userSetup.py', c=partial(self.perform) )
        
        showWindow()


    def perform(self, *args):
        ''' Callback to actually create or edit a userSetup.py, performing the correct one.'''
        sel = textScrollList(self.choices, q=True, si=True)
        
        if not sel:
            return
        
        if sel[0].endswith(HAS_FILE_TEXT):
            filename = sel[0][:-len(HAS_FILE_TEXT)]
            self.editUserSetup(filename + '/userSetup.py')
        else:
            self.createUserSetup(sel[0])
        
        deleteUI(self.win)
        
        confirmDialog(m='Successfully installed!  Restart maya so your new userSetup takes effect.')


    def editUserSetup(self, fullpath):
        ''' Called by `perform` to edit an existing file.
        Args:
            fullpath: String path to userSetup.py, eg "C:/maya/2019/scripts/userSetup.py"
        '''
        
        modified = modifiedUserSetup(fullpath, self.key, self.text)
        
        if modified is False:
            confirmDialog(m='Unable to find the right place to edit userSetup.py\n\nYou will need to manually edit it, see the script editor')
            print( 'Make sure the `# BEGIN_MAYA_HOOKS...` and `# END_MAYA_HOOKS` blocks match.  Paste in the following code:' )
            print( self.text )
            return
        else:
            with open(fullpath, 'w') as fid:
                fid.write( ''.join(lines) )
        '''
        with open(fullpath, 'r') as fid:
            lines = fid.readlines()
        
        start = None
        end = None
        beginLine = begin_hook_text(self.key)
        for i, line in enumerate(lines):
            print(line, 'LLLIINNE', start is not None and line.startswith( END_HOOK ), (start is not None), line.startswith( END_HOOK ))
            if line.startswith(beginLine):
                start = i
            elif start is not None and line.startswith( END_HOOK ):
                end = i + 1
                break

        # A start and end tag were found so replace the code.
        if start is not None and end is not None:
            lines[start:end] = self.text.splitlines(True)
        
        # No blocks were found so append the code to the end of the file.
        elif start is None and end is None:
            lines += self.text.splitlines(True)
        
        # A start was found but no end so don't do anything to prevent accidental code deletion.
        else:
            confirmDialog(m='Unable to find the right place to edit userSetup.py\n\nYou will need to manually edit it, see the script editor')
            print( 'Make sure the `# BEGIN_MAYA_HOOKS...` and `# END_MAYA_HOOKS` blocks match.  Paste in the following code:' )
            print( self.text )
            return
        
        with open(fullpath, 'w') as fid:
            fid.write( ''.join(lines) )
        '''

    
    def createUserSetup(self, path):
        ''' Called by `perform` to create a userSetup.
        Args:
            path: Directory to place userSetup.py
        '''
        with open(path + '/userSetup.py', 'w') as fid:
            fid.write( self.text )


def modifiedUserSetup(fullpath_or_text, key, newText):
    ''' If successful, returns the text for a modified userSetup.py
    Args:
        fullpath: String path to userSetup.py, eg "C:/maya/2019/scripts/userSetup.py"
        key: The maya hooks key
        newTest: Block of text to insert into the file or `None` to clear the entry, if it exists.
    '''
    if os.path.exists(fullpath_or_text):
        with open(fullpath_or_text, 'r') as fid:
            lines = fid.readlines()
    else:
        lines = fullpath_or_text.splitlines(True)
    
    startRE = re.compile( '^' + BEGIN_HOOK + ' ' + key + r'\s*', flags=re.I )
    endRE = re.compile( '^' + END_HOOK + r'\s*$', flags=re.I )
    
    start = None
    end = None
    
    if newText is not None:
        newLines = (BEGIN_HOOK + ' ' + key + '\n' + newText + '\n' + END_HOOK + '\n').splitlines(True)
    else:
        newLines = []

    for i, line in enumerate(lines):
        if startRE.search(line):
            start = i
        elif start is not None and endRE.search(line):
            end = i + 1
            break

    # A start and end tag were found so replace the code.
    if start is not None and end is not None:
        lines[start:end] = newLines
    
    # No blocks were found so append the code to the end of the file.
    elif start is None and end is None:
        if newText is not None:
            lines += ['\n'] + newLines
    
    # A start was found but no end so don't do anything to prevent accidental code deletion.
    else:
        #confirmDialog(m='Unable to find the right place to edit userSetup.py\n\nYou will need to manually edit it, see the script editor')
        #print( 'Make sure the `# BEGIN_MAYA_HOOKS...` and `# END_MAYA_HOOKS` blocks match.  Paste in the following code:' )
        #print( self.text )
        return False
    
    return ''.join(lines)