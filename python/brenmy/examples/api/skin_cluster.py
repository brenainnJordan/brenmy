'''
Created on 23 Jun 2018

@author: Bren

Maya API skinCluster example code.
Because we all need a little reminder every now and then...


docs:
http://help.autodesk.com/view/MAYAUL/2018/ENU/?guid=__py_ref_index_html

'''


from maya.api import OpenMaya, OpenMayaAnim


def get_skin_cluster_weights(mesh, skin_cluster):

    sl = OpenMaya.MSelectionList()

    # get mesh dag path
    sl.add(mesh)
    mesh_dag = sl.getDagPath(0)

    # get skin
    sl.add(skin_cluster)
    mfn_skin = sl.getDependNode(1)

    # we just pass in an empty MObject to return all weights
    components = OpenMaya.MObject()

    # get weights
    mfn_skin = OpenMayaAnim.MFnSkinCluster(mfn_skin)
    weights, influence_count = mfn_skin.getWeights(mesh_dag, components)

    return weights


def flood_skin_cluster_influence_weights(mesh, skin_cluster, influence, weight):
    """
    TODO/wip
    """
    sl = OpenMaya.MSelectionList()

    sl.add(mesh)
    sl.add(skin_cluster)

    mesh_dag = sl.getDagPath(0)
    m_skin = sl.getDependNode(1)
    mfn_skin = OpenMayaAnim.MFnSkinCluster(m_skin)

    component = OpenMaya.MFnSingleIndexedComponent().create(OpenMaya.MFn.kMeshVertexComponent)

    # TODO find this
    influence_index = 0

    mfn_skin.setWeights(mesh_dag, component, influence_index, weight)

    return True
