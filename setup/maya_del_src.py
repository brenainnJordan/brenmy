"""Script to be run in Maya to delete any loaded modules from python sources
"""

import sys
import os

REPO_DIR = r"D:\Repos"

SRC_DIRS = [
	os.path.join(REPO_DIR, r"brenpy\python"),
    os.path.join(REPO_DIR, r"brenmy\python"),
    os.path.join(REPO_DIR, r"brenfbxpy\python"),
    os.path.join(REPO_DIR, r"brenfbxdccpy\python"),
]

def is_src(filepath):
    for src_dir in SRC_DIRS:
        if filepath.startswith(src_dir):
            return True

    return False

def delete_src_modules():
    for module_name in sys.modules.keys():
        if module_name in sys.builtin_module_names:
            continue

        module = sys.modules[module_name]

        if module is None:
            continue

        try:
            module_filepath = module.__file__

            if is_src(module_filepath):
                print "Removing module: {}".format(module_name)
                del sys.modules[module_name]

        except AttributeError:
            continue
            # print "failed to get file: {}".format(module_name)

# call
delete_src_modules()

# remove from src
for src_dir in SRC_DIRS:
    if src_dir in sys.path:
        sys.path.remove(src_dir)
        print "Src removed: {}".format(src_dir)
