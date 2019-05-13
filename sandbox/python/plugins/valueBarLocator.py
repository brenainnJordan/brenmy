'''Value Bar custom locator plugin for Maya.

Provides visual feedback for something like a blendshape slider.
Shape node should be parented to the slider transform parent,
and slider channels should connect into the shape node.

Created on 14 Jul 2018

@author: Bren

Help:
    https://help.autodesk.com/view/MAYAUL/2017/ENU/?guid=__py_ref_scripted_2py_foot_print_node_8py_example_html

Usage:

- Add to plugin path (eg via maya.env)

MAYA_PLUG_IN_PATH = D:\Repos\brenmy\sandbox\python\plugins;otherstuff

- restart maya

cmds.delete(test)

cmds.flushUndo()
cmds.unloadPlugin("valueBarLocator.py")

cmds.loadPlugin(r"valueBarLocator.py")

test = cmds.createNode("valueBarLocator")

'''

import sys
from maya.api import OpenMaya, OpenMayaUI, OpenMayaAnim, OpenMayaRender


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


class ValueBarLocatorData(OpenMaya.MUserData):
    """Class for handling node attribute values.

    Instanced to hold cached attribute values.
    Class globals used as attribute default values.
    """

    # default values
    inputValue = 0.0

    barAim = (0.0, 1.0, 0.0)
    barUp = (0.0, 0.0, 1.0)

    barWidth = 0.05
    barColor = (0.0, 1.0, 0.0)

    barHasMin = True
    barMin = 0.0
    barMinColor = (0.0, 0.0, 1.0)

    barHasMax = True
    barMax = 1.0
    barMaxColor = (1.0, 0.0, 0.0)

    def __init__(self):
        OpenMaya.MUserData.__init__(self, False)  # don't delete after draw


class ValueBarLocator(OpenMayaUI.MPxLocatorNode):
    """Custom ValueBarLocator class.
    """

    name = "valueBarLocator"
    id = OpenMaya.MTypeId(0x00002)
    drawDbClassification = "drawdb/geometry/ValueBarLocator"
    drawRegistrantId = "ValueBarLocatorNodePlugin"

    # node inputs/outputs
    inputValue = OpenMaya.MObject()

    barAim = OpenMaya.MObject()
    barUp = OpenMaya.MObject()

    barWidth = OpenMaya.MObject()
    barColor = OpenMaya.MObject()
    # TODO
    barAlpha = OpenMaya.MObject()

    barHasMin = OpenMaya.MObject()
    barMin = OpenMaya.MObject()
    barMinColor = OpenMaya.MObject()

    barHasMax = OpenMaya.MObject()
    barMax = OpenMaya.MObject()
    barMaxColor = OpenMaya.MObject()

    @staticmethod
    def creator():
        return ValueBarLocator()

    @classmethod
    def initialize(cls):
        """Create input attributes.

        Maya is very sensitive to how attributes are created during plugin initialization.
        Often crashing or needing to be restarted for attributes to appear
        correctly if at all, especially when changing an attr name for example.

        MStatus is returned as None or Str in python:

        if res is None:
            # kSuccess
            print "attr added"
        elif isinstance(res, string):
            # OpenMaya.MStatus.kInvalidParameter
            print "stuff: {}, {}".format(res, attr)
        else:
            # OpenMaya.MStatus.kFailure??
            print "attr failed: {}".format(attr)

        """
        cls._create_input_value_attr()
        cls._create_bar_width_attr()
        cls._create_bar_aim_attr()
        cls._create_bar_up_attr()
        cls._create_bar_color_attr()

    @classmethod
    def _create_input_value_attr(cls):
        """Create attr.
        """
        attr = OpenMaya.MFnNumericAttribute()

        cls.inputValue = attr.create(
            "inputValue", "iv", OpenMaya.MFnNumericData.kFloat,
            ValueBarLocatorData.inputValue
        )

        res = cls.addAttribute(cls.inputValue)
        return res

    @classmethod
    def _create_bar_aim_attr(cls):
        """Create attr.
        """
        attr = OpenMaya.MFnNumericAttribute()

        cls.barAim = attr.create(
            "barAim", "ba", OpenMaya.MFnNumericData.k3Double,
        )

        attr.default = ValueBarLocatorData.barAim

        res = cls.addAttribute(cls.barAim)
        return res

    @classmethod
    def _create_bar_up_attr(cls):
        """Create attr.
        """
        attr = OpenMaya.MFnNumericAttribute()

        cls.barUp = attr.create(
            "barUp", "bu", OpenMaya.MFnNumericData.k3Double,
        )

        # setting defaults seems to be most stable after creating attr with specified type
        # object is still bound to the function set
        # which is why this works:
        attr.default = ValueBarLocatorData.barUp

        # this does not:
#         self.barUp.default = (0.0, 1.0, 0.0)

        res = cls.addAttribute(cls.barUp)
        return res

    @classmethod
    def _create_bar_width_attr(cls):
        """Create attr.
        """
        attr = OpenMaya.MFnNumericAttribute()

        # setting simple default value of type float seems to be stable
        # however a tuple will crash maya
        cls.barWidth = attr.create(
            "barWidth", "bw", OpenMaya.MFnNumericData.kFloat,
            ValueBarLocatorData.barWidth
        )

        res = cls.addAttribute(cls.barWidth)
        return res

    @classmethod
    def _create_bar_color_attr(cls):
        """Create attr.
        """
        attr = OpenMaya.MFnNumericAttribute()

        cls.barColor = attr.create(
            "barColor", "bc", OpenMaya.MFnNumericData.k3Double,
        )

        attr.usedAsColor = True
        attr.default = ValueBarLocatorData.barColor

        res = cls.addAttribute(cls.barColor)
        return res

    def __init__(self):
        OpenMayaUI.MPxLocatorNode.__init__(self)


class ValueBarLocatorDrawOverride(OpenMayaRender.MPxDrawOverride):
    """ This handles the actually drawing of stuff.
    TODO
    - add circles to start and end of lines to round ends (optional)

    """
    @staticmethod
    def creator(obj):
        return ValueBarLocatorDrawOverride(obj)

    def __init__(self, obj):
        """

        By setting isAlwaysDirty to false in MPxDrawOverride constructor, the
        draw override will be updated (via prepareForDraw()) only when the node
        is marked dirty via DG evaluation or dirty propagation. Additional
        callback is also added to explicitly mark the node as being dirty (via
        MRenderer::setGeometryDrawDirty()) for certain circumstances.

        """
        OpenMayaRender.MPxDrawOverride.__init__(
            self, obj, None, isAlwaysDirty=False)

    def _get_attr_float(self, attr, default):
        """Get attribute value via plug.
        """
        node = dag_path.node()
        plug = OpenMaya.MPlug(node, attr)

        if plug.isNull:
            return default

        return plug.asFloat()

    def _get_attr_float_multi(self, attr, default, child_count):
        """Get multi attribute value via plug.
        """
        node = dag_path.node()
        plug = OpenMaya.MPlug(node, attr)

        if plug.isNull:
            return default

        return [
            plug.child(i).asFloat()
            for i in range(child_count)
        ]

    def _get_input_value(self, node):
        """Get input value via plug.
        """
        plug = OpenMaya.MPlug(node, ValueBarLocator.inputValue)

        if plug.isNull:
            return ValueBarLocatorData.inputValue

        return plug.asFloat()

    def _get_input_bar_width(self, node):
        """Get input value via plug.
        """
        plug = OpenMaya.MPlug(node, ValueBarLocator.barWidth)

        if plug.isNull:
            return ValueBarLocatorData.barWidth

        return plug.asFloat()

    def _get_input_bar_aim(self, node):
        """Get input value via plug.
        """
        plug = OpenMaya.MPlug(node, ValueBarLocator.barAim)

        if plug.isNull:
            return ValueBarLocatorData.barAim

        return [
            plug.child(i).asFloat()
            for i in range(3)
        ]

    def _get_input_bar_up(self, node):
        """Get input value via plug.
        """
        plug = OpenMaya.MPlug(node, ValueBarLocator.barUp)

        if plug.isNull:
            return ValueBarLocatorData.barUp

        return [
            plug.child(i).asFloat()
            for i in range(3)
        ]

    def _get_input_bar_color(self, node):
        """Get input value via plug.
        """
        plug = OpenMaya.MPlug(node, ValueBarLocator.barColor)

        if plug.isNull:
            return ValueBarLocatorData.barColor

        return [
            plug.child(i).asFloat()
            for i in range(3)
        ]

    def supportedDrawAPIs(self):
        """This plugin supports both GL and DX
        """
        return OpenMayaRender.MRenderer.kOpenGL | OpenMayaRender.MRenderer.kDirectX11 | OpenMayaRender.MRenderer.kOpenGLCoreProfile

    def prepareForDraw(self, dag_path, cameraPath, frameContext, old_data):
        # Retrieve data cache (create if does not exist)
        if isinstance(old_data, ValueBarLocatorData):
            data = old_data
        else:
            data = ValueBarLocatorData()

#         data.fColor = OpenMayaRender.MGeometryUtilities.wireframeColor(
#             dag_path)

#         data.inputValue = self._get_input_value(dag_path)
#         data.barWidth = self._get_input_bar_width(dag_path)
#         data.barUp = self._get_input_bar_up(dag_path)
#         data.barAim = self._get_input_bar_normal(dag_path)
#         data.barColor = self._get_input_bar_color(dag_path)

        node = dag_path.node()

        data.inputValue = self._get_input_value(node)
        data.barWidth = self._get_input_bar_width(node)
        data.barAim = self._get_input_bar_aim(node)
        data.barUp = self._get_input_bar_up(node)
        data.barColor = self._get_input_bar_color(node)

        return data

    def hasUIDrawables(self):
        return True

    def addUIDrawables(self, objPath, drawManager, frameContext, cache_data):
        """
        Draw some stuff.

        drawManager = OpenMayaRender.MUIDrawManager

        drawManager handles the drawing of stuff in Viewport 2.0, such as OpenGl calls

        """

        if not isinstance(cache_data, ValueBarLocatorData):
            return

        drawManager.beginDrawable()

        start_point = OpenMaya.MPoint(0.0, 0.0, 0.0)

        aim_vector = OpenMaya.MVector(*cache_data.barAim).normalize()
        up_vector = OpenMaya.MVector(*cache_data.barUp).normalize()

        # use cross product to get normal vector
        # (direction the face points towards)
        normal_vector = (aim_vector ^ up_vector) ^ aim_vector

#         end_point = OpenMaya.MPoint(
#             direction * cache_data.inputValue
#         )

        drawManager.setColor(
            OpenMaya.MColor(
                cache_data.barColor + [1.0]
            )
        )

        # draw rectacle
        center_point = OpenMaya.MPoint(
            aim_vector * cache_data.inputValue * 0.5
        )

        drawManager.rect(
            center_point,
            aim_vector,
            normal_vector,
            cache_data.barWidth,
            cache_data.inputValue * 0.5,
            True,  # filled = True
        )

        drawManager.endDrawable()


def initializePlugin(obj):
    #plugin = OpenMaya.MFnPlugin(obj, "Autodesk", "3.0", "Any")
    plugin = OpenMaya.MFnPlugin(obj)

    cls = ValueBarLocator

    try:
        plugin.registerNode(
            cls.name,
            cls.id,
            cls.creator,
            cls.initialize,
            OpenMaya.MPxNode.kLocatorNode,
            cls.drawDbClassification
        )
    except:
        raise Exception("Failed to register node")

    try:
        OpenMayaRender.MDrawRegistry.registerDrawOverrideCreator(
            cls.drawDbClassification,
            cls.drawRegistrantId,
            ValueBarLocatorDrawOverride.creator
        )
    except:
        raise Exception("Failed to register override")


def uninitializePlugin(obj):
    plugin = OpenMaya.MFnPlugin(obj)

    cls = ValueBarLocator

    try:
        plugin.deregisterNode(cls.id)
    except:
        raise Exception("Failed to deregister node")

    try:
        OpenMayaRender.MDrawRegistry.deregisterDrawOverrideCreator(
            cls.drawDbClassification,
            cls.drawRegistrantId
        )
    except:
        raise Exception("Failed to deregister override")
