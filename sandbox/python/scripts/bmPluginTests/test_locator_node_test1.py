import subprocess

from maya import cmds

# unload
cmds.file(new=True, force=True)
cmds.flushUndo()
cmds.unloadPlugin("testLocatorNode")

# copy new build
src = r"D:\Repos\brenmy\sandbox\cpp\testLocatorNode\testLocatorNode\Release\testLocatorNode.mll"
dst = r"D:\Repos\brenmy\sandbox\testBuilds\testLocatorNode.mll"

status = subprocess.call(
    ["copy", src, dst],
    shell=True
)

# test
cmds.loadPlugin(r"testLocatorNode")
cmds.createNode("testLocatorNode")