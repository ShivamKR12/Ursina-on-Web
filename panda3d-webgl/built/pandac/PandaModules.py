
"This module is deprecated.  Import from panda3d.core and other panda3d.* modules instead."

if __debug__:
    print("Warning: pandac.PandaModules is deprecated, import from panda3d.core instead")

try:
    from panda3d.core import *
except ImportError as err:
    if "No module named core" not in str(err):
        raise
try:
    from panda3d.direct import *
except ImportError as err:
    if "No module named direct" not in str(err):
        raise

from direct.showbase import DConfig

def get_config_showbase():
    return DConfig

def get_config_express():
    return DConfig

getConfigShowbase = get_config_showbase
getConfigExpress = get_config_express
