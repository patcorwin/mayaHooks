from __future__ import absolute_import, division, print_function

from .baseOverride import baseOverride, buildCallStr, insertLine, CustomCallbacks


def enable():
    '''
    Builds `<TARGET>.<maya version#>.mel` if it doesn't exist.
    '''

    #line = '''\t\tpython("try:mayaHooks.override.FileMenu.existingSave('" + $sceneName + "')\\nexcept Exception as ex:print(ex)");'''
    with baseOverride('FileMenu.mel', source=False) as (filename, overrideFilename):

        if filename:
            line = buildCallStr(2, existingSave, 'sceneName')
            insertLine(
                filename,
                overrideFilename,
                "} else if ((`file -q -mf`) || (`file -q -ex` == 0)) {",
                [line],
                lineOffset=1
            )


if '_EXISTING_SAVE' not in globals():
    _EXISTING_SAVE = CustomCallbacks()


def existingSave(filename):
    _EXISTING_SAVE.run(filename)


def registerExistingSave(func):
    _EXISTING_SAVE.register(func)
    
    
def unregisterExistingSave(func):
    _EXISTING_SAVE.unregister(func)
