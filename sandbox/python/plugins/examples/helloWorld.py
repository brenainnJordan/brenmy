"""Autodesk basic example python plugin.

https://knowledge.autodesk.com/search-result/caas/CloudHelp/cloudhelp/2016/ENU/Maya-SDK/files/GUID-B968733D-B288-4DAF-9685-4676DC3E4E94-htm.html

cmds.unloadPlugin("helloWorld.py")
cmds.loadPlugin(r"D:\Repos\brenmy\python\plugins\helloWorld.py")

cmds.pyHelloWorld()

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
class PyHelloWorldCmd(om.MPxCommand):
    kPluginCmdName = "pyHelloWorld"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return PyHelloWorldCmd()

    def doIt(self, args):
        print "Hello World!"


# Initialize the plug-in
def initializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin)
    try:
        pluginFn.registerCommand(
            PyHelloWorldCmd.kPluginCmdName, PyHelloWorldCmd.cmdCreator
        )
    except:
        sys.stderr.write(
            "Failed to register command: %s\n" % PyHelloWorldCmd.kPluginCmdName
        )
        raise


# Uninitialize the plug-in
def uninitializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin)
    try:
        pluginFn.deregisterCommand(PyHelloWorldCmd.kPluginCmdName)
    except:
        sys.stderr.write(
            "Failed to unregister command: %s\n" % PyHelloWorldCmd.kPluginCmdName
        )
        raise
