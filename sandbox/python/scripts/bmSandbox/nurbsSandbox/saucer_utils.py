"""sandbox for creating starship saucer hull surfaces
"""

from maya import cmds
import math

from brenmy.geometry.nurbs import bmCurveOnSurface

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
    if cmds.nodeType(curve) not in ["transform", "nurbsCurve"]:
        return False

    con = cmds.listConnections(
        "{}.create".format(curve), source=True, destination=False, type="curveVarGroup", plugs=True
    )

    if con:
        if return_nodes:
            # maya, just wtf...
            surface, var_group_output = con[0].split("->")
            var_group, attr = var_group_output.split(".")
            return surface, var_group, attr
        else:
            return True
    else:
        return False


def create_birail_2(profile_1, profile_2, rail_1, rail_2, name, parent):
    """

from bmSandbox.nurbsSandbox import saucer_utils
reload(saucer_utils)

profile_1, profile_2, rail_1, rail_2 = cmds.ls(sl=True)

name = "test"
parent = "birail_GRP"

saucer_utils.create_birail_2(
    profile_1, profile_2,
    rail_1, rail_2,
    name, parent
)


    """
    birail = cmds.createNode("dpBirailSrf", name="{}_dpBirailSrf".format(name))

    for node, attr in [
        (profile_1, "inputProfile1"),
        (profile_2, "inputProfile2"),
        (rail_1, "inputRail1"),
        (rail_2, "inputRail2"),
    ]:
        cos_res = is_curve_on_surface(node, return_nodes=True)

        if cos_res:
            node = node.split("->")[-1]

        if cmds.nodeType(node) == "curveFromSurfaceCoS":
            curve_output = "{}.outputCurve".format(node)

        elif cos_res:
            surface, var_node, var_attr = cos_res

            cmds.warning("Creating curveFromSurfaceCoS node: {}".format(node))

            # TODO use bm build class

            # create curveFromSurfaceCoS to get output from curve on surface
            cfs_node = cmds.createNode("curveFromSurfaceCoS", name="{}{}_curveFromSurfaceCoS".format(name, node))

            cmds.connectAttr(
                "{}.worldSpace[0]".format(surface),
                "{}.inputSurface".format(cfs_node)
            )

            cmds.connectAttr(
                "{}.{}".format(var_node, var_attr),
                "{}.curveOnSurface".format(cfs_node)
            )

            curve_output = "{}.outputCurve".format(cfs_node)
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

    cmds.sets(surface_shape, edit=True, forceElement="initialShadingGroup")

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
# curve = "saucerPlateCurve1"
curve = cmds.ls(sl=True)[0]
surface = "saucer_surface"
parent = "ring_offset_GRP"

saucer_utils.project_saucer_plate_curves(
    control, curve, surface, parent
)

    """
    cos_objects = project_offset_curves(
        control, curve, curve, surface, PLATE_SEPARATION_ATTR, use_surface_local=False, use_curve_local=False,
        on_surface=True, parent=parent
    )

    return cos_objects

def create_attrs(control):
    for attr in [
        PLATE_SEPARATION_ATTR,
        DIVISION_SEPARATION_ATTR,
    ]:
        cmds.addAttr(control, longName=attr, defaultValue=1.0, keyable=True)


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
    cos_objects = []

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
        if True:
            curve_on_surface = bmCurveOnSurface.BmProjectCurveOnSurface(
                name="{}{}COS".format(name, suffix),
                curve_node=offset_node,
                curve_attr="outputCurve[0]",
                surface=surface,
                use_surface_local=False,
                direction=(0, 1, 0),
                # create_curve_outputs=True,
                # create_cfs_outputs=True,
                use_cmd=False
            )
        else:
            curve_on_surface = bmCurveOnSurface.BmProjectCurveOnSurface(
                name="{}{}COS".format(name, suffix),
                curve_node=offset_shape,
                # curve_attr="worldSpace[0]",
                surface=surface,
                use_surface_local=False,
                direction=(0, 1, 0),
                # create_curve_outputs=True,
                # create_cfs_outputs=True,
                use_cmd=True
            )

        curve_on_surface.build()

        cos_objects.append(curve_on_surface)

    # for cos_object in cos_objects:
    #     cos_object.refresh_outputs()

    return cos_objects


def create_plate_division_curves(control, name, parent, offsets_parent, surface, length):
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

    curve = cmds.curve(name=name, point=[(0, 0, 0), (length, 0, 0)], degree=1)
    cmds.parent(curve, parent)
    cmds.setAttr("{}.translate".format(curve), 0, 0, 0)

    cos_objects = project_offset_curves(
        control, name, curve, surface, DIVISION_SEPARATION_ATTR, use_surface_local=False, use_curve_local=False,
        on_surface=True, parent=offsets_parent
    )

    return curve, cos_objects


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
    division_cos_objects = []

    for i in range(division_count):
        curve, cos_objects = create_plate_division_curves(
            control, "plateDivision{}".format(i), divisions_grp, divisions_offsets_grp, saucer_surface, 100
        )

        cmds.setAttr("{}.rotateY".format(curve), 360.0*(float(i)/division_count))

        division_curves.append(curve)
        division_cos_objects.append(cos_objects)

    # create plate offset curves
    ring_cos_objects = []

    for i in range(ring_count+1):
        curve = "{}{}".format(plate_curve_name, i+1)
        cos_objects = project_saucer_plate_curves(control, curve, saucer_surface, ring_offsets_grp)
        ring_cos_objects.append(cos_objects)

    # return
    cmds.refresh()

    for cos_objects in division_cos_objects + ring_cos_objects:
        for cos_object in cos_objects:
            cos_object.refresh_outputs()
            cos_object.create_cfs_outputs()

    # create surfaces
    # note this process is HIGHLY sensitive to tolerances
    # when they're not right, or if nodes aren't quite hooked up or parented correct or whatever
    # the birail will fail!!

    for i in range(ring_count):
        rail_cos_1 = ring_cos_objects[i][1]
        rail_cos_2 = ring_cos_objects[i + 1][0]

        rail_1 = rail_cos_1.output_cfs_nodes()[0]
        rail_2 = rail_cos_2.output_cfs_nodes()[0]

        for j in range(division_count):

            profile_cos_1 = division_cos_objects[j][0]

            if j+1 < division_count:
                profile_cos_2 = division_cos_objects[j+1][1]
            else:
                profile_cos_2 = division_cos_objects[0][1]

            # take into account where offset curves cross revolved surface boundary
            if j < division_count/2:
                profile_1 = profile_cos_1.output_cfs_nodes()[0]
                profile_2 = profile_cos_2.output_cfs_nodes()[0]
            else:
                profile_1 = profile_cos_1.output_cfs_nodes()[-1]
                profile_2 = profile_cos_2.output_cfs_nodes()[-1]

            surface_transform, surface_shape, birail = create_birail_2(
                profile_1, profile_2,
                rail_1, rail_2,
                "plateSurface_{}_{}".format(i, j), plate_surface_grp
            )

            # TODO make some geo!  