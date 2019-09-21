"""
** WIP **
"""

import os
from maya import cmds


class MayaEnv():
    """Convenience methods to locate Maya environment variables
    """
    version = cmds.about(version=True)
    env_file = cmds.about(environmentFile=True)
    preferences_dir = cmds.about(preferences=True)
    install_dir = os.environ["MAYA_LOCATION"]
