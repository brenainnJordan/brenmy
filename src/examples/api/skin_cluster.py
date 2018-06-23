'''
Created on 23 Jun 2018

@author: Bren

Maya API skinCluster example code.
Because we all need a little reminder every now and then...

'''


from maya.api import OpenMaya, OpenMayaAnim


def get_skin_cluster_weights(mesh, skin_cluster):

    sl = OpenMaya.MSelectionList()

    # get mesh dag path
    sl.add(mesh)
    mesh_dag = sl.getDagPath(0)

    # get skin
    sl.add(skin_cluster)
    m_skin = sl.getDependNode(1)

    # we just pass in an empty MObject to return all weights
    components = OpenMaya.MObject()

    # get weights
    m_skin = OpenMayaAnim.MFnSkinCluster(m_skin)
    weights, influence_count = m_skin.getWeights(mesh_dag, components)

    return weights
