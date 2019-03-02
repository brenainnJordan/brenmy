'''
Created on 14 Jul 2018

@author: Bren

from maya import cmds


https://help.autodesk.com/view/MAYAUL/2017/ENU/?guid=__py_ref_scripted_2py_foot_print_node_8py_example_html


cmds.delete(test)

cmds.flushUndo()
cmds.unloadPlugin("PlyPointCloud.py")

cmds.loadPlugin(r"E:\dev\python\maya_sandbox\src\testing\plugins\PlyPointCloud.py")

test = cmds.createNode("plyPointCloud")


'''

import sys
from maya.api import OpenMaya, OpenMayaUI, OpenMayaAnim, OpenMayaRender


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


class PlyPointCloud(OpenMayaUI.MPxLocatorNode):
    name = "plyPointCloud"
    id = OpenMaya.MTypeId(0x80008)
    drawDbClassification = "drawdb/geometry/PlyPointCloud"
    drawRegistrantId = "PlyPointCloudPlugin"

    @staticmethod
    def creator():
        return PlyPointCloud()

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


class PlyPointCloudData(OpenMaya.MUserData):
    """ Construct some initial user data to be passed around by the DrawManager
    """

    def __init__(self):
        OpenMaya.MUserData.__init__(self, False)  # don't delete after draw

        self._vertex_positions = []
        self._vertex_normals = []
        self._vertex_colors = []

        self._file_path = r"F:\Bren\Media\2018\11_redmire_kitchen_scan\scan_001\scan_004.0.ply"
        self.read(self._file_path)

    def vertex_positions(self):
        return self._vertex_positions

    def vertex_normals(self):
        return self._vertex_normals

    def vertex_colors(self):
        return self._vertex_colors

    def read(self, file_path):
        f = open(file_path, 'r')
        lines = f.read().splitlines()

        header = True

        for line in lines:

            if not header:
                l = [i for i in line.split(' ') if i != ""]
                fL = [float(i) for i in l]
                self._vertex_positions.append(fL[0:3])
                self._vertex_normals.append(fL[3:6])
                self._vertex_colors.append([i / 255.0 for i in fL[6:9]])

            if 'end_header' in line:
                header = False


class PlyPointCloudDrawOverride(OpenMayaRender.MPxDrawOverride):
    """ This handles the actually drawing of stuff.
    """
    @staticmethod
    def creator(obj):
        return PlyPointCloudDrawOverride(obj)

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
        if not isinstance(data, PlyPointCloudData):
            data = PlyPointCloudData()

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

        if not isinstance(data, PlyPointCloudData):
            return

        drawManager.beginDrawable()

        # draw some points
        drawManager.setPointSize(2.0)

        for color, point in zip(data.vertex_colors(), data.vertex_positions()):
            drawManager.setColor(
                OpenMaya.MColor(color)
            )

            drawManager.point(
                OpenMaya.MPoint(*point)
            )

        drawManager.endDrawable()


def initializePlugin(obj):
    #plugin = OpenMaya.MFnPlugin(obj, "Autodesk", "3.0", "Any")
    plugin = OpenMaya.MFnPlugin(obj)

    try:
        plugin.registerNode(PlyPointCloud.name, PlyPointCloud.id, PlyPointCloud.creator,
                            PlyPointCloud.initialize, OpenMaya.MPxNode.kLocatorNode, PlyPointCloud.drawDbClassification)
    except:
        sys.stderr.write("Failed to register node\n")
        raise Exception("poop bags")

    try:
        OpenMayaRender.MDrawRegistry.registerDrawOverrideCreator(
            PlyPointCloud.drawDbClassification, PlyPointCloud.drawRegistrantId, PlyPointCloudDrawOverride.creator)
    except:
        sys.stderr.write("Failed to register override\n")
        raise Exception("poop bags")


def uninitializePlugin(obj):
    plugin = OpenMaya.MFnPlugin(obj)

    try:
        plugin.deregisterNode(PlyPointCloud.id)
    except:
        sys.stderr.write("Failed to deregister node\n")
        raise Exception("poop bags")

    try:
        OpenMayaRender.MDrawRegistry.deregisterDrawOverrideCreator(
            PlyPointCloud.drawDbClassification, PlyPointCloud.drawRegistrantId)
    except:
        sys.stderr.write("Failed to deregister override\n")
        raise Exception("poop bags")
