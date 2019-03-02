'''
Created on 25 Aug 2018

@author: Bren
'''

from maya import cmds, mel


def get_skin_cluster(mesh):
    """Find skin cluster on mesh

    :TODO pythonize
    C:/Program Files/Autodesk/Maya2018/scripts/others/findRelatedSkinCluster.mel
    findRelatedSkinCluster
    """
    skin_cluster = mel.eval("findRelatedSkinCluster " + mesh)
    return skin_cluster
