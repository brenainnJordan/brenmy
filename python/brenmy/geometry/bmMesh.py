'''
Created on 23 Jun 2018

@author: Bren

OpenMaya API mesh utilities

'''

from maya.api import OpenMaya


def get_points(mesh):
    # get dag
    sl = OpenMaya.MSelectionList()
    sl.add(mesh)
    dag = sl.getDagPath(0)

    # get points
    m_mesh = OpenMaya.MFnMesh(dag)
    points = m_mesh.getVertices()

    return points


def set_points(mesh, points):
    # get dag
    sl = OpenMaya.MSelectionList()
    sl.add(mesh)
    dag = sl.getDagPath(0)

    # get points
    m_mesh = OpenMaya.MFnMesh(dag)
    m_mesh.setVertices(points)

    return True