'''
Created on 11 Jun 2019

@author: Bren
'''
import math
import random
import fbx

import numpy
from scipy.spatial.transform import Rotation as scipy_rotation

from bmSandbox import matrix_stuff2
reload(matrix_stuff2)

from maya import cmds

ROTATE_SEED = 16.6
ROTATE_SEED = None

x_mat = matrix_stuff2.XMatrixFunctions()
y_mat = matrix_stuff2.YMatrixFunctions()
z_mat = matrix_stuff2.ZMatrixFunctions()

rotate_order_names = [
    'xyz',
    'yzx',
    'zxy',
    'xzy',
    'yxz',
    'zyx'
]

rotate_order_matrices = {
    'xyz': x_mat * y_mat * z_mat,
    'yzx': y_mat * z_mat * x_mat,
    'zxy': z_mat * x_mat * y_mat,
    'xzy': x_mat * z_mat * y_mat,
    'yxz': y_mat * x_mat * z_mat,
    'zyx': z_mat * y_mat * x_mat,
}


def get_random_rotate(seed, min=-360, max=360):
    if seed is not None:
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


def thingA2(rotate_order_index):
    """
    As above but with varying rotation order
    """

    loc = cmds.spaceLocator()[0]

    rotate = get_random_rotate(ROTATE_SEED)

    cmds.xform(loc, rotation=rotate)

    rotate_order_name = rotate_order_names[rotate_order_index]
    matrix_fn = rotate_order_matrices[rotate_order_name]

    composed_matrix = matrix_fn.compose(rotate)
    composed_matrix = numpy.array(composed_matrix).flatten().tolist()

#     rotate_orders = cmds.attributeQuery("rotateOrder", node="locator1", listEnum=True)
#     rotate_orders = rotate_orders[0].split(":")

    local_matrix = cmds.getAttr(loc + ".matrix")
    print "maya matrix xyz: ", local_matrix

    cmds.setAttr(loc + ".rotateOrder", rotate_order_index)

    local_matrix = cmds.getAttr(loc + ".matrix")

    # test on new loc
    loc1 = cmds.spaceLocator()[0]
    cmds.setAttr(loc1 + ".rotateOrder", rotate_order_index)
    cmds.xform(loc1, matrix=composed_matrix)

    # print results
    print "rotation: ", rotate
    print "maya matrix attr: ", local_matrix
    print "composed matrix: ", composed_matrix


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

    # initialize a random rotation
    rotate = get_random_rotate(ROTATE_SEED)

    # create a locator and apply rotation
    loc = cmds.spaceLocator()[0]
    cmds.xform(loc, rotation=rotate)

    # query local matrix
    local_matrix = cmds.getAttr(loc + ".matrix")

    # seperate rows
    row_0 = local_matrix[0:4]
    row_1 = local_matrix[4:8]
    row_2 = local_matrix[8:12]
    row_3 = local_matrix[12:16]

    # apply matrix to new loc to compare how maya xform command performs
#     loc_1 = cmds.spaceLocator()[0]
    loc_1 = cmds.createNode("transform")

    cmds.xform(loc_1, matrix=local_matrix)
    maya_decomp = cmds.xform(loc_1, query=True, rotation=True)

    # construct fbx matrix
    fbx_matrix = fbx.FbxMatrix()
    for i, row in enumerate([row_0, row_1, row_2, row_3]):
        fbx_matrix.SetRow(i, fbx.FbxVector4(*row))

    # decompose via FbxMatrix, FbxQuaternion and FbxAMatrix
    # note this only works for XYZ rotation order
    pTranslation = fbx.FbxVector4()
    pRotation = fbx.FbxQuaternion()
    pShearing = fbx.FbxVector4()
    pScaling = fbx.FbxVector4()

    fbx_matrix.GetElements(
        pTranslation,
        pRotation,
        pShearing,
        pScaling,
    )

    test = fbx.FbxAMatrix()
    test.SetQ(pRotation)

    # manual decomp

    # nope try again (wrong order? xyz instead of zyx?)
    #rot_y = math.asin(row_2[0])

    # xyz order gives correct y
    # interesting to note sometimes this matches maya decomp
    # and sometimes is matches original rotation
    rot_y = -math.asin(row_0[2])
    rot_y_degs = math.degrees(rot_y)

    # not exactly
    # correct value but positive/negative often incorrect
    # not sure why
#     rot_x = math.acos(row_2[2] / math.cos(rot_y))
#     rot_x_degs = math.degrees(rot_x)
#     rot_x = math.asin(row_1[2] / math.cos(rot_y))
#     rot_x_degs = math.degrees(rot_x)
#
#     rot_z = math.acos(row_0[0] / math.cos(rot_y))
#     rot_z_degs = math.degrees(rot_z)

    # use sine instead of cosine to get pos/neg values
    # sometimes right!!
    # obviously there's certain conditions where this works
    # and others where it doesn't
    # probably some gimbal lock related stuff

    # TODO rot y seems to be correct 100% of the time
    # do some random tests to see if that's consistent

    # _p for partial
#     rot_x_p = math.asin(row_2[2] / math.sin(math.radians(90 - rot_y_degs)))
#     rot_x_degs = (math.degrees(rot_x_p) - 90) * -1
#
#     rot_z = math.asin(row_0[1] / math.sin(math.radians(90 - rot_y_degs)))
#     rot_z_degs = math.degrees(rot_z)

    # check for pos/neg
    # we can determine the direction of rotation by comparing
    # cosine and sine values of the angle
    # these can be found from particular rows and columns
    # of the matrix when written out algebraically
    # this seems to work consistently!!!

    sin_z = row_0[1] / math.cos(rot_y)
    cos_z = row_0[0] / math.cos(rot_y)
    print "cos z: {}, sin z: {}".format(cos_z, sin_z)

    if cos_z == 1:
        rot_z = 0.0
    elif cos_z == 0:
        rot_z = math.radians(180)
    elif sin_z == 1:
        rot_z = math.radians(90)
    elif sin_z == -1:
        rot_z = math.radians(-90)
    elif cos_z > 0 and sin_z > 0:
        print "+z"
        rot_z = math.acos(cos_z)
    elif cos_z < 0 and sin_z > 0:
        print "180-z"
        rot_z = math.radians(180) - math.asin(sin_z)
    elif cos_z > 0 and sin_z < 0:
        print "-z"
        rot_z = -math.acos(cos_z)
    elif cos_z < 0 and sin_z < 0:
        print "-180-z"
        rot_z = math.radians(-180) - math.asin(sin_z)
    elif cos_z > 1 or cos_z < -1 or sin_z > 1 or sin_z < -1:
        raise Exception("-1 > cos/sin > 1 out of  bounds")
        # TOOD if neccesary

    rot_z_degs = math.degrees(rot_z)

    # check for pos/neg
    cos_x = row_2[2] / math.cos(rot_y)

    sin_x = row_1[2] / math.cos(rot_y)

    print "cos x: {}, sin x: {}".format(cos_x, sin_x)

    if cos_x == 1:
        rot_x = 0.0
    elif cos_x == 0:
        rot_x = math.radians(180)
    elif sin_x == 1:
        rot_x = math.radians(90)
    elif sin_x == -1:
        rot_x = math.radians(-90)
    elif cos_x > 0 and sin_x > 0:
        print "+z"
        rot_x = math.acos(cos_x)
    elif cos_x < 0 and sin_x > 0:
        print "180-z"
        rot_x = math.radians(180) - math.asin(sin_x)
    elif cos_x > 0 and sin_x < 0:
        print "-z"
        rot_x = -math.acos(cos_x)
    elif cos_x < 0 and sin_x < 0:
        print "-180-z"
        rot_x = math.radians(-180) - math.asin(sin_x)
    elif cos_x > 1 or cos_x < -1 or sin_x > 1 or sin_x < -1:
        raise Exception("-1 > cos/sin > 1 out of  bounds")
        # TOOD if neccesary

    rot_x_degs = math.degrees(rot_x)

    # test going back through each rotation
    # Nope, can't work cos y is not the last rotation!
#     mat_y = fbx.FbxMatrix()
#     mat_y.SetRow(0, fbx.FbxVector4(math.cos(rot_y), 0, -math.sin(rot_y), 0))
#     mat_y.SetRow(1, fbx.FbxVector4(0, 1, 0, 0))
#     mat_y.SetRow(2, fbx.FbxVector4(math.sin(rot_y), 0, math.cos(rot_y), 0))
#     mat_y.SetRow(3, fbx.FbxVector4(0, 0, 0, 1))
#
#     mat_xz = mat_y.Inverse() * fbx_matrix
#
#     rot_x = math.acos(mat_xz.GetRow(1)[1])
#     rot_x_degs = math.degrees(rot_x)
#
#     rot_z_degs = 0  # TODO

    # test manual decomp
    loc_2 = cmds.spaceLocator()[0]
    cmds.xform(loc_2, rotation=(rot_x_degs, rot_y_degs, rot_z_degs))

    # test scipy direction cosines method

    # get direction cosines using dot product
    # this seems to suffer similar problems
    # to when we don't check for pos/neg rotations
    # sometimes is correct, others not
    # probably best to avoid using this
    # especially considering this module
    # is not present in the sourced maya version of scipy

    world_x_vec = fbx.FbxVector4(1, 0, 0)
    world_y_vec = fbx.FbxVector4(0, 1, 0)
    world_z_vec = fbx.FbxVector4(0, 0, 1)
    world_vectors = [world_x_vec, world_y_vec, world_z_vec]

    row_0_vec = fbx.FbxVector4(*row_0)
    row_1_vec = fbx.FbxVector4(*row_1)
    row_2_vec = fbx.FbxVector4(*row_2)

    row_vectors = [fbx.FbxVector4(*i) for i in row_0, row_1, row_2]

    # actually, we can determine if these should be positive or negative
    # from cross products etc.
    # would that actually help though??
    # TODO!

    direction_cosines = [
        [row_vec.DotProduct(w_vec) for w_vec in world_vectors]
        for row_vec in row_vectors
    ]

    sp_rot = scipy_rotation.from_dcm(
        numpy.array(direction_cosines)
    )

    sp_decomp = sp_rot.as_euler('XYZ', degrees=True)

#     loc_3 = cmds.spaceLocator()[0]
#     cmds.xform(loc_3, rotation=sp_decomp.tolist())

    # compare matrices
    print "maya matrix attr: ", local_matrix

    fbx_matrix_list = [j for i in range(4) for j in list(fbx_matrix.GetRow(i))]
    print "fbx matrix: ", fbx_matrix_list

    # print rows
    print "maya matrix rows:\n\t{}\n\t{}\n\t{}\n\t{}".format(
        row_0, row_1, row_2, row_3
    )

    # compare results
    print "rotation: ", rotate
    print "maya decomp: ", maya_decomp
    print "Fbx decomp: {}".format(list(test.GetR()))
    print "Scipy decomp: {}".format(sp_decomp.tolist())
    print "manual decomp: ", rot_x_degs, rot_y_degs, rot_z_degs

#     for i in local_matrix:
#         print math.degrees(math.asin(i))


def thingB2():
    """
    as above but using matrix function classes
    """
    rotate = get_random_rotate(ROTATE_SEED)

    loc = cmds.spaceLocator()[0]
    cmds.xform(loc, rotation=rotate)

    matrix_fn = x_mat * y_mat * z_mat

    local_matrix = cmds.getAttr(loc + ".matrix")

    decomposed_rotate = matrix_fn.decompose(local_matrix, verbose=True)

    # test
    loc1 = cmds.spaceLocator()[0]
    cmds.xform(loc1, rotation=decomposed_rotate)

    # print results
    print "original rotate: {}".format(rotate)
    print "decomposed rotate: {}".format(decomposed_rotate)


def thingB3(rotate_order_index):
    """
    as above with different rotation orders
    """
    pass
