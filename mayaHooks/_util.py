from __future__ import absolute_import, print_function

import os
import sys
import traceback

from maya.cmds import about, setParent


def version(includeBitVersion=False):
    ''' Returns the year, and optionally a tuple of (year, bit)
    '''
    
    year = int(about(v=True)[:4])
    
    if includeBitVersion:
        return (int(year), 64 if about(v=True).count('x64') else 32  )
    else:
        return int(year)
        
        
def getCallableAsStr(callable):
    ''' Given a function or class, returns the string name.  This allows for reloading since the name will be the same
    '''
    return callable.__module__ + '.' + callable.__name__
    
     
def menuWrapper(callable):
    ''' Wrapper to ensure the parent menu is restored, so any menu making sub menus doesn't accidentally affect others.
    '''
    
    parentMenu = setParent(m=True, q=True)
    
    def wrapped(*args, **kwargs):
        return callable(*args, **kwargs)
        
    parentMenu = setParent(parentMenu, m=True)
    
    
def nicePath(path):
    ''' Returns a consistent path string for correct comparisons. '''
    return os.path.normcase( os.path.normpath(path) )
    
    
def runFile(path):
    ''' Runs the code in the given file in the __main__ namespace.  Used to dynamically run userSetups for dev installs.
    '''
    
    try:
        with open(path, 'r') as fid:
            compiledCode = compile(fid.read(), path, 'exec')
            exec(compiledCode, vars(sys.modules['__main__']), vars(sys.modules['__main__']))

    except Exception:
        print(traceback.format_exc())