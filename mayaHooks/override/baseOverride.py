'''
A safe, uninvasive way to alter base a maya scripts.  This is done by finding
the *.mel file, duplicating it with modifications and sourcing it instead.

Some files have to be sourced on load, like FileMenu.mel, so Maya must be
restarted for it to take affect.  You can simply not use the override to use
the stock Maya scripts.  Duplication also means adding new overrides is safe.

See any of the sibling py files for examples.
'''

from __future__ import absolute_import, division, print_function

from collections import OrderedDict
from contextlib import contextmanager
import inspect
import os
import re
import shutil
import traceback

from pymel.core import mel, warning

from .. import _util as util

try:
    basestring # noqa
except Exception:
    basestring = str


def Q(s):
    # Helper to quote mel vars
    return """'" + ${} + "'""".format(s)


def NQ(s):
    # Helper for not quoted mel vars
    return '" + ${} + "'.format(s)


def autoQ(s):
    if s.startswith('NQ:'):
        return NQ(s[3:])
    else:
        return Q(s.split(':')[-1])


TEMPLATE = '''{}python("try:{}\\nexcept Exception:import traceback;print(traceback.format_exc())");'''
NO_CATCH = '''python("{}");'''


def buildCallStr(indent, func, args, autoCatch=True):
    '''
    Args:
        indent: # of tab indentations
        func: Generally, a CustomCallback() instance
        args: Like namedtuple, a SINGLE string of space delimited attributes
        autoCatch: If True (default), wrap in try/except clause
    '''

    if inspect.isfunction(func):
        # Not sure this is actually needed
        name = func.__module__ + '.' + func.__name__
        
    elif isinstance(func, basestring):
        # Simple way
        frame = inspect.currentframe()
        name = frame.f_back.f_globals['__name__'] + '.' + func
    
    else:
        
        frame = inspect.currentframe()
        
        for key, val in frame.f_back.f_globals.items():
            if val is func:
                name = frame.f_back.f_globals['__name__'] + '.' + key
                break
        else:
            raise Exception('{} was not found in {}, unable to `buildCallStr()`'.format(func, frame.f_back.f_globals['__name__']))
        
    
    s = name + '(' + ', '.join( [autoQ(name) for name in args.split()] ) + ')'
    
    if autoCatch:
        return TEMPLATE.format( '\t' * indent, s )
    else:
        return NO_CATCH.format( s )


def findMelTarget(target):
    ''' Given a `target` like "FileMenu.mel", returns the full path to the file on `maya_script_path`.
    '''
    targetLowered = target.lower()
    
    for path in os.environ['maya_script_path'].split(';'):
        if not os.path.isdir(path):
            continue
        
        for f in os.listdir(path):
            if f.lower() == targetLowered:
                return path + '/' + f
    
    return ''


def getOverrideFolder():
    ''' Returns the folder to store overrides for this version of Maya. '''
    return os.path.dirname(os.path.dirname(__file__)).replace('\\', '/') + '/generated/' + str(util.version())


def clearAllOverrides():
    ''' Deletes all the overridden mel files.  Needed on updating mayaHooks so old overrides don't linger.'''
    folder = os.path.dirname( getOverrideFolder() )
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    for f in os.listdir(folder):
        if os.path.isdir(folder + '/' + f):
            shutil.rmtree(folder + '/' + f)


@contextmanager
def baseOverride(target, source):
    '''
    Builds `<target>.<maya version#>.mel` if it doesn't exist.
    
    Args:
        target: Simple mel filename, ex "FileMenu.mel"
        
    Yields:
        Tuple of (<source filepath>, <override filepath to make>)
        
    '''
    
    folder = getOverrideFolder()
    overrideFilename = folder + '/' + target
        
    if not os.path.exists(overrideFilename):
        if not os.path.exists(folder):
            os.makedirs(folder)

        filename = findMelTarget(target)
        
        if not filename:
            raise Exception( '{} not found so unable to create custom override'.format(target) )
        else:
            print('Making {} override'.format(target) )

            try:
                yield filename, overrideFilename

            except Exception:
                print('Error creating {} override'.format(target))
                print(traceback.format_exc())

    else:
        yield None, None
    
    print('Sourced override ' + overrideFilename)
    
    # Prepend so it supercedes the maya version
    if folder not in os.environ['maya_script_path']:
        os.environ['maya_script_path'] = folder + ';' + os.environ['maya_script_path']
    mel.rehash()
    
    if source:
        mel.source(overrideFilename)
        #mel.source(target.split('.')[0] )  # Strip off the extension


def insertLine(filename, overrideFilename, targetLine, newCode, lineOffset=0):
    '''
    Convenience function to insert `newCode` when `targetLine` is found.
    '''

    insertLines(filename, overrideFilename, [[targetLine, newCode, lineOffset]])

    """
    with open(filename, 'r') as fid:
        lines = fid.readlines()
    
    newline = re.search('[\r\n]+$', lines[0]).group(0)
    
    for i, line in enumerate(lines):
        if targetLine in line:
            index = i + lineOffset
            lines[index:index] = [s + newline for s in newCode]
            break

    with open(overrideFilename, 'w') as fid:
        fid.write( ''.join(lines) )
    """


def insertLines(filename, overrideFilename, edits):
    '''
    The most common edit is to identify a location and insert code near it.
    `edits` is a list of [targetLine, [newCode], lineOffset].  See gameFbxExporter for an example.

    targetLine is a string to search for, make sure it's unique within the file, this only
    replaces the first occurrence

    newCode is a list of strings, each element a line WITHOUT a newline, that will be added in.

    lineOffset is an in, 0 will insert the newCode above the the targetLine, 1 to follow after,
    2 will be two lines below etc.
    

    '''
    with open(filename, 'r') as fid:
        lines = fid.readlines()
    
    newline = re.search('[\r\n]+$', lines[0]).group(0)
    
    for targetLine, newCode, lineOffset in edits:
        for i, line in enumerate(lines):
            if targetLine in line:
                index = i + lineOffset
                lines[index:index] = [s + newline for s in newCode]
                break

    with open(overrideFilename, 'w') as fid:
        fid.write( ''.join(lines) )



class CustomCallbacks(object):
    
    def __init__(self, *args):
        self.args = args
        self.callbacks = OrderedDict()
    
    
    def register(self, callback):
        funcName = util.getCallableAsStr(callback)
    
        self.callbacks[funcName] = callback
    
    
    def unregister(self, callback):
        self.callbacks.pop( util.getCallableAsStr(callback), None )
    
    
    def __call__(self, *args):
        returnVal = None
        for name, func in self.callbacks.items():
            try:
                returnVal = func(*args)
            except Exception as ex:
                print(ex)
                warning('Error in function {}'.format(name) )
                
        return returnVal


    def callString(self, indent=0, autoCatch=True):
        frame = inspect.currentframe()
        for key, val in frame.f_back.f_globals.items():
            if self == val:
                name = frame.f_back.f_globals['__name__'] + '.' + key
                break
        else:
            raise Exception('CustomCallbacks variable not found in globals')

        s = name + '(' + ', '.join( [autoQ(name) for name in self.args] ) + ')'
        
        if autoCatch:
            return TEMPLATE.format( '\t' * indent, s )
        else:
            return NO_CATCH.format( s )