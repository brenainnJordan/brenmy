'''
Created on 11 Jun 2019

@author: Bren
'''
import math
import random
import fbx

from maya import cmds

ROTATE_SEED = 16.6


def get_random_rotate(seed, min=-360, max=360):
    random.seed(seed)
    return (
        random.uniform(min, max),
        random.uniform(min, max),
        random.uniform(min, max),
    )


def thingA1():
    """
    Create locator, give it some random local translate and rotate values.
    Get matrix via xform.
    Calculate matrix manually.
    Compare matrices.
    xform second locator with manual matrix.
    Compare locators.
    """

    loc = cmds.spaceLocator()[0]

    rotate = get_random_rotate(ROTATE_SEED)
    print "rotation: ", rotate

    rads = [math.radians(i) for i in rotate]
    print "radians: ", rads

    cmds.xform(loc, rotation=rotate)

    xform_matrix = cmds.xform(loc, query=True, matrix=True)
    print "maya xform: ", xform_matrix

    local_matrix = cmds.getAttr(loc + ".matrix")
    print "maya matrix attr: ", local_matrix

    x_rot, y_rot, z_rot = rads

    x_matrix = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, math.cos(x_rot), math.sin(x_rot), 0.0],
        [0.0, -math.sin(x_rot), math.cos(x_rot), 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ]

    y_matrix = [
        [math.cos(y_rot), 0.0, -math.sin(y_rot), 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [math.sin(y_rot), 0.0, math.cos(y_rot), 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ]

    z_matrix = [
        [math.cos(z_rot), math.sin(z_rot), 0.0, 0.0],
        [-math.sin(z_rot), math.cos(z_rot), 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ]

    fbx_x_matrix = fbx.FbxMatrix()
    for i, row in enumerate(x_matrix):
        fbx_x_matrix.SetRow(i, fbx.FbxVector4(*row))

    fbx_y_matrix = fbx.FbxMatrix()
    for i, row in enumerate(y_matrix):
        fbx_y_matrix.SetRow(i, fbx.FbxVector4(*row))

    fbx_z_matrix = fbx.FbxMatrix()
    for i, row in enumerate(z_matrix):
        fbx_z_matrix.SetRow(i, fbx.FbxVector4(*row))

    transform = fbx_z_matrix * fbx_y_matrix * fbx_x_matrix

    # print matrix
    fbx_matrix = [j for i in range(4) for j in list(transform.GetRow(i))]
    print "fbx matrix: ", fbx_matrix

    # test on new loc
    loc2 = cmds.spaceLocator()[0]
    cmds.xform(loc2, matrix=fbx_matrix)

    # interesting to note that maya does not decompose
    # identical local rotate values to the original
    # loc2 and loc3 results are the same
    # axes align with loc1, but local values are different!
    loc3 = cmds.spaceLocator()[0]
    cmds.xform(loc3, matrix=local_matrix)

    # decompose via FbxMatrix, FbxQuaternion and FbxAMatrix
    # note this only works for XYZ rotation order
    pTranslation = fbx.FbxVector4()
    pRotation = fbx.FbxQuaternion()
    pShearing = fbx.FbxVector4()
    pScaling = fbx.FbxVector4()

    transform.GetElements(
        pTranslation,
        pRotation,
        pShearing,
        pScaling,
    )

    # test results
    # local values are same as maya's decompose!
    # as in correct axis alignment with loc1
    # but different local values to loc1
    test = fbx.FbxAMatrix()
    test.SetQ(pRotation)
    print "FbxAMatrix rotation: ", test.GetR()


def thingA2(rotation_order):
    """
    As above but with varying rotation order
    """
    pass


def thingA3(rotation_order):
    """
    As above but with scale
    """
    pass


def thingA4(rotation_order):
    """
    As above but with non uniform scale
    """
    pass


def thingA5():
    """
    parent stuff, and rotate pivots etc. the works.
    (Maybe split into more methods?)
    """
    pass


def thingB1():
    """
    Create locator, give it some random local rotate values.
    Get matrix via xform.
    Decompose matrix to local rotate values.
    Compare values
    """
    pass


def thingB2():
    """
    Stuff
    """
    pass
