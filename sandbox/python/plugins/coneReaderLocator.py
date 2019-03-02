'''
Created on 14 Jul 2018

@author: Bren

from maya import cmds

cmds.delete(test)

cmds.flushUndo()
cmds.unloadPlugin("coneReaderLocator.py")

cmds.loadPlugin(r"coneReaderLocator.py")

test = cmds.createNode("coneReaderLocator")


'''

import sys
from maya.api import OpenMaya, OpenMayaUI, OpenMayaAnim, OpenMayaRender


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


class ConeReaderLocator(OpenMayaUI.MPxLocatorNode):
    name = "coneReaderLocator"
    id = OpenMaya.MTypeId(0x00001)
    drawDbClassification = "drawdb/geometry/coneReaderLocator"
    drawRegistrantId = "coneReaderLocatorNodePlugin"

    # node inputs/outputs
    input = OpenMaya.MObject()
    inputRadius = OpenMaya.MObject()
    output = OpenMaya.MObject()

    @staticmethod
    def creator():
        return ConeReaderLocator()

    #@staticmethod
    @classmethod
    def initialize(self):
        """
        unitFn = OpenMaya.MFnUnitAttribute()

        CustomLocator.size = unitFn.create(
            "size", "sz", OpenMaya.MFnUnitAttribute.kDistance)
        unitFn.default = OpenMaya.MDistance(1.0)

        OpenMaya.MPxNode.addAttribute(CustomLocator.size)
        """

        # input radius
        n_attr = OpenMaya.MFnNumericAttribute()

        self.inputRadius = n_attr.create(
            "inputRadius", "blahPoop", OpenMaya.MFnNumericData.kFloat, 1.0
        )

        # set attribute properties
        n_attr.storable = True
        n_attr.keyable = True
        n_attr.writable = True

        # input
        n_attr = OpenMaya.MFnNumericAttribute()

        self.input = n_attr.create(
            "input", "input", OpenMaya.MFnNumericData.kFloat, 1.0
        )

        # set attribute properties
        n_attr.storable = True
        n_attr.writable = True

        # output
        n_attr = OpenMaya.MFnNumericAttribute()

        self.output = n_attr.create(
            "output", "out", OpenMaya.MFnNumericData.kFloat, 0.0
        )

        # set attribute properties
        n_attr.storable = True
        #n_attr.writable = True

        # add attributes
        self.addAttribute(self.input)
        self.addAttribute(self.inputRadius)
        self.addAttribute(self.output)
        self.attributeAffects(self.inputRadius, self.output)
        self.attributeAffects(self.input, self.output)

    def __init__(self):
        OpenMayaUI.MPxLocatorNode.__init__(self)


class ConeReaderLocatorData(OpenMaya.MUserData):
    """ Construct some initial user data to be passed around by the DrawManager
    """

    def __init__(self):
        OpenMaya.MUserData.__init__(self, False)  # don't delete after draw

        self.test = "stuff"
        self.radius = 1.0


class ConeReaderLocatorDrawOverride(OpenMayaRender.MPxDrawOverride):
    """ This handles the actually drawing of stuff.
    """
    @staticmethod
    def creator(obj):
        return ConeReaderLocatorDrawOverride(obj)

    # By setting isAlwaysDirty to false in MPxDrawOverride constructor, the
    # draw override will be updated (via prepareForDraw()) only when the node
    # is marked dirty via DG evaluation or dirty propagation. Additional
    # callback is also added to explicitly mark the node as being dirty (via
    # MRenderer::setGeometryDrawDirty()) for certain circumstances.
    def __init__(self, obj):
        OpenMayaRender.MPxDrawOverride.__init__(
            self, obj, None, isAlwaysDirty=False)

    def _get_input_radius(self, dag_path):
        node = dag_path.node()
        plug = OpenMaya.MPlug(node, ConeReaderLocator.inputRadius)

        if plug.isNull:
            return 1.0

        return plug.asFloat()

    def supportedDrawAPIs(self):
        # this plugin supports both GL and DX
        return OpenMayaRender.MRenderer.kOpenGL | OpenMayaRender.MRenderer.kDirectX11 | OpenMayaRender.MRenderer.kOpenGLCoreProfile

    def prepareForDraw(self, dag_path, cameraPath, frameContext, oldData):
        # Retrieve data cache (create if does not exist)
        data = oldData
        if not isinstance(data, ConeReaderLocatorData):
            data = ConeReaderLocatorData()

        data.fColor = OpenMayaRender.MGeometryUtilities.wireframeColor(
            dag_path
        )

        data.radius = self._get_input_radius(dag_path)

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
        if not isinstance(locatordata, ConeReaderLocatorData):
            return

        drawManager.beginDrawable()

        # the order of these operations doesn't seem to affect the end result
        # ie text will always been drawn over everything else

        # draw a green wireframe cone
        base = OpenMaya.MPoint(0.0, 0.0, 0.0)
        direction = OpenMaya.MVector(0.0, 0.0, 1.0)
        radius = locatordata.radius
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
        plugin.registerNode(
            ConeReaderLocator.name,
            ConeReaderLocator.id,
            ConeReaderLocator.creator,
            ConeReaderLocator.initialize,
            OpenMaya.MPxNode.kLocatorNode,
            ConeReaderLocator.drawDbClassification
        )
    except:
        raise Exception("Failed to register node\n")

    try:
        OpenMayaRender.MDrawRegistry.registerDrawOverrideCreator(
            ConeReaderLocator.drawDbClassification,
            ConeReaderLocator.drawRegistrantId,
            ConeReaderLocatorDrawOverride.creator
        )
    except:
        raise Exception("Failed to register override\n")


def uninitializePlugin(obj):
    plugin = OpenMaya.MFnPlugin(obj)

    try:
        plugin.deregisterNode(ConeReaderLocator.id)
    except:
        raise Exception("Failed to deregister node\n")

    try:
        OpenMayaRender.MDrawRegistry.deregisterDrawOverrideCreator(
            ConeReaderLocator.drawDbClassification,
            ConeReaderLocator.drawRegistrantId
        )
    except:
        raise Exception("Failed to deregister override\n")
