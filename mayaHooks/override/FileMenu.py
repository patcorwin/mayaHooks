'''
Provides access to when an existin file is about to be saved.
The most useful thing is probably to tell source control to edit the file.

This can ONLY be run in userSetup since runs at startup.

    import mayaHooks.override.FileMenu
    import mayaHooks.override.FileMenu.enable()


    def editFile( filename ):
        # Tell souce control to edit the file
        pass

    import mayaHooks.override.FileMenu.existingSave.register(editFile)

'''
from __future__ import absolute_import, division, print_function

from .baseOverride import baseOverride, insertLine, CustomCallbacks


if 'existingSave' not in globals():
    existingSave = CustomCallbacks('sceneName')


def enable():
    global existingSave

    with baseOverride('FileMenu.mel', source=False) as (filename, overrideFilename):

        if filename:
            insertLine(
                filename,
                overrideFilename,
                "} else if ((`file -q -mf`) || (`file -q -ex` == 0)) {",
                [existingSave.callString(indent=2)],
                lineOffset=1
            )
