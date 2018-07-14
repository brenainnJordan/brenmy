'''
Created on 14 Jul 2018

@author: Bren

from maya import cmds

cmds.delete(test)

cmds.flushUndo()
cmds.unloadPlugin("customLocator_001.py")

cmds.loadPlugin(r"E:\dev\python\maya_sandbox\src\testing\plugins\customLocator_001.py")

test = cmds.createNode("customLocator")


'''

import sys
from maya.api import OpenMaya, OpenMayaUI, OpenMayaAnim, OpenMayaRender


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


class CustomLocator(OpenMayaUI.MPxLocatorNode):
    name = "customLocator"
    id = OpenMaya.MTypeId(0x80007)
    drawDbClassification = "drawdb/geometry/CustomLocator"
    drawRegistrantId = "CustomLocatorNodePlugin"

    @staticmethod
    def creator():
        return CustomLocator()

    @staticmethod
    def initialize():
        """
        unitFn = OpenMaya.MFnUnitAttribute()

        CustomLocator.size = unitFn.create(
            "size", "sz", OpenMaya.MFnUnitAttribute.kDistance)
        unitFn.default = OpenMaya.MDistance(1.0)

        OpenMaya.MPxNode.addAttribute(CustomLocator.size)
        """
        pass

    def __init__(self):
        OpenMayaUI.MPxLocatorNode.__init__(self)


class CustomLocatorData(OpenMaya.MUserData):
    """ Construct some initial user data to be passed around by the DrawManager
    """

    def __init__(self):
        OpenMaya.MUserData.__init__(self, False)  # don't delete after draw

        self.test = "stuff"


class CustomLocatorDrawOverride(OpenMayaRender.MPxDrawOverride):
    """ This handles the actually drawing of stuff.
    """
    @staticmethod
    def creator(obj):
        return CustomLocatorDrawOverride(obj)

    # By setting isAlwaysDirty to false in MPxDrawOverride constructor, the
    # draw override will be updated (via prepareForDraw()) only when the node
    # is marked dirty via DG evaluation or dirty propagation. Additional
    # callback is also added to explicitly mark the node as being dirty (via
    # MRenderer::setGeometryDrawDirty()) for certain circumstances.
    def __init__(self, obj):
        OpenMayaRender.MPxDrawOverride.__init__(
            self, obj, None, isAlwaysDirty=False)

    def supportedDrawAPIs(self):
        # this plugin supports both GL and DX
        return OpenMayaRender.MRenderer.kOpenGL | OpenMayaRender.MRenderer.kDirectX11 | OpenMayaRender.MRenderer.kOpenGLCoreProfile

    def prepareForDraw(self, objPath, cameraPath, frameContext, oldData):
        # Retrieve data cache (create if does not exist)
        data = oldData
        if not isinstance(data, CustomLocatorData):
            data = CustomLocatorData()

        data.fColor = OpenMayaRender.MGeometryUtilities.wireframeColor(objPath)

        return data

    def hasUIDrawables(self):
        return True

    def addUIDrawables(self, objPath, drawManager, frameContext, data):
        """
        Draw some stuff.

        drawManager = OpenMayaRender.MUIDrawManager

        drawManager handles the drawing of stuff in Viewport 2.0, such as OpenGl calls

        """

        locatordata = data
        if not isinstance(locatordata, CustomLocatorData):
            return

        drawManager.beginDrawable()

        # the order of these operations doesn't seem to affect the end result
        # ie text will always been drawn over everything else

        # draw a green wireframe cone
        base = OpenMaya.MPoint(0.0, 0.0, 0.0)
        direction = OpenMaya.MVector(0.0, 0.0, 1.0)
        radius = 1.0
        height = 2.0
        filled = False

        drawManager.setColor(
            OpenMaya.MColor((0, 1, 0, 1))
        )

        drawManager.cone(base, direction, radius, height, filled=filled)

        # draw a solid (but not shaded) red sphere
        drawManager.setColor(
            OpenMaya.MColor((1, 0, 0, 1))
        )

        drawManager.sphere(base, radius * 0.5, filled=True)

        # draw some blue text
        pos = OpenMaya.MPoint(0.0, 0.0, 0.0)  # Position of the text
        textColor = OpenMaya.MColor((0.1, 0.8, 0.8, 1.0))  # Text color

        drawManager.setColor(textColor)

        # drawManager.setFontSize(OpenMayaRender.MUIDrawManager.kSmallFontSize)
        drawManager.setFontSize(OpenMayaRender.MUIDrawManager.kDefaultFontSize)

        drawManager.text(
            pos,
            locatordata.test,
            OpenMayaRender.MUIDrawManager.kCenter
        )

        # draw a line
        drawManager.line(
            base,
            OpenMaya.MPoint(0, 0, -1)
        )

        # draw another line and an arc between them
        drawManager.line(
            base,
            OpenMaya.MPoint(0, 2, 0)
        )

        center = base
        start = OpenMaya.MVector(0, 0, -1)
        end = OpenMaya.MVector(0, 1, 0)
        normal = OpenMaya.MVector(1, 0, 0)
        radius = radius
        filled = True

        drawManager.arc(center, start, end, normal, radius, filled=filled)

        # draw a list of lines
        # ** buggy!! **
        # https://forums.autodesk.com/t5/maya-programming/muidrawmanager-linelist-python-returns-an-error-when-it-s-passed/m-p/7838834#M7466
        """
        drawManager.lineList(
            OpenMaya.MPointArray([
                (0, 0, 0),
                (0, 1, 0),
                #(0, 0, 0),
                (1, 0, 0),
                (2, 2, 0),
                (10, 0, 0),
                (20, 20, 0),
            ]),
            True
        )
        """
        drawManager.endDrawable()


def initializePlugin(obj):
    #plugin = OpenMaya.MFnPlugin(obj, "Autodesk", "3.0", "Any")
    plugin = OpenMaya.MFnPlugin(obj)

    try:
        plugin.registerNode(CustomLocator.name, CustomLocator.id, CustomLocator.creator,
                            CustomLocator.initialize, OpenMaya.MPxNode.kLocatorNode, CustomLocator.drawDbClassification)
    except:
        sys.stderr.write("Failed to register node\n")
        raise Exception("poop bags")

    try:
        OpenMayaRender.MDrawRegistry.registerDrawOverrideCreator(
            CustomLocator.drawDbClassification, CustomLocator.drawRegistrantId, CustomLocatorDrawOverride.creator)
    except:
        sys.stderr.write("Failed to register override\n")
        raise Exception("poop bags")


def uninitializePlugin(obj):
    plugin = OpenMaya.MFnPlugin(obj)

    try:
        plugin.deregisterNode(CustomLocator.id)
    except:
        sys.stderr.write("Failed to deregister node\n")
        raise Exception("poop bags")

    try:
        OpenMayaRender.MDrawRegistry.deregisterDrawOverrideCreator(
            CustomLocator.drawDbClassification, CustomLocator.drawRegistrantId)
    except:
        sys.stderr.write("Failed to deregister override\n")
        raise Exception("poop bags")
