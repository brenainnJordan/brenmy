"""Script to be run inside maya to add python sources
"""

import sys
import os

from maya import cmds
from maya import mel

REPO_DIR = r"D:\Repos"

SRC_DIRS = [
    os.path.join(REPO_DIR, r"brenpy\python"),
    os.path.join(REPO_DIR, r"brenmy\python"),
    os.path.join(REPO_DIR, r"brenmy\sandbox\python\scripts"),
    os.path.join(REPO_DIR, r"brenfbxpy\python"),
    os.path.join(REPO_DIR, r"brenfbxdccpy\python"),
    os.path.join(REPO_DIR, r"brenrig\python"),
    r"D:\Dev\maya\numpy\numpy-1.13.1+mkl-cp27-none-win_amd64",
    r"D:\Dev\maya\fbx"
]

MEL_DIRS = [
    r"D:/Dev/sourced/comet"
]


def add_sources():
    """Add SRC_DIRS to sys.path
    """
    for src_dir in SRC_DIRS:
        if src_dir not in sys.path:
            sys.path.append(src_dir)
            print "Src added: {}".format(src_dir)


def instance_fbx_manager():
    """Instance global fbx manager if it doesn't exist
    """
    import fbx

    global FBX_MANAGER

    if "FBX_MANAGER" not in globals():
        cmds.warning("creating new FbxManager")
        FBX_MANAGER = fbx.FbxManager.Create()
    else:
        print "global FBX_MANAGER found: {}".format(FBX_MANAGER)


def add_mel_sources():
    maya_script_path = mel.eval('getenv "MAYA_SCRIPT_PATH"')

    for mel_dir in MEL_DIRS:
        maya_script_path += "{};".format(mel_dir.replace("\\", "/"))

    print "TEST", maya_script_path

    mel.eval('putenv "MAYA_SCRIPT_PATH" "{}"'.format(maya_script_path))
    mel.eval("rehash")


def initialize_mel_tools():
    mel.eval("source cometMenu.mel")


if __name__ == "__main__":
    add_sources()
    instance_fbx_manager()
    add_mel_sources()
    initialize_mel_tools()
