'''
Created on 26 May 2019

@author: Bren
'''

import numpy

from maya import cmds, mel
from maya.api import OpenMaya, OpenMayaAnim


def get_skin_cluster(mesh):
    """Find skin cluster on mesh

    :TODO pythonize
    C:/Program Files/Autodesk/Maya2018/scripts/others/findRelatedSkinCluster.mel
    findRelatedSkinCluster
    """
    skin_cluster = mel.eval("findRelatedSkinCluster " + mesh)
    return skin_cluster


def get_skin_cluster_weights(mesh, skin_cluster):
    """Get skin cluster weights via MFnSkinCluster.

    TODO check that mesh is deformed by skin cluster.
    TODO options for selective influences.

    Weights are returned as a list of lists, one per influence,
    containing weights for all points.

    """
    sl = OpenMaya.MSelectionList()

    # get objects
    sl.add(mesh)
    mesh_dag = sl.getDagPath(0)

    sl.add(skin_cluster)
    m_skin = sl.getDependNode(1)

    # we just pass in an empty MObject to return all weights
    components = OpenMaya.MObject()

    # get weights
    m_skin = OpenMayaAnim.MFnSkinCluster(m_skin)
    weights, influence_count = m_skin.getWeights(mesh_dag, components)

    # slice weights per influence
#     mesh_fn = OpenMaya.MFnMesh(mesh_dag)
#     point_count = mesh_fn.numFaceVertices

    weights = list(weights)

    sliced_weights = [
        weights[i::influence_count]
        for i in range(influence_count)
    ]

    return sliced_weights


def set_skin_cluster_weights(mesh, skin_cluster, weights):
    """Set all weights on skin cluster via MFnSkinCluster.

    Weights should be in same form as returned by
    get_skin_cluster_weights.

    TODO options for selective influences.
    TODO options for selective components.

    """
    sl = OpenMaya.MSelectionList()

    # get mesh dag path
    sl.add(mesh)
    mesh_dag = sl.getDagPath(0)

    # get skin
    sl.add(skin_cluster)
    m_skin = sl.getDependNode(1)

    # restructure weights to match form expected by MFnSkinCluster
    n_weights = numpy.array(weights)
    flat_weights = n_weights.transpose().flatten().tolist()
    weights = OpenMaya.MDoubleArray(flat_weights)

    if True:
        # construct component object for all verts
        # TODO perform on specific components?!?
        mesh_fn = OpenMaya.MFnMesh(mesh_dag)
        point_count = mesh_fn.numVertices

        component = OpenMaya.MFnSingleIndexedComponent()
        component.create(OpenMaya.MFn.kMeshVertComponent)
        component.addElements([i for i in range(point_count)])

        components = component.object()

    else:
        # or simply pass in an empty MObject to set all weights
        # note sometimes this doesn't work?!
        components = OpenMaya.MObject()

    # set weights
    m_skin = OpenMayaAnim.MFnSkinCluster(m_skin)

    influences = [
        m_skin.indexForInfluenceObject(i) for i in m_skin.influenceObjects()
    ]

    # influences must be passed in as a MIntArray
    # python list will throw an unhelpful error
    # Error: TypeError: file ...py line 116: an integer is required #

    influences = OpenMaya.MIntArray(influences)

    m_skin.setWeights(
        mesh_dag, components, influences, weights
    )

    return True
