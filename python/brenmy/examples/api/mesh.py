'''
Created on 23 Jun 2018

@author: Bren

OpenMaya API mesh example code

'''

from maya import OpenMaya


def get_points(mesh):
    # get dag
    sl = OpenMaya.MSelectionList()
    sl.add(mesh)
    dag = sl.getDagPath(0)

    # get points
    m_mesh = OpenMaya.MFnMesh(dag)
    points = m_mesh.getVertices()

    return points
