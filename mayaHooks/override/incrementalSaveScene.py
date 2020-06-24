from __future__ import absolute_import, division, print_function

from .baseOverride import baseOverride, insertLine, CustomCallbacks


if 'onSave' not in globals():
    onSave = CustomCallbacks('incrementDirPath', 'newVersionString', 'sceneToMove')


def enable():

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
                    onSave.callString(2),
                    '\t}'
                ],
                lineOffset=1
            )
