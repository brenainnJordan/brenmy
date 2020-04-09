"""Script to be run inside maya to add python sources
"""

import sys
import os

REPO_DIR = r"D:\Repos"

src_dirs = [
	os.path.join(REPO_DIR, r"brenpy\python"),
    os.path.join(REPO_DIR, r"brenmy\python"),
    os.path.join(REPO_DIR, r"brenfbxpy\python"),
    os.path.join(REPO_DIR, r"brenfbxdccpy\python"),
	r"D:\Dev\maya\numpy\numpy-1.13.1+mkl-cp27-none-win_amd64"
]

for src_dir in src_dirs:
    if src_dir not in sys.path:
        sys.path.append(src_dir)
        print "Src added: {}".format(src_dir)
