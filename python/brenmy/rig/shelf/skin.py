'''
Created on 25 Aug 2018

@author: Bren
'''


from maya import cmds

from ..utils.skin import get_skin_cluster


def select_skinned_joints():
    """Get selected mesh and select skinned joints

    :TODO get_selected_mesh
    """

    mesh = cmds.ls(sl=True)[0]
    if mesh is None:
        return

    skin_cluster = get_skin_cluster(mesh)
    if not skin_cluster:
        return

    influences = cmds.skinCluster(skin_cluster, query=True, influence=True)
    joints = cmds.ls(influences, type="joint")
    cmds.select(joints)

    return
