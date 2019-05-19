""" Performance tests of valueBar custom locator plugin

import sys

path = r"D:\Repos\brenmy\sandbox\python\scripts"
if path not in sys.path:
    sys.path.append(path)

from bmPluginTests import value_bar_testing_1
reload(value_bar_testing_1)

value_bar_testing_1.performance_test1(100)

"""

import subprocess

from maya import cmds


def create_driver_locator():
    loc = cmds.spaceLocator()[0]
    cmds.setKeyframe(loc + ".translateY", v=0.0, t=1)
    cmds.setKeyframe(loc + ".translateY", v=5.0, t=50)
    cmds.setKeyframe(loc + ".translateY", v=-5.0, t=115)
    return loc


def benchmark_test_locator(count=100):
    """

    1 x animated locator ~400fps

    x100 driven locators ~260fps

    x1000 driven locators ~55fps

    x10000 driven locators ~6fps

    """
    cmds.file(new=True, force=True)

    loc = create_driver_locator()

    for i in range(count):
        test = cmds.createNode("locator", name="test{}".format(i))
        test_prnt = cmds.listRelatives(test, parent=True)[0]

        cmds.setAttr(test_prnt + ".translateX", i)
        cmds.connectAttr(loc + ".translateY", test + ".localPositionY")


def benchmark_test_linear_curve(count=100):
    """
    x100 ~100fps
    x1000 ~13fps

    """
    cmds.file(new=True, force=True)

    loc = create_driver_locator()

    for i in range(count):
        test = cmds.curve(d=1, p=[(0, 0, 0), (1, 0, 0)])
        test_shape = cmds.listRelatives(test)[0]

        cmds.setAttr(test + ".translateX", i)
        cmds.connectAttr(
            loc + ".translate",
            test_shape + ".controlPoints[1]"
        )


def performance_test1(count=100):
    """

    rect x 100 ~60fps :(
    rect x 1000 ~7fps :'(

    line x 100 ~65fps :(

    line x 1000 ~7.5fps :( (alwaysDirty=true, using preEvaluation, tumbling viewport remains fast) 
    line x 1000 ~8.5fps (alwaysDirty=true, but tumbling viewport slows to ~9fps when not playing)
    line x 1000 ~53fps (without updating draw)

    """

    # unload
    cmds.file(new=True, force=True)
    cmds.flushUndo()
    cmds.unloadPlugin("valueBarLocator")

    # copy new build
    src = r"D:\Repos\brenmy\sandbox\cpp\valueBarLocator\valueBarLocator\Release\valueBarLocator.mll"
    dst = r"D:\Repos\brenmy\sandbox\testBuilds\valueBarLocator.mll"

    status = subprocess.call(
        ["copy", src, dst],
        shell=True
    )

    print status

    # test
    cmds.loadPlugin(r"valueBarLocator")

    loc = create_driver_locator()

    for i in range(count):
        test = cmds.createNode(
            "valueBarLocator", name="valueBarTest{}".format(i))
        test_prnt = cmds.listRelatives(test, parent=True)[0]

        cmds.setAttr(test_prnt + ".translateX", i)
        cmds.connectAttr(loc + ".translateY", test + ".input")


def performance_test_py_1(count=100):
    """

    x100 ~23fps (full value bar setup)

    """

    # unload
    cmds.file(new=True, force=True)
    cmds.flushUndo()
    cmds.unloadPlugin("valueBarLocatorPy")

    # test
    cmds.loadPlugin(r"valueBarLocatorPy")

    loc = create_driver_locator()

    for i in range(count):
        test = cmds.createNode(
            "valueBarLocator", name="valueBarTest{}".format(i)
        )

        test_prnt = cmds.listRelatives(test, parent=True)[0]

        cmds.setAttr(test_prnt + ".translateX", i)
        cmds.connectAttr(loc + ".translateY", test + ".inputValue")


def performance_test_loc_geom(count=100):
    """

    foot x100 ~63fps
    foot x1000 ~7.5fps

    sqaure x100 ~63fps
    sqaure x1000 ~7.5fps

    """

    # unload
    cmds.file(new=True, force=True)
    cmds.flushUndo()
    cmds.unloadPlugin("testLocatorGeom")

    # copy new build
    src = r"D:\Repos\brenmy\sandbox\cpp\testLocatorGeom\testLocatorGeom\Release\testLocatorGeom.mll"
    dst = r"D:\Repos\brenmy\sandbox\testBuilds\testLocatorGeom.mll"

    status = subprocess.call(
        ["copy", src, dst],
        shell=True
    )

    print status

    # test
    cmds.loadPlugin(r"testLocatorGeom")

    loc = create_driver_locator()

    for i in range(count):
        test = cmds.createNode(
            "testLocatorGeom", name="test{}".format(i))
        test_prnt = cmds.listRelatives(test, parent=True)[0]

        cmds.setAttr(test_prnt + ".translateX", i)
        cmds.connectAttr(loc + ".translateY", test + ".input")


def performance_test_foot_geom(count=100):
    """


    """

    # unload
    cmds.file(new=True, force=True)
    cmds.flushUndo()
    cmds.unloadPlugin("footPrintNode_GeometryOverride")

#     # copy new build
#     src = r"D:\Repos\brenmy\sandbox\cpp\testLocatorGeom\testLocatorGeom\Release\testLocatorGeom.mll"
#     dst = r"D:\Repos\brenmy\sandbox\testBuilds\testLocatorGeom.mll"
#
#     status = subprocess.call(
#         ["copy", src, dst],
#         shell=True
#     )
#
#     print status

    # test
    cmds.loadPlugin(r"footPrintNode_GeometryOverride")

    loc = create_driver_locator()

    for i in range(count):
        test = cmds.createNode(
            "footPrint_GeometryOverride", name="test{}".format(i))
        test_prnt = cmds.listRelatives(test, parent=True)[0]

        cmds.setAttr(test_prnt + ".translateX", i)
        cmds.connectAttr(loc + ".translateY", test + ".size")
