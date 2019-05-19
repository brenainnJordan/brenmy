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
    barAlpha = 0.5

    barHasMin = True
    barMinValue = 0.0
    barMinVisibility = True
    barMinColor = (0.0, 0.0, 1.0)

    barHasMax = True
    barMaxValue = 1.0
    barMaxVisibility = True
    barMaxColor = (1.0, 0.0, 0.0)

    # calculated values
    start_point = OpenMaya.MPoint(0.0, 0.0, 0.0)
    aim_vector = OpenMaya.MVector()
    up_vector = OpenMaya.MVector()
    normal_vector = OpenMaya.MVector()

    start_value = 0.0
    end_value = 0.0
    bar_height = 0.0
    bar_center_point = OpenMaya.MPoint()

    min_bar_height = 0.0
    min_center_point = OpenMaya.MPoint()

    max_bar_height = 0.0
    max_center_point = OpenMaya.MPoint()

    bar_m_color = OpenMaya.MColor()
    min_m_color = OpenMaya.MColor()
    max_m_color = OpenMaya.MColor()

    def __init__(self):
        OpenMaya.MUserData.__init__(self, False)  # don't delete after draw


class ValueBarLocator(OpenMayaUI.MPxLocatorNode):
    """Custom ValueBarLocator class.
    """

    name = "valueBarLocator"
    id = OpenMaya.MTypeId(0x10002)
    drawDbClassification = "drawdb/geometry/ValueBarLocator"
    drawRegistrantId = "ValueBarLocatorNodePlugin"

    # node inputs/outputs
    output = OpenMaya.MObject()

    inputValue = OpenMaya.MObject()

    barAim = OpenMaya.MObject()
    barUp = OpenMaya.MObject()

    barWidth = OpenMaya.MObject()
    barColor = OpenMaya.MObject()
    barAlpha = OpenMaya.MObject()

    barMinComp = OpenMaya.MObject()
    barHasMin = OpenMaya.MObject()
    barMinValue = OpenMaya.MObject()
    barMinVisibility = OpenMaya.MObject()
    barMinColor = OpenMaya.MObject()

    barMaxComp = OpenMaya.MObject()
    barHasMax = OpenMaya.MObject()
    barMaxValue = OpenMaya.MObject()
    barMaxVisibility = OpenMaya.MObject()
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

        # dummy output
        # TEST
        output_attr = OpenMaya.MFnNumericAttribute()

        cls.output = output_attr.create(
            "output", "out", OpenMaya.MFnNumericData.kFloat, 0.0
        )

        cls.addAttribute(cls.output)

        cls._create_input_value_attr()
        cls._create_bar_width_attr()
        cls._create_bar_aim_attr()
        cls._create_bar_up_attr()
        cls._create_bar_color_attr()
        cls._create_bar_alpha_attr()

        cls._create_min_comp_attr()
        cls._create_max_comp_attr()

    @classmethod
    def _create_input_value_attr(cls):
        """Create attr.
        """
        attr = OpenMaya.MFnNumericAttribute()

        cls.inputValue = attr.create(
            "inputValue", "iv", OpenMaya.MFnNumericData.kFloat,
            ValueBarLocatorData.inputValue
        )

        attr.affectsAppearance = True
        attr.storable = True
        attr.keyable = True
        attr.writable = True

        res = cls.addAttribute(cls.inputValue)

        cls.attributeAffects(cls.inputValue, cls.output)
        cls.attributeAffects(cls.inputValue, cls.localPositionX)

        return res

    @classmethod
    def _create_bar_aim_attr(cls):
        """Create attr.
        """
        attr = OpenMaya.MFnNumericAttribute()

        cls.barAim = attr.create(
            "barAim", "aim", OpenMaya.MFnNumericData.k3Double,
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
            "barUp", "up", OpenMaya.MFnNumericData.k3Double,
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

    @classmethod
    def _create_bar_alpha_attr(cls):
        """Create attr.

        TODO limit between 0.0 and 1.0
        """
        attr = OpenMaya.MFnNumericAttribute()

        cls.barAlpha = attr.create(
            "barAlpha", "bal", OpenMaya.MFnNumericData.kFloat,
            ValueBarLocatorData.barAlpha
        )

        res = cls.addAttribute(cls.barAlpha)
        return res

    @classmethod
    def _create_bar_min_attr(cls):
        """Create attr.
        """
        attr = OpenMaya.MFnNumericAttribute()

        cls.barMin = attr.create(
            "barMin", "min", OpenMaya.MFnNumericData.kFloat,
            ValueBarLocatorData.barMin
        )

        res = cls.addAttribute(cls.barMin)
        return res

    @classmethod
    def _create_bar_max_attr(cls):
        """Create attr.
        """
        attr = OpenMaya.MFnNumericAttribute()

        cls.barMax = attr.create(
            "barMax", "max", OpenMaya.MFnNumericData.kFloat,
            ValueBarLocatorData.barMax
        )

        res = cls.addAttribute(cls.barMax)
        return res

    @classmethod
    def _create_min_comp_attr(cls):
        """Create attr.
        """
        comp_attr = OpenMaya.MFnCompoundAttribute()
        cls.barMinComp = comp_attr.create("barMinComp", "minc")

        # has min
        has_min_attr = OpenMaya.MFnNumericAttribute()

        cls.barHasMin = has_min_attr.create(
            "barHasMin", "hMin", OpenMaya.MFnNumericData.kBoolean,
            ValueBarLocatorData.barHasMin
        )

        # min visibility
        min_vis_attr = OpenMaya.MFnNumericAttribute()

        cls.barMinVisibility = min_vis_attr.create(
            "barMinVisibility", "minV", OpenMaya.MFnNumericData.kBoolean,
            ValueBarLocatorData.barMinVisibility
        )

        # min value
        min_val_attr = OpenMaya.MFnNumericAttribute()

        cls.barMinValue = min_val_attr.create(
            "barMinValue", "min", OpenMaya.MFnNumericData.kFloat,
            ValueBarLocatorData.barMinValue
        )

        # min color
        min_col_attr = OpenMaya.MFnNumericAttribute()

        cls.barMinColor = min_col_attr.create(
            "barMinColor", "minC", OpenMaya.MFnNumericData.k3Double,
        )

        min_col_attr.usedAsColor = True
        min_col_attr.default = ValueBarLocatorData.barMinColor

        # create attr hierarchy
        comp_attr.addChild(cls.barHasMin)
        comp_attr.addChild(cls.barMinVisibility)
        comp_attr.addChild(cls.barMinValue)
        comp_attr.addChild(cls.barMinColor)

        # add comp attr
        res = cls.addAttribute(cls.barMinComp)

        return res

    @classmethod
    def _create_max_comp_attr(cls):
        """Create attr.
        """
        comp_attr = OpenMaya.MFnCompoundAttribute()
        cls.barMaxComp = comp_attr.create("barMaxComp", "maxc")

        # has max
        has_max_attr = OpenMaya.MFnNumericAttribute()

        cls.barHasMax = has_max_attr.create(
            "barHasMax", "hMax", OpenMaya.MFnNumericData.kBoolean,
            ValueBarLocatorData.barHasMax
        )

        # max visibility
        max_vis_attr = OpenMaya.MFnNumericAttribute()

        cls.barMaxVisibility = max_vis_attr.create(
            "barMaxVisibility", "maxV", OpenMaya.MFnNumericData.kBoolean,
            ValueBarLocatorData.barMaxVisibility
        )

        # max value
        max_val_attr = OpenMaya.MFnNumericAttribute()

        cls.barMaxValue = max_val_attr.create(
            "barMaxValue", "max", OpenMaya.MFnNumericData.kFloat,
            ValueBarLocatorData.barMaxValue
        )

        # max color
        max_col_attr = OpenMaya.MFnNumericAttribute()

        cls.barMaxColor = max_col_attr.create(
            "barMaxColor", "maxC", OpenMaya.MFnNumericData.k3Double,
        )

        max_col_attr.usedAsColor = True
        max_col_attr.default = ValueBarLocatorData.barMaxColor

        # create attr hierarchy
        comp_attr.addChild(cls.barHasMax)
        comp_attr.addChild(cls.barMaxVisibility)
        comp_attr.addChild(cls.barMaxValue)
        comp_attr.addChild(cls.barMaxColor)

        # add comp attr
        res = cls.addAttribute(cls.barMaxComp)

        return res

    def __init__(self):
        OpenMayaUI.MPxLocatorNode.__init__(self)

#     def setDependentsDirty(self, dirtyPlug, plugArray):
#         #- This code shows how to make a dynamic attribute (dynAttr)
#         #- affect a static attribute (output)
#
#         #- Check if the dynamic attribute is set to dirty by Maya
#         if dirtyPlug == self.inputValue:
#             print "poop"
#
#         if dirtyPlug == self.localPositionX:
#             print "test"

    def preEvaluation(self, context, evaluation_node):
        """
        ** super important!! **

        this is what causes our dirty inputValue attr to trigger draw calls
        such as if the attr is animated or connected
        saves having to set "isAlwaysDirty" flag

        TODO compare how well this optimizes over isAlwaysDirty (if at all?)
        """

        if context.isNormal():
            if evaluation_node.dirtyPlugExists(self.inputValue):
                OpenMayaRender.MRenderer.setGeometryDrawDirty(
                    self.thisMObject()
                )


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

    def _get_attr_float(self, node, attr_name):
        """Get attribute value via plug.
        """
        attr = getattr(ValueBarLocator, attr_name)
        default_value = getattr(ValueBarLocatorData, attr_name)

        plug = OpenMaya.MPlug(node, attr)

        if plug.isNull:
            return default_value

        return plug.asFloat()

    def _get_attr_bool(self, node, attr_name):
        """Get attribute value via plug.
        """
        attr = getattr(ValueBarLocator, attr_name)
        default_value = getattr(ValueBarLocatorData, attr_name)

        plug = OpenMaya.MPlug(node, attr)

        if plug.isNull:
            return default_value

        return plug.asBool()

    def _get_attr_float_multi(self, node, attr_name):
        """Get multi attribute value via plug.
        """
        attr = getattr(ValueBarLocator, attr_name)
        default_value = getattr(ValueBarLocatorData, attr_name)

        plug = OpenMaya.MPlug(node, attr)

        if plug.isNull:
            return default_value

        child_count = plug.numChildren()

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

        node = dag_path.node()

        data.inputValue = self._get_input_value(node)
        data.barWidth = self._get_input_bar_width(node)
        data.barAim = self._get_input_bar_aim(node)
        data.barUp = self._get_input_bar_up(node)
        data.barColor = self._get_input_bar_color(node)
        data.barAlpha = self._get_attr_float(node, "barAlpha")

        # min
        data.barHasMin = self._get_attr_bool(node, "barHasMin")
        data.barMinVisibility = self._get_attr_bool(node, "barMinVisibility")
        data.barMinValue = self._get_attr_float(node, "barMinValue")
        data.barMinColor = self._get_attr_float_multi(node, "barMinColor")

        # max
        data.barHasMax = self._get_attr_bool(node, "barHasMax")
        data.barMaxVisibility = self._get_attr_bool(node, "barMaxVisibility")
        data.barMaxValue = self._get_attr_float(node, "barMaxValue")
        data.barMaxColor = self._get_attr_float_multi(node, "barMaxColor")

        # calculate values
        data.start_point = OpenMaya.MPoint(0.0, 0.0, 0.0)

        data.aim_vector = OpenMaya.MVector(*data.barAim).normalize()
        data.up_vector = OpenMaya.MVector(*data.barUp).normalize()

        # use cross product to get normal vector
        # (direction the face points towards)
        data.normal_vector = (
            data.aim_vector ^ data.up_vector
        ) ^ data.aim_vector

        # get values
        if data.barHasMin:
            data.start_value = data.barMinValue
        else:
            data.start_value = 0.0

        if data.barHasMin and data.inputValue < data.barMinValue:
            data.end_value = data.barMinValue
        elif data.barHasMax and data.inputValue > data.barMaxValue:
            data.end_value = data.barMaxValue
        else:
            data.end_value = data.inputValue

        data.bar_height = data.end_value - data.start_value

        data.bar_center_point = OpenMaya.MPoint(
            data.aim_vector * (
                (data.bar_height * 0.5) + data.start_value
            )
        )

        # min values
        data.min_bar_height = (
            data.inputValue - data.barMinValue
        ) * -1.0

        data.min_center_point = OpenMaya.MPoint(
            data.aim_vector * (
                data.barMinValue - (data.min_bar_height * 0.5)
            )
        )

        # max values
        data.max_bar_height = data.inputValue - data.barMaxValue

        data.max_center_point = OpenMaya.MPoint(
            data.aim_vector * (
                data.barMaxValue + (data.max_bar_height * 0.5)
            )
        )

        # MColors
        data.bar_m_color = OpenMaya.MColor(
            data.barColor + [data.barAlpha]
        )

        data.min_m_color = OpenMaya.MColor(
            data.barMinColor + [data.barAlpha]
        )

        data.max_m_color = OpenMaya.MColor(
            data.barMaxColor + [data.barAlpha]
        )

        return data

    def hasUIDrawables(self):
        return True

    def addUIDrawables(self, objPath, drawManager, frameContext, cache_data):
        """
        Draw some stuff.

        drawManager = OpenMayaRender.MUIDrawManager

        drawManager handles the drawing of stuff in Viewport 2.0, such as OpenGl calls

        TODO cache calculated values

        """

        if not isinstance(cache_data, ValueBarLocatorData):
            return

        drawManager.beginDrawable()

        # draw bar rectangle
        drawManager.setColor(cache_data.bar_m_color)

        drawManager.rect(
            cache_data.bar_center_point,
            cache_data.aim_vector,
            cache_data.normal_vector,
            cache_data.barWidth,
            cache_data.bar_height * 0.5,
            True,  # filled = True
        )

        # draw max rectangle
        if cache_data.barMaxVisibility:
            if cache_data.barHasMax and cache_data.inputValue > cache_data.barMaxValue:

                drawManager.setColor(cache_data.max_m_color)

                drawManager.rect(
                    cache_data.max_center_point,
                    cache_data.aim_vector,
                    cache_data.normal_vector,
                    cache_data.barWidth,
                    cache_data.max_bar_height * 0.5,
                    True,  # filled = True
                )

        # draw min rectangle
        if cache_data.barMinVisibility:
            if cache_data.barHasMin and cache_data.inputValue < cache_data.barMinValue:

                drawManager.setColor(cache_data.min_m_color)

                drawManager.rect(
                    cache_data.min_center_point,
                    cache_data.aim_vector,
                    cache_data.normal_vector,
                    cache_data.barWidth,
                    cache_data.min_bar_height * 0.5,
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
