from __future__ import absolute_import, division, print_function

from .baseOverride import baseOverride, buildCallStr, insertLine, CustomCallbacks


def enable():
    '''
    Builds `<TARGET>.<maya version#>.mel` if it doesn't exist.
    '''

    with baseOverride('incrementalSaveScene.mel', source=True) as (filename, overrideFilename):
        if filename:
            line = buildCallStr(2, onSave, 'incrementDirPath newVersionString sceneToMove')
            insertLine(
                filename,
                overrideFilename,
                "evalEcho ($cmd);",
                [
                    '\tif ($movedSceneFile) {',
                    line,
                    '\t}'
                ],
                lineOffset=1
            )


if '_ON_SAVE' not in globals():
    _ON_SAVE = CustomCallbacks()


def onSave(incrementDirPath, newVersionString, sceneToMove):
    _ON_SAVE.run(incrementDirPath, newVersionString, sceneToMove)


def registerOnSave(func):
    _ON_SAVE.register(func)
    
    
def unregisterOnSave(func):
    _ON_SAVE.unregister(func)
