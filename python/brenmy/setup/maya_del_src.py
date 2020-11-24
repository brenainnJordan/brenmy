"""Script to be run in Maya to delete any loaded modules from python sources
"""

import sys
import os

def get_repo_sources():
    if "BRENMY_REPO_SOURCES" not in globals():
        raise Exception("BRENMY_REPO_SOURCES global not found, cannot get repo sources")

    global BRENMY_REPO_SOURCES
    return BRENMY_REPO_SOURCES


def is_src(filepath):

    for src_dir in get_repo_sources():
        if os.path.commonprefix([src_dir, filepath]) == src_dir:
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

def remove_sources():
    for src_dir in get_repo_sources():
        if src_dir in sys.path:
            sys.path.remove(src_dir)
            print "Src removed: {}".format(src_dir)


if __name__ == "__main__":
    delete_src_modules()
    remove_sources()
