"""Autodesk basic example python plugin expanded with undo.

https://knowledge.autodesk.com/search-result/caas/CloudHelp/cloudhelp/2016/ENU/Maya-SDK/files/GUID-B968733D-B288-4DAF-9685-4676DC3E4E94-htm.html

cmds.flushUndo()
cmds.unloadPlugin("bmSymMesh.py")
cmds.loadPlugin(r"D:\Repos\brenmy\python\plugins\bmSymMesh.py")

cmds.bmSymMesh()


Reference:
https://github.com/alicevision/mayaAPI/blob/master/2016.sp1/linux/devkit/plug-ins/skinClusterWeights/skinClusterWeights.cpp
TODO see above for kQueryFlagLong, parseArgs, queryUsed etc.

"""
import sys
from maya.api import OpenMaya

for path in [
    r"D:\Repos\brenmy\python",
    r"D:\Dev\maya\numpy\numpy-1.13.1+mkl-cp27-none-win_amd64"
]:
    if path not in sys.path:
        sys.path.append(path)

from brenmy.geometry import bmMeshTopology
reload(bmMeshTopology)


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


# command
class BmSymMeshCmd(OpenMaya.MPxCommand):
    """
    TODO expose mirror options.
    """
    kPluginCmdName = "bmSymMesh"

    def __init__(self):
        OpenMaya.MPxCommand.__init__(self)
        self._dag = None
        self._old_points = None
        self._mirrored_points = None

        # args
        self._reverse = False

    @staticmethod
    def cmdCreator():
        return BmSymMeshCmd()

    def isUndoable(self):
        return True

    def parseArgs(self, args):

        #         if len(args) > 0:
        #             self._data = args.asString(0)
        pass

    def doIt(self, args):
        self.parseArgs(args)

        # get selected edges
        # assuming middle edges are currently selected
        sel = OpenMaya.MGlobal.getActiveSelectionList()

        self._dag, comp_obj = sel.getComponent(0)

        middle_edge_component = OpenMaya.MFnSingleIndexedComponent(
            comp_obj
        )

        if middle_edge_component.componentType != OpenMaya.MFn.kMeshEdgeComponent:
            raise Exception("Please select full middle edge loop")

        middle_edges = middle_edge_component.getElements()

        # TODO get points only from bmMeshTopology and set points in doIt()
        self._old_points, self._mirrored_points = bmMeshTopology.mirror_sym_topo(
            self._dag.partialPathName(), middle_edges, reverse=self._reverse
        )

        return True

    def undoIt(self):

        m_mesh = OpenMaya.MFnMesh(self._dag)

        m_mesh.setPoints(
            OpenMaya.MPointArray(self._old_points.tolist())
        )

    def redoIt(self):
        m_mesh = OpenMaya.MFnMesh(self._dag)

        m_mesh.setPoints(
            OpenMaya.MPointArray(self._mirrored_points.tolist())
        )


# Initialize the plug-in
def initializePlugin(plugin):
    pluginFn = OpenMaya.MFnPlugin(plugin)
    try:
        pluginFn.registerCommand(
            BmSymMeshCmd.kPluginCmdName, BmSymMeshCmd.cmdCreator
        )
    except:
        sys.stderr.write(
            "Failed to register command: %s\n" % BmSymMeshCmd.kPluginCmdName
        )
        raise


# Uninitialize the plug-in
def uninitializePlugin(plugin):
    pluginFn = OpenMaya.MFnPlugin(plugin)
    try:
        pluginFn.deregisterCommand(BmSymMeshCmd.kPluginCmdName)
    except:
        sys.stderr.write(
            "Failed to unregister command: %s\n" % BmSymMeshCmd.kPluginCmdName
        )
        raise
