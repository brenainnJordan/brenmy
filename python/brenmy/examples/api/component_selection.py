from maya.api import OpenMaya


def mesh_edge_example():
    sel = OpenMaya.MGlobal.getActiveSelectionList()
    sel.length()

    dag, obj = sel.getComponent(0)

    print dag.partialPathName()

    #comp = OpenMaya.MFnComponent(obj)
    comp = OpenMaya.MFnSingleIndexedComponent(obj)

    print comp.componentType == OpenMaya.MFn.kMeshEdgeComponent
    # True

    comp.elementCount
    comp.getElements()

    it_edge = OpenMaya.MItMeshEdge(dag)
