# mayaHooks

Lots of Maya functionality is customizable becuase it is in mel script, but
doing so can be a real pain.

This aims to be a non-destructive way to customize these scripts, allowing for
distribution to people with unknown setups.

## How to Use It

This can be used to package up libraries for distribution and/or hooking into
some facet of Maya.


### To hook into Maya's dag menu (right clicking in object mode)
    
Here is an example of a hook (you can run this in the script editor and it will
only be active for this session.

Place the mayaHooks folder somewhere that Maya searches for scripts, often
somewhere like `<your user folder>\Documents\maya\scripts`.

In a python tab of the script editor, run:

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

This will make it so right cliking anything with `cube` in the name will add
one menuItem, otherwise different menuItems are added.

### To distribute code

See the `installFromZip`