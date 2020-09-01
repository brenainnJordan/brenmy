"""sandbox for creating starship saucer hull surfaces
"""

from maya import cmds
import math

PLATE_SEPARATION_ATTR = "plateSeparation"
DIVISION_SEPARATION_ATTR = "divisionSeparation"
PLATE_COUNT_ATTR = "plateCount"
PLATE_SWEEP_ANGLE_ATTR = "plateSweepAngle"
PLATE_SWEEP_RATIO_ATTR = "plateSweepRatio"

def create_nurbs_circle(name, parent, normal=(0, 1, 0), reset_transform=True):
    circle_transform, circle_node = cmds.circle(name=name, normal=normal)
    circle_node = cmds.rename(circle_node, "{}_makeNurbCircle".format(name))

    if parent is not None:
        cmds.parent(circle_transform, parent)

        if reset_transform:
            cmds.xform(circle_transform, translation=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1))

    return circle_transform, circle_node

def get_curve_shape(curve):
    if cmds.nodeType("curve") == "transform":
        shapes = cmds.listRelatives(curve, type="nurbsCurve")
        if len(shapes):
            pass

def is_curve_on_surface(curve, return_nodes):
    con = cmds.listConnections("{}.create".format(curve), source=True, destination=False, type="curveVarGroup")

    if con:
        if return_nodes:
            # maya, just wtf...
            surface, var_group = con[0].split("->")
            return surface, var_group
        else:
            return True
    else:
        return False

def create_birail_2_curve_on_surface(profile_1, profile_2, rail_1, rail_2, surface, name, parent):
    birail = cmds.createNode("dpBirailSrf", name="{}_dpBirailSrf".format(name))

    for curve, attr in [
        (profile_1, "inputProfile1"),
        (profile_2, "inputProfile2"),
        (rail_1, "inputRail1"),
        (rail_2, "inputRail2"),
    ]:
        cfs_node = cmds.createNode("curveFromSurfaceCoS", name="{}_{}_curveFromSurfaceCoS".format(name, curve))

        cmds.connectAttr(
            "{}.worldSpace[0]".format(surface),
            "{}.inputSurface".format(cfs_node)
        )

        cmds.connectAttr(
            "{}.worldSpace[0]".format(curve),
            "{}.curveOnSurface".format(cfs_node)
        )

        cmds.connectAttr(
            "{}.worldSpace[0]".format(curve),
            "{}.{}".format(birail, attr)
        )

    cmds.setAttr("{}.transformMode".format(birail), 1)  # proportional

    surface_transform = cmds.createNode("transform", name=name, parent=parent)
    surface_shape = cmds.createNode("nurbsSurface", name="{}Shape".format(name), parent=surface_transform)

    cmds.connectAttr("{}.outputSurface".format(birail), "{}.create".format(surface_shape))

    return surface_transform, surface_shape, birail

def create_birail_2(profile_1, profile_2, rail_1, rail_2, name, parent):
    birail = cmds.createNode("dpBirailSrf", name="{}_dpBirailSrf".format(name))

    for node, attr in [
        (profile_1, "inputProfile1"),
        (profile_2, "inputProfile2"),
        (rail_1, "inputRail1"),
        (rail_2, "inputRail2"),
    ]:
        cos_res = is_curve_on_surface(node, return_nodes=True)

        if cmds.nodeType(node) == "curveFromSurfaceCoS":
            curve_output = "{}.outputCurve".format(node)

        elif cos_res:
            # create curveFromSurfaceCoS to get output from curve on surface
            cfs_node = cmds.createNode("curveFromSurfaceCoS", name="{}{}_curveFromSurfaceCoS".format(name, node))

            cmds.connectAttr(
                "{}.worldSpace[0]".format(cos_res[0]),
                "{}.inputSurface".format(cfs_node)
            )

            cmds.connectAttr(
                "{}.local[0]".format(cos_res[1]),
                "{}.curveOnSurface".format(cfs_node)
            )

            curve_output = "{}"
        else:
            curve_output = "{}.worldSpace[0]".format(node)

        cmds.connectAttr(
            curve_output,
            "{}.{}".format(birail, attr)
        )

    cmds.setAttr("{}.transformMode".format(birail), 1) # proportional

    surface_transform = cmds.createNode("transform", name=name, parent=parent)
    surface_shape = cmds.createNode("nurbsSurface", name="{}Shape".format(name), parent=surface_transform)

    cmds.connectAttr("{}.outputSurface".format(birail), "{}.create".format(surface_shape))

    return surface_transform, surface_shape, birail


def create_saucer_plate_curve(control, name, parent):
    circle_transform, circle_node = create_nurbs_circle(name, parent=parent)

    cmds.addAttr(control, longName=name, defaultValue=1.0, keyable=True)
    cmds.connectAttr("{}.{}".format(control, name), "{}.radius".format(circle_node))

    return circle_transform, circle_node


def project_saucer_plate_curves(control, curve, surface, parent):
    """

from bmSandbox.nurbsSandbox import saucer_utils
reload(saucer_utils)

control = "saucerCurveControl_loc"
curve = "saucerPlateCurve1"
surface = "saucer_surface"

saucer_utils.project_saucer_plate_curves(
    control, curve, surface,
)

    """
    offset_transforms, cfs_nodes = project_offset_curves(
        control, curve, curve, surface, PLATE_SEPARATION_ATTR, use_surface_local=False, use_curve_local=False,
        on_surface=True, parent=parent
    )

    return offset_transforms, cfs_nodes

def create_attrs(control):
    for attr in [
        PLATE_SEPARATION_ATTR,
        DIVISION_SEPARATION_ATTR,
    ]:
        cmds.addAttr(control, longName=attr, defaultValue=1.0, keyable=True)

class BmCurveOnSurface(object):
    def __init__(self):
        self._curve = None
        self._surface = None

def project_offset_curves(
        control, name, curve, surface, offset_attr,
        use_surface_local=True, use_curve_local=False, on_surface=False, parent=None
):
    """
    Note for this to work, Maya has a bunch of hoops you need to jump through,
    such as the use of a curveVarGroup, said node needs to be parented to the surface shape node

    Usage:

from bmSandbox.nurbsSandbox import saucer_sandbox
reload(saucer_sandbox)

control = "saucerCurveControl_loc"
name = "test1"
parent = "saucer_pivot"
surface = "saucer_surface"
length = 100

saucer_sandbox.create_plate_separator_curves(
    control, name, parent, surface, length
)

    """

    if use_surface_local:
        surface_space_attr = "local"
    else:
        surface_space_attr = "worldSpace[0]"

    if use_curve_local:
        curve_space_attr = "local"
    else:
        curve_space_attr = "worldSpace[0]"

    surface_shape = cmds.listRelatives(surface, type="nurbsSurface")[0]

    offset_transforms = []
    projected_transforms = []
    cfs_nodes = []

    for suffix, direction in ("A", 1), ("B", -1):

        # offset curve
        offset_node = cmds.createNode("offsetCurve", name="{}{}_offsetCurve".format(name, suffix))

        cmds.connectAttr("{}.{}".format(curve, curve_space_attr), "{}.inputCurve".format(offset_node))
        cmds.setAttr("{}.useGivenNormal".format(offset_node), True)
        cmds.setAttr("{}.normal".format(offset_node), 0, direction, 0)

        # not sure what this actually does
        # but is on by default
        cmds.setAttr("{}.cutLoop".format(offset_node), True)

        # important note!
        # this is important to increase to get stuff to build
        cmds.setAttr("{}.tolerance".format(offset_node), 0.010)

        cmds.connectAttr("{}.{}".format(control, offset_attr), "{}.distance".format(offset_node))

        offset_transform = cmds.createNode("transform", name="{}Offset{}".format(name, suffix), parent=parent)
        offset_shape = cmds.createNode("nurbsCurve", name="{}{}Shape".format(name, suffix), parent=offset_transform)
        offset_transforms.append(offset_transform)

        cmds.connectAttr("{}.outputCurve[0]".format(offset_node), "{}.create".format(offset_shape))

        # project onto surface
        project_node = cmds.createNode("projectCurve", name="{}{}_projectCurve".format(name, suffix))
        # cmds.connectAttr("{}.outputCurve[0]".format(offset_node), "{}.inputCurve".format(project_node))
        cmds.connectAttr("{}.worldSpace[0]".format(offset_shape), "{}.inputCurve".format(project_node))
        cmds.connectAttr("{}.{}".format(surface, surface_space_attr), "{}.inputSurface".format(project_node))
        cmds.setAttr("{}.useNormal".format(project_node), False)
        cmds.setAttr("{}.direction".format(project_node), 0,-1,0)

        min_tol = cmds.attributeQuery("tolerance", node=project_node, min=True)[0]
        cmds.setAttr("{}.tolerance".format(project_node), min_tol)

        # attach to surface
        var_node = cmds.createNode(
            "curveVarGroup", name="{}{}_curveVarGroup".format(name, suffix), parent=surface_shape
        )

        cmds.connectAttr("{}.outputCurve".format(project_node), "{}.create".format(var_node))

        if on_surface:
            projected_transform = cmds.createNode("transform", name="{}{}".format(name, suffix), parent=var_node)
            projected_shape = cmds.createNode("nurbsCurve", name="{}{}Shape".format(name, suffix), parent=projected_transform)

            cmds.connectAttr(
                # "{}.outputCurve[0]".format(project_node), # doesn't work!
                "{}.local[0]".format(var_node),
                "{}.create".format(projected_shape)
            )

            cfs_node = cmds.createNode("curveFromSurfaceCoS", name="{}{}_curveFromSurfaceCoS".format(name, suffix))
            cfs_nodes.append(cfs_node)

            cmds.connectAttr(
                "{}.{}".format(surface_shape, surface_space_attr),
                "{}.inputSurface".format(cfs_node)
            )

            cmds.connectAttr(
                "{}.local[0]".format(var_node),
                "{}.curveOnSurface".format(cfs_node)
            )

        else:
            projected_transform = cmds.createNode("transform", name="{}{}".format(name, suffix), parent=parent)
            projected_shape = cmds.createNode("nurbsCurve", name="{}{}Shape".format(name, suffix), parent=projected_transform)

            cfs_node = cmds.createNode("curveFromSurfaceCoS", name="{}{}_curveFromSurfaceCoS".format(name, suffix))

            cmds.connectAttr(
                "{}.{}".format(surface_shape, surface_space_attr),
                "{}.inputSurface".format(cfs_node)
            )

            cmds.connectAttr(
                "{}.local[0]".format(var_node),
                "{}.curveOnSurface".format(cfs_node)
            )

            cmds.connectAttr(
                "{}.outputCurve".format(cfs_node),
                "{}.create".format(projected_shape)
            )

        projected_transforms.append(projected_transform)

    return projected_transforms, cfs_nodes


def create_plate_separator_curves(control, name, parent, offsets_parent, surface, length):
    """
    Usage:

from bmSandbox.nurbsSandbox import saucer_sandbox
reload(saucer_sandbox)

control = "saucerCurveControl_loc"
name = "test1"
parent = "saucer_pivot"
surface = "saucer_surface"
length = 100
world_space=False

saucer_sandbox.create_plate_separator_curves(
    control, name, parent, surface, length
)

    """

    curve = cmds.curve(name=name, point=[(0,0,0), (length,0,0)], degree=1)
    cmds.parent(curve, parent)
    cmds.setAttr("{}.translate".format(curve), 0, 0, 0)

    offset_transforms, cfs_nodes = project_offset_curves(
        control, name, curve, surface, DIVISION_SEPARATION_ATTR, use_surface_local=False, use_curve_local=False,
        on_surface=True, parent=offsets_parent
    )

    return curve, offset_transforms, cfs_nodes


def create_saucer_plates(
        control, saucer_surface, ring_count, division_count, parent, plate_curve_name="saucerPlateCurve"
):
    """

from bmSandbox.nurbsSandbox import saucer_utils
reload(saucer_utils)

saucer_utils.create_saucer_plates(
    "saucerCurveControl_loc", "saucer_surface", 3, 10, "saucer_pivot"
)

    """
    # create groups
    ring_offsets_grp = "ringOffsets_GRP"
    cmds.createNode("transform", name=ring_offsets_grp)#, parent=parent)

    divisions_grp = "divisions_GRP"
    cmds.createNode("transform", name=divisions_grp, parent=parent)

    divisions_offsets_grp = "divisionsOffsets_GRP"
    cmds.createNode("transform", name=divisions_offsets_grp)#, parent=parent)

    plate_surface_grp = "plateSurface_GRP"
    cmds.createNode("transform", name=plate_surface_grp)#, parent=parent)

    # create divisions
    division_curves = []
    division_cfs_nodes = []

    for i in range(division_count):
        curve, offset_curves, cfs_nodes = create_plate_separator_curves(
            control, "plateDivision{}".format(i), divisions_grp, divisions_offsets_grp, saucer_surface, 100
        )

        cmds.setAttr("{}.rotateY".format(curve), 360.0*(float(i)/division_count))

        division_curves.append(offset_curves)
        division_cfs_nodes.append(cfs_nodes)

    # create plate offset curves
    ring_curves = []
    ring_cfs_nodes = []

    for i in range(ring_count+1):
        curve = "{}{}".format(plate_curve_name, i+1)
        offset_curves, cfs_nodes = project_saucer_plate_curves(control, curve, saucer_surface, ring_offsets_grp)
        ring_curves.append(offset_curves)
        ring_cfs_nodes.append(cfs_nodes)

    # return

    # create surfaces
    # TODO for some reason my projected curves aren't working with birail, even manually, figure out why
    for i in range(ring_count):
        rail_1 = ring_curves[i][1]
        rail_cfs_node_1 = ring_cfs_nodes[i][1]

        rail_2 = ring_curves[i+1][0]
        rail_cfs_nodes_2 = ring_cfs_nodes[i + 1][0]

        for j in range(division_count):
            profile_1 = division_curves[j][0]
            profile_cfs_node_1 = division_cfs_nodes[j][0]

            if j+1 < division_count:
                profile_2 = division_curves[j+1][1]
                profile_cfs_node_2 = division_cfs_nodes[j+1][1]
            else:
                profile_2 = division_curves[0][1]
                profile_cfs_node_2 = division_cfs_nodes[0][1]

            # surface_transform, surface_shape, birail = create_birail_2(
            #     profile_1, profile_2, rail_1, rail_2, "plateSurface_{}_{}".format(i, j), plate_surface_grp
            # )

            surface_transform, surface_shape, birail = create_birail_2(
                profile_cfs_node_1, profile_cfs_node_2,
                rail_cfs_node_1, rail_cfs_nodes_2,
                "plateSurface_{}_{}".format(i, j), plate_surface_grp
            )

            # angle = 360.0*(float(j)/division_count)
            #
            # if angle > 180.0:
            #     surface_transform, surface_shape, birail = create_birail_2(
            #         profile_cfs_node_1, profile_cfs_node_2,
            #         rail_cfs_node_1, rail_cfs_nodes_2,
            #         "plateSurface_{}_{}".format(i, j), plate_surface_grp
            #     )
            # else:
            #     surface_transform, surface_shape, birail = create_birail_2(
            #         profile_cfs_node_2, profile_cfs_node_1,
            #         rail_cfs_node_1, rail_cfs_nodes_2,
            #         "plateSurface_{}_{}".format(i, j), plate_surface_grp
            #     )
