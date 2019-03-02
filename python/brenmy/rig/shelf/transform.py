'''
Created on 26 Aug 2018

@author: Bren
'''

from maya import cmds


def align_transforms_to_last():
    """Align selected Transforms to last selected Transform

    Gets and sets matrices in worldSpace
    """

    sl = cmds.ls(sl=True, type="transform")
    matrix = cmds.xform(sl[-1], query=True, matrix=True, worldSpace=True)
    for i in sl[:-1]:
        cmds.xform(i, matrix=matrix, worldSpace=True)
