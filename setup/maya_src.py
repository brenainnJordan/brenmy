"""Script to be run inside maya to add python sources
"""
import sys
import os

import fbx
from maya import cmds

REPO_DIR = r"D:\Repos"

src_dirs = [
	os.path.join(REPO_DIR, r"brenpy\python"),
    os.path.join(REPO_DIR, r"brenmy\python"),
    os.path.join(REPO_DIR, r"brenmy\sandbox\python\scripts"),
    os.path.join(REPO_DIR, r"brenfbxpy\python"),
    os.path.join(REPO_DIR, r"brenfbxdccpy\python"),
    os.path.join(REPO_DIR, r"brenrig\python"),
	r"D:\Dev\maya\numpy\numpy-1.13.1+mkl-cp27-none-win_amd64"
]

for src_dir in src_dirs:
    if src_dir not in sys.path:
        sys.path.append(src_dir)
        print "Src added: {}".format(src_dir)

# instance global fbx manager if it doesn't exist
global FBX_MANAGER

if "FBX_MANAGER" not in globals():
    cmds.warning("creating new FbxManager")
    FBX_MANAGER = fbx.FbxManager.Create()
else:
    print "global FBX_MANAGER found: {}".format(FBX_MANAGER)
