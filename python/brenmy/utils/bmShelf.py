import sys
import os
import shutil

from maya import mel
from maya import cmds

from brenmy.utils import bmEnv
from brenmy.setup import maya_src

MAYA_SHELF_DIR = os.path.join(
    bmEnv.MayaEnv.install_dir,
    "scripts",
    "shelves"
)

MAYA_PREFS_SHELF_DIR = os.path.join(
    bmEnv.MayaEnv.preferences_dir,
    "prefs",
    "shelves"
)

CUSTOM_SHELF_NAMES = [
    "shelfMan",
    "brenmy",
    "bmSkin",
    "bmJoints",
    "bmPy",
    "bmXform"
]

SRC_DIR = os.path.join(maya_src.REPO_DIR, "brenmy")

REPO_SHELVES_DIR = os.path.join(
    SRC_DIR,
    "shelves"
)


def snippets():
    cmds.shelfLayout("testShelf", exists=True)
    cmds.saveShelf("testShelf", r"D:\Repos\brenmy\shelves\testShelf")


class ShelfFile(object):
    """Custom object to manage shelf filepaths
    """

    def __init__(self, shelf_name):
        self._shelf_name = shelf_name

    def name(self):
        return self._shelf_name

    def filename(self):
        return "shelf_{}.mel".format(self._shelf_name)

    def maya_filepath(self, custom=True):
        if custom:
            return os.path.join(
                MAYA_PREFS_SHELF_DIR,
                self.filename()
            )
        else:
            return os.path.join(
                MAYA_SHELF_DIR,
                self.filename()
            )

    def repo_filepath(self):
        return os.path.join(
            REPO_SHELVES_DIR,
            self.filename()
        )

    def exists(self, repo=False, custom=True):
        if repo:
            return os.path.exists(self.repo_filepath())
        else:
            return os.path.exists(self.maya_filepath(custom=custom))


def export_shelf_to_repo(shelf_name):
    if not cmds.shelfLayout(shelf_name, exists=True):
        cmds.warning("Shelf not found: {}".format(shelf_name))
        return False

    # locate shelf file
    shelf_file = ShelfFile(shelf_name)

    if not shelf_file.exists(repo=False):
        cmds.warning(
            "Shelf file not found: {}".format(
                shelf_file.maya_filepath(custom=True)
            )
        )

        return False

    # copy to repo
    # TODO check repo file exists
    shutil.copyfile(
        shelf_file.maya_filepath(),
        shelf_file.repo_filepath(),
    )

    return True


def export_shelves_to_repo():
    for shelf_name in CUSTOM_SHELF_NAMES:
        res = export_shelf_to_repo(shelf_name)

        if res:
            print "Shelf exported: {}".format(shelf_name)
        else:
            print "[ WARNING ] Failed to export shelf: {}".format(shelf_name)

    return True


def load_shelf_from_repo(shelf_name):

    # delete if it already exists before loading
    while cmds.shelfLayout(shelf_name, exists=True):
        print "Shelf exists, deleting... {}".format(shelf_name)

        mel.eval("deleteShelfTab {}".format(shelf_name))

    # get filepath
    shelf_file = ShelfFile(shelf_name)

    if not shelf_file.exists(repo=True):
        cmds.warning(
            "Shelf file not found: {}".format(
                shelf_file.repo_filepath()
            )
        )

        return False

    mel_shelf_filepath = shelf_file.repo_filepath()
    mel_shelf_filepath = mel_shelf_filepath.replace("\\", "//")

    mel.eval('loadNewShelf "{}"'.format(mel_shelf_filepath))

    return True


def load_shelves_from_repo():
    for shelf_name in CUSTOM_SHELF_NAMES:
        res = load_shelf_from_repo(shelf_name)

        if res:
            print "Shelf loaded: {}".format(shelf_name)
        else:
            print "[ WARNING ] Failed to load shelf: {}".format(shelf_name)

    return True
