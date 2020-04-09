"""Stuff
"""

import time
import numpy

from maya import cmds
from maya.api import OpenMaya


def get_component_selection():
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

    return dag, comp_fn


def get_selected_vertex_indices():
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

    return vertex_indices


def get_selected_vertex_positions(use_numpy=False, world_space=True):
    """
    Notes: initial testing suggests using numpy to filter points is actually slower!
    """

    dag, comp_fn = get_component_selection()

    if comp_fn.componentType != OpenMaya.MFn.kMeshVertComponent:
        raise Exception("Please select some vertices!")

    vertex_indices = comp_fn.getElements()

    points = []

    if world_space:
        space = OpenMaya.MSpace.kWorld
    else:
        space = OpenMaya.MSpace.kObject

    start_time = time.time()

    if use_numpy:
        mesh_fn = OpenMaya.MFnMesh(dag)
        all_points = mesh_fn.getPoints(space=space)
        points = numpy.array(all_points)[vertex_indices].tolist()

    else:
        vert_it = OpenMaya.MItMeshVertex(dag)

        for vertex_index in vertex_indices:
            vert_it.setIndex(vertex_index)

            points.append(
                vert_it.position(space=space)
            )

    end_time = time.time()

    print "Got points in {} seconds".format(end_time - start_time)

    return points


def get_selected_vertex_mean_position(use_numpy=False, world_space=True):
    """

    """

    dag, comp_fn = get_component_selection()

    if comp_fn.componentType != OpenMaya.MFn.kMeshVertComponent:
        raise Exception("Please select some vertices!")

    vertex_indices = comp_fn.getElements()

    if world_space:
        space = OpenMaya.MSpace.kWorld
    else:
        space = OpenMaya.MSpace.kObject

    start_time = time.time()

    if use_numpy:
        mesh_fn = OpenMaya.MFnMesh(dag)

        all_points = mesh_fn.getPoints(space=space)
        points = numpy.array(all_points)[vertex_indices]

        avg_point = points.mean(axis=0)

    else:
        vert_it = OpenMaya.MItMeshVertex(dag)

        point_sum = OpenMaya.MPoint()

        for vertex_index in vertex_indices:
            vert_it.setIndex(vertex_index)

            point_sum += vert_it.position(space=space)

        avg_point = point_sum / len(vertex_indices)

    end_time = time.time()

    print "Got mean point in {} seconds".format(end_time - start_time)

    return avg_point


def create_avg_locator():
    """

    """

    dag, comp_fn = get_component_selection()

    if comp_fn.componentType == OpenMaya.MFn.kMeshVertComponent:
        # get average vertex position

        vertex_indices = comp_fn.getElements()

        # get average point
        vert_it = OpenMaya.MItMeshVertex(dag)

        point_sum = OpenMaya.MPoint()

        for vertex_index in vertex_indices:
            vert_it.setIndex(vertex_index)

            point_sum += vert_it.position(space=OpenMaya.MSpace.kWorld)

        avg_point = point_sum / len(vertex_indices)

    else:
        # TODO
        avg_point = OpenMaya.MPoint()

    # create locator
    loc = cmds.spaceLocator(
        name="{}_avg_locator".format(dag.partialPathName())
    )[0]

    cmds.xform(loc, translation=list(avg_point)[:3])

    return loc
