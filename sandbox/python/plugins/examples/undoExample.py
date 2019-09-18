"""Autodesk basic example python plugin expanded with undo.

https://knowledge.autodesk.com/search-result/caas/CloudHelp/cloudhelp/2016/ENU/Maya-SDK/files/GUID-B968733D-B288-4DAF-9685-4676DC3E4E94-htm.html

cmds.flushUndo()
cmds.unloadPlugin("undoExample.py")
cmds.loadPlugin(r"D:\Repos\brenmy\sandbox\python\plugins\examples\undoExample.py")

cmds.pyUndoCmd("blah")


Reference:
https://github.com/alicevision/mayaAPI/blob/master/2016.sp1/linux/devkit/plug-ins/skinClusterWeights/skinClusterWeights.cpp
TODO see above for kQueryFlagLong, parseArgs, queryUsed etc.

"""
import sys
import maya.api.OpenMaya as om


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


# command
class PyUndoCmd(om.MPxCommand):
    kPluginCmdName = "pyUndoCmd"

    def __init__(self):
        om.MPxCommand.__init__(self)
        self._data = ""

    @staticmethod
    def cmdCreator():
        return PyUndoCmd()

    def isUndoable(self):
        return True

    def parseArgs(self, args):

        if len(args) > 0:
            self._data = args.asString(0)

    def doIt(self, args):
        self.parseArgs(args)
        print "do message: {}".format(self._data)

    def undoIt(self):
        print "undo message: {}".format(self._data)

    def redoIt(self):
        print "redo message: {}".format(self._data)


# Initialize the plug-in
def initializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin)
    try:
        pluginFn.registerCommand(
            PyUndoCmd.kPluginCmdName, PyUndoCmd.cmdCreator
        )
    except:
        sys.stderr.write(
            "Failed to register command: %s\n" % PyUndoCmd.kPluginCmdName
        )
        raise


# Uninitialize the plug-in
def uninitializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin)
    try:
        pluginFn.deregisterCommand(PyUndoCmd.kPluginCmdName)
    except:
        sys.stderr.write(
            "Failed to unregister command: %s\n" % PyUndoCmd.kPluginCmdName
        )
        raise
