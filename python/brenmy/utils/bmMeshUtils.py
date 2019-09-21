"""Stuff
"""

from maya import cmds
from maya.api import OpenMaya


def get_selected_point_positions():
    # get selection
    sel = OpenMaya.MGlobal.getActiveSelectionList()

    if sel.length() == 0:
        raise Exception("Nothing selected!")

    dag, comp_obj = sel.getComponent(0)

    if comp_obj.isNull():
        raise Exception("No component selected!")

    comp_fn = OpenMaya.MFnSingleIndexedComponent(
        comp_obj
    )

#     print comp_fn.isEmpty

    if comp_fn.componentType != OpenMaya.MFn.kMeshVertComponent:
        raise Exception("Please select some vertices!")

    vertex_indices = comp_fn.getElements()

    print vertex_indices
