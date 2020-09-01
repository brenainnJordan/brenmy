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


def create_saucer_plate_curve(control, name, parent):
    circle_transform, circle_node = create_nurbs_circle(name, parent=parent)

    cmds.addAttr(control, longName=name, defaultValue=1.0, keyable=True)
    cmds.connectAttr("{}.{}".format(control, name), "{}.radius".format(circle_node))

    return circle_transform, circle_node


def create_attrs(control):
    for attr in [
        PLATE_SEPARATION_ATTR,
        DIVISION_SEPARATION_ATTR,
    ]:
        cmds.addAttr(control, longName=attr, defaultValue=1.0, keyable=True)


def project_offset_curves(control, name, curve, surface, offset_attr, use_surface_local=True, use_curve_local=False):
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
world_space=False

saucer_sandbox.create_plate_separator_curves(
    control, name, parent, surface, length, world_space=world_space
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

    for suffix, direction in ("A", 1), ("B", -1):
        offset_node = cmds.createNode("offsetCurve", name="{}{}_offsetCurve".format(name, suffix))

        cmds.connectAttr("{}.{}".format(curve, curve_space_attr), "{}.inputCurve".format(offset_node))
        cmds.setAttr("{}.useGivenNormal".format(offset_node), True)
        cmds.setAttr("{}.normal".format(offset_node), 0, direction, 0)
        cmds.connectAttr("{}.{}".format(control, offset_attr), "{}.distance".format(offset_node))

        project_node = cmds.createNode("projectCurve", name="{}{}_projectCurve".format(name, suffix))
        cmds.connectAttr("{}.outputCurve[0]".format(offset_node), "{}.inputCurve".format(project_node))
        cmds.connectAttr("{}.{}".format(surface, surface_space_attr), "{}.inputSurface".format(project_node))
        cmds.setAttr("{}.useNormal".format(project_node), False)
        cmds.setAttr("{}.direction".format(project_node), 0,-1,0)

        var_node = cmds.createNode(
            "curveVarGroup", name="{}{}_curveVarGroup".format(name, suffix), parent=surface_shape
        )

        cmds.connectAttr("{}.outputCurve".format(project_node), "{}.create".format(var_node))

        transform = cmds.createNode("transform", name="{}{}".format(name, suffix), parent=var_node)
        shape = cmds.createNode("nurbsCurve", name="{}{}Shape".format(name, suffix), parent=transform)

        cmds.connectAttr(
            # "{}.outputCurve[0]".format(project_node), # doesn't work!
            "{}.local[0]".format(var_node),
            "{}.create".format(shape)
        )

        offset_transforms.append(transform)

    return offset_transforms


def create_plate_separator_curves(control, name, parent, surface, length, use_surface_local=True, use_curve_local=False):
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

    offset_transforms = project_offset_curves(
        control, name, curve, surface, DIVISION_SEPARATION_ATTR, use_surface_local=False, use_curve_local=False
    )

    return curve, offset_transforms


def create_saucer_plate_a(
        control, name, saucer_surface, saucer_profile, saucer_circle_1, saucer_circle_2, parent, start_angle,
        sweep_angle
):
    # create offset circles
    plate_circle_transform_1, plate_circle_node_1 = create_nurbs_circle("{}_plateCircle1".format(name), parent)
    plate_circle_transform_2, plate_circle_node_2 = create_nurbs_circle("{}_plateCircle2".format(name), parent)

    circle_add_1 = cmds.createNode("plusMinusAverage", name="{}CircleAdd1_plusMinusAverage".format(name))
    circle_add_2 = cmds.createNode("plusMinusAverage", name="{}CircleAdd2_plusMinusAverage".format(name))

    cmds.connectAttr("{}.{}".format(control, saucer_circle_1), "{}.input1D[0]".format(circle_add_1))
    cmds.connectAttr("{}.{}".format(control, PLATE_SEPARATION_ATTR), "{}.input1D[1]".format(circle_add_1))
    cmds.connectAttr("{}.output1D".format(circle_add_1), "{}.radius".format(plate_circle_node_1))

    cmds.setAttr("{}.operation".format(circle_add_2), 2)  # subtract
    cmds.connectAttr("{}.{}".format(control, saucer_circle_2), "{}.input1D[0]".format(circle_add_2))
    cmds.connectAttr("{}.{}".format(control, PLATE_SEPARATION_ATTR), "{}.input1D[1]".format(circle_add_2))
    cmds.connectAttr("{}.output1D".format(circle_add_2), "{}.radius".format(plate_circle_node_2))

    # calculate angles
    start_add = cmds.createNode("plusMinusAverage", name="{}StartAngle_plusMinusAverage".format(name))
    cmds.connectAttr("{}.{}".format(control, DIVISION_SEPARATION_ATTR), "{}.input1D[0]".format(start_add))
    cmds.setAttr("{}.input1D[1]".format(start_add), start_angle)

    end_add = cmds.createNode("plusMinusAverage", name="{}EndAngle_plusMinusAverage".format(name))
    cmds.setAttr("{}.operation".format(end_add), 2)  # subtract
    cmds.setAttr("{}.input1D[0]".format(end_add), sweep_angle)
    cmds.connectAttr("{}.{}".format(control, DIVISION_SEPARATION_ATTR), "{}.input1D[1]".format(end_add))
    cmds.connectAttr("{}.{}".format(control, DIVISION_SEPARATION_ATTR), "{}.input1D[2]".format(end_add))

    # connect angles
    # cmds.connectAttr("{}.output1D".format(start_add), "{}.rotateY".format(plate_circle_transform_1))
    # cmds.connectAttr("{}.output1D".format(start_add), "{}.rotateY".format(plate_circle_transform_2))
    cmds.setAttr("{}.rotateY".format(plate_circle_transform_1), start_angle)
    cmds.setAttr("{}.rotateY".format(plate_circle_transform_2), start_angle)

    cmds.connectAttr("{}.output1D".format(end_add), "{}.sweep".format(plate_circle_node_1))
    cmds.connectAttr("{}.output1D".format(end_add), "{}.sweep".format(plate_circle_node_2))

    # project curves
    projection_kwargs = {
        "ch": True,
        "direction": (0, 1, 0),
        "range": False,
        "useNormal": False,
        "tol": 0.01
    }

    cmds.projectCurve(plate_circle_transform_1, saucer_surface, **projection_kwargs)
    cmds.projectCurve(plate_circle_transform_2, saucer_surface, **projection_kwargs)

    # birail curves

def calculate_plate_curve_sweep_angle(control, saucer_circle):
    """calculate circumferences

    circumference_1 = 2*pi*radius_1
    sweep_ratio = sweep_angle/360.0
    plate_circumference_1 = circumference_1 * sweep_ratio
    plate_offset_circumference_1 = plate_circumference_1 - plate_separation_attr
    plate_ratio = plate_offset_circumference_1/circumference_1
    plate_angle = 360.0 * plate_ratio

    """

    # circumference = 2*pi*radius_1
    circumference_node = cmds.createNode(
        "multiplyDivide", name="{}_circumference_multiplyDivide".format(saucer_circle)
    )

    cmds.setAttr("{}.input1X".format(circumference_node), 2*math.pi)
    cmds.connectAttr("{}.{}".format(control, saucer_circle), "{}.input2X".format(circumference_node))

    # plate_circumference = circumference * sweep_ratio
    plate_circumference_node = cmds.createNode(
        "multiplyDivide", name="{}_plateCircumference_multiplyDivide".format(saucer_circle)
    )

    cmds.connectAttr("{}.{}".format(control, PLATE_SWEEP_RATIO_ATTR), "{}.input1X".format(plate_circumference_node))
    cmds.connectAttr("{}.outputX".format(circumference_node), "{}.input2X".format(plate_circumference_node))

    # plate_offset_circumference = plate_circumference - plate_separation_attr
    plate_offset_circumference_node = cmds.createNode(
        "plusMinusAverage", name="{}_plateOffsetCircumference_plusMinusAverage".format(saucer_circle)
    )

    cmds.setAttr("{}.operation".format(plate_offset_circumference_node), 2)  # subtract

    cmds.connectAttr(
        "{}.outputX".format(plate_circumference_node), "{}.input1D[0]".format(plate_offset_circumference_node)
    )
    cmds.connectAttr(
        "{}.{}".format(control, PLATE_SEPARATION_ATTR), "{}.input1D[1]".format(plate_offset_circumference_node)
    )

    # plate_ratio = plate_offset_circumference_1/circumference_1
    plate_ratio_node = cmds.createNode("multiplyDivide", name="{}_plateRatio_multiplyDivide".format(saucer_circle))
    cmds.setAttr("{}.operation".format(plate_ratio_node), 2)  # divide

    cmds.connectAttr("{}.output1D".format(plate_offset_circumference_node), "{}.input1X".format(plate_ratio_node))
    cmds.connectAttr("{}.outputX".format(circumference_node), "{}.input2X".format(plate_ratio_node))

    # plate_angle = 360.0 * plate_ratio
    plate_angle_node = cmds.createNode("multiplyDivide", name="{}_plateAngle_multiplyDivide".format(saucer_circle))
    cmds.connectAttr("{}.outputX".format(plate_ratio_node), "{}.input1X".format(plate_angle_node))
    cmds.setAttr("{}.input2X".format(plate_angle_node), 360.0)

    # divide by two
    half_node = cmds.createNode("multiplyDivide", name="{}_half_multiplyDivide".format(saucer_circle))
    cmds.connectAttr("{}.outputX".format(plate_angle_node), "{}.input1X".format(half_node))
    cmds.setAttr("{}.input2X".format(half_node), 0.5)

    # connect output
    attr_name = "{}SweepAngle".format(saucer_circle)
    cmds.addAttr(control, longName=attr_name, defaultValue=0.0, keyable=True)
    cmds.connectAttr("{}.outputX".format(half_node), "{}.{}".format(control, attr_name))

    return attr_name


def create_saucer_plate_b(
        control, name, saucer_surface, saucer_profile, saucer_circle_1, saucer_circle_2, parent, start_angle,
        sweep_angle
):
    """
    in this version we offset sweep angle based on the difference in the circumference of each circle
    (instead of the sweep angle) to ensure parallel gaps

    we also divide the plate in half to make sure the curves start precisely from the profile
    this will create one half, to create the other half, reverse the sweep angle
    """
    # create offset circles
    plate_circle_transform_1, plate_circle_node_1 = create_nurbs_circle("{}_plateCircle1".format(name), parent)
    plate_circle_transform_2, plate_circle_node_2 = create_nurbs_circle("{}_plateCircle2".format(name), parent)

    circle_add_1 = cmds.createNode("plusMinusAverage", name="{}CircleAdd1_plusMinusAverage".format(name))
    circle_add_2 = cmds.createNode("plusMinusAverage", name="{}CircleAdd2_plusMinusAverage".format(name))

    cmds.connectAttr("{}.{}".format(control, saucer_circle_1), "{}.input1D[0]".format(circle_add_1))
    cmds.connectAttr("{}.{}".format(control, PLATE_SEPARATION_ATTR), "{}.input1D[1]".format(circle_add_1))
    cmds.connectAttr("{}.output1D".format(circle_add_1), "{}.radius".format(plate_circle_node_1))

    cmds.setAttr("{}.operation".format(circle_add_2), 2)  # subtract
    cmds.connectAttr("{}.{}".format(control, saucer_circle_2), "{}.input1D[0]".format(circle_add_2))
    cmds.connectAttr("{}.{}".format(control, PLATE_SEPARATION_ATTR), "{}.input1D[1]".format(circle_add_2))
    cmds.connectAttr("{}.output1D".format(circle_add_2), "{}.radius".format(plate_circle_node_2))





    start_add = cmds.createNode("plusMinusAverage", name="{}StartAngle_plusMinusAverage".format(name))
    cmds.connectAttr("{}.{}".format(control, DIVISION_SEPARATION_ATTR), "{}.input1D[0]".format(start_add))
    cmds.setAttr("{}.input1D[1]".format(start_add), start_angle)

    end_add = cmds.createNode("plusMinusAverage", name="{}EndAngle_plusMinusAverage".format(name))
    cmds.setAttr("{}.operation".format(end_add), 2)  # subtract
    cmds.setAttr("{}.input1D[0]".format(end_add), sweep_angle)
    cmds.connectAttr("{}.{}".format(control, DIVISION_SEPARATION_ATTR), "{}.input1D[1]".format(end_add))
    cmds.connectAttr("{}.{}".format(control, DIVISION_SEPARATION_ATTR), "{}.input1D[2]".format(end_add))

    # connect angles
    # cmds.connectAttr("{}.output1D".format(start_add), "{}.rotateY".format(plate_circle_transform_1))
    # cmds.connectAttr("{}.output1D".format(start_add), "{}.rotateY".format(plate_circle_transform_2))
    cmds.setAttr("{}.rotateY".format(plate_circle_transform_1), start_angle)
    cmds.setAttr("{}.rotateY".format(plate_circle_transform_2), start_angle)

    cmds.connectAttr("{}.output1D".format(end_add), "{}.sweep".format(plate_circle_node_1))
    cmds.connectAttr("{}.output1D".format(end_add), "{}.sweep".format(plate_circle_node_2))

    # project curves
    projection_kwargs = {
        "ch": True,
        "direction": (0, 1, 0),
        "range": False,
        "useNormal": False,
        "tol": 0.01
    }

    cmds.projectCurve(plate_circle_transform_1, saucer_surface, **projection_kwargs)
    cmds.projectCurve(plate_circle_transform_2, saucer_surface, **projection_kwargs)

    # birail curves

def create_saucer_plates(
        control, saucer_surface, saucer_profile, plate_curves, division_count, plate_separation, division_separation,
        parent
):
    pass
