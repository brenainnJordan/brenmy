'''Bits and bobs of useful code.

Created on 11 Jun 2019

@author: Bren
'''

from maya.api import OpenMaya

# node types are represented as MTypeId objects
# this is how you instance one
# but not so useful out of context
some_id = OpenMaya.MTypeId(1)
some_id.id()

# find id for transform node
# and create a node via node class id
transform_cls = OpenMaya.MNodeClass("transform")
transform_id = transform_cls.typeId

node = OpenMaya.MFnDependencyNode()

# this will error as instancing the function set class does not create a node
# so there is no object bound to the class instance
# and therfore nothing to query
node.name()
plug = node.findPlug("translateX", False)

# call create() to create a node
# this returns a MObject
blah = node.create(transform_id, name="blah")

# then cast as the function set class to utilise the methods
blah_node = OpenMaya.MFnDependencyNode(blah)
blah_node.name()
blah_plug = blah_node.findPlug("translateX", False)

# this...
# is not useful
blah_node == node
plug == blah_plug
plug.asFloat()

# but this is
blah_plug.asFloat()
