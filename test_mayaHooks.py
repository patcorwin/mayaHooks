import os

from pymel.core import textScrollList

import mayaHooks.userSetup_setup



targetText1 = '''# BEGIN_MAYA_HOOKS <test>
import this
# END_MAYA_HOOKS
'''

targetText2 = '''# BEGIN_MAYA_HOOKS <test>
1 + 2 + 3
# END_MAYA_HOOKS
'''

targetText3 = '''# BEGIN_MAYA_HOOKS <test>
1 + 2 + 3
# END_MAYA_HOOKS
# BEGIN_MAYA_HOOKS <test>
import this
# END_MAYA_HOOKS
'''


def test_create_then_edit():

    win = mayaHooks.userSetup_setup.ManageUserSetup('import this', '<test>')

    choices = textScrollList(win.choices, q=True, ai=True)

    assert choices[1].endswith( mayaHooks.userSetup_setup.HAS_FILE_TEXT ) is False, 'First choice must be empty to run this test.'


    def readUserSetup():
        with open(choices[1] + '/userSetup.py', 'r') as fid:
            return fid.read()


    #textScrollList(win.choices, e=True, sii=2)
    
    win.createUserSetup(choices[1])

    fileName = choices[1] + '/userSetup.py'
    assert os.path.exists( fileName )
    
    assert readUserSetup() == targetText1
    
    win = mayaHooks.userSetup_setup.ManageUserSetup('1 + 2 + 3', '<test>')
    
    assert readUserSetup() == targetText2
    
    win = mayaHooks.userSetup_setup.ManageUserSetup('import this', '<test 2>')

    win.editUserSetup(choices[1] + '/userSetup.py')
    
    assert readUserSetup() == targetText3