from __future__ import absolute_import, division, print_function

from .baseOverride import baseOverride, insertLine, CustomCallbacks


def enable():
    global callback_onSave
    
    with baseOverride('incrementalSaveScene.mel', source=True) as (filename, overrideFilename):
        if filename:
            #line = buildCallStr(2, onSave, 'incrementDirPath newVersionString sceneToMove')
            #line = buildCallStr(2, onSave)
            insertLine(
                filename,
                overrideFilename,
                "evalEcho ($cmd);",
                [
                    '\tif ($movedSceneFile) {',
                    callback_onSave._callString(2),
                    '\t}'
                ],
                lineOffset=1
            )


if 'callback_onSave' not in globals():
    callback_onSave = CustomCallbacks('incrementDirPath', 'newVersionString', 'sceneToMove', enable=enable)