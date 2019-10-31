# mayaHooks

1) Manage installation of python code and 2) easily extend internal maya functionality.


1. As of Maya 2019, pip isn't support without a lot of effort.  Additionally
any compiled pip packages are unlikely to work (ex numpy scipy).  Since Maya is
really it's own ecosystem, this lets you easily install pure python packages.

2. Lots of Maya functionality is customizable because it is in mel script, but
doing so can be a real pain.

This aims to be a non-destructive way to customize these scripts, allowing for
distribution to people with unknown setups.

## How to Use It

The Easy Way - Download mayaHooksInstaller.mel and drag it into Maya.  This
is self contained and will extract itself to the right place, letting you run
the following python commands to open the gui

```
import mayaHooks
mayaHooks.main()
```

The Not As Easy Way - Download the source code.  The `mayaHooks` folder that
contains `__init__.py` needs to be placed in a folder where Maya searches for
scripts.

### For Developers

#### Creating Valid Python Package

1. It needs to be a package (for now) aka a folder with an `__init__.py`
2. Adjacent to the package needs to be `info.json`
    * `"utc_build_time"` is the only required key, and should be a `str(datetime.utcnow())`
    of when the package was built
    * See the example on how to provide a shelf item.  Currently it's up to you
    to manage placing images somewhere, or adding a new folder to the image search path
3. Optionally create `userSetup_setup.py` to have code that run on maya startup

```
{
    "utc_build_time": "2019-10-07 04:16:04.434000",
    "shelf_items": [
        {
            "command": "import mayaHooks.gui\nmayaHooks.gui.Gui()",
            "image": "",
            "annotation": "Hooks"
        }
    ]
}
```

You can then:

* Select the info.json and package folder and make a zip file
* Upload it to github


#### To hook into Maya's dag menu (right clicking in object mode)
    
Here is an example of a hook (you can run this in the script editor and it will
only be active for this session.

In a python tab of the script editor, run


```
import mayaHooks.dagMenuProc
mayaHooks.dagMenuProc.overrideDagMenuProc()

from pymel.core import Callback, menuItem, setParent

def showMessage(msg):
    print( msg )

def cubeFriend(objName):
    if 'cube' in objName.lower():
        menuItem(l='I love being a cube!')
    else:
        menuItem(l='Dang, I wish I was a cube', sm=True)
        menuItem(l='But I still keep it real', c=Callback(showMessage, 'True story'))
        menuItem(l='But I could become a cube if I really wanted to', c=Callback(showMessage, "Mighty Morphin' Targets!"))
        setParent('..', m=True)
    

mayaHooks.dagMenuProc.registerMenu(cubeFriend)
```

This will make it so right clicking anything with `cube` in the name will add
one menuItem, otherwise different menuItems are added.