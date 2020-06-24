'''
`alterExportPath` lets you edit a path when exporting is called.
Probably the most useful things are making sure the file is writable and expanding env vars.


    def alterPath(directory)

    import mayaHook.override.gameFbxExporter

    mayaHook.override.gameFbxExporter.enable()
    mayaHook.override.gameFbxExporter.alterExportPath.register()

'''

from __future__ import absolute_import, division, print_function

from .baseOverride import baseOverride, insertLines, CustomCallbacks

'''
Since this alters the path, the least complicated thing is to take the last result.
Therefore, the last registered function is the one that actually will alter the path,
any preceding actions are effectively ignored.
'''
if 'alterExportPath' not in globals():
    alterExportPath = CustomCallbacks('dir')

if 'onExport' not in globals():
    onExport = CustomCallbacks('exportFilePath')


def enable():

    global alterExportPath
    global onExport

    with baseOverride('gameFbxExporter.mel', source=True) as (filename, overrideFilename):

        edits = [
            [
                'string $dir = `getAttr($gGameFbxExporterCurrentNode + ".exportPath")`;',
                ['\t$dir = ' + alterExportPath.callString(indent=0, autoCatch=False)],
                1
            ],
            [
                'if(catch(`FBXExport $exportSelectionFlag -file $exportFilePath`))',
                [onExport.callString(indent=1)],
                0
            ]
        ]

        if filename:
            insertLines(
                filename,
                overrideFilename,
                edits
            )
