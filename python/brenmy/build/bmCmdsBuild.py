from maya import cmds

from brenpy.core import bpDebug
from brenmy.build import bmBuild

class BmCmdsBuildBase(bpDebug.BpDebugObject):
    def __init__(self, name):
        super(BmCmdsBuildBase, self).__init__()
        self._name = name
        self._input_nodes = []
        self._nodes = []

        # TODO
        self._name_rule = None

    def add_input_nodes(self, values):
        self._input_nodes += list(values)

    def input_nodes(self):
        return self._input_nodes

    def append_input_node(self, value):
        self._input_nodes.append(value)

    def name(self):
        return self._name

    def nodes(self):
        return self._nodes

    def create_node(self, name, node_type):
        """
        TODO check node type
            check name (enforce name rules where neccesary, eg camelCase vs underscores etc.)

        """
        node = cmds.createNode(
            node_type, name="{}_{}_{}".format(self._name, name, node_type)
        )

        self.debug("Node created: {}".format(node), level=self.LEVELS.low())

        self._nodes.append(node)

        return node

    def set_attr(self, node, long_name, *args, **kwargs):
        cmds.setAttr(
            "{}.{}".format(node, long_name),
            *args, **kwargs
        )
        return True

    def connect_attr(self, src_node, src_attr, dst_node, dst_attr, **kwargs):
        cmds.connectAttr(
            "{}.{}".format(src_node, src_attr),
            "{}.{}".format(dst_node, dst_attr),
            **kwargs
        )
        return True

    def _validate_input_nodes(self, err=True):
        for node in self._input_nodes:
            if not cmds.objExists(node):
                if err:
                    raise bmBuild.BmBuildError(
                        "Input node not found: {}".format(node)
                    )
                else:
                    return False

        return True

    def _create_nodes(self):
        pass

    def _create_attributes(self):
        pass

    def _set_node_values(self):
        pass

    def _connect_nodes(self):
        pass

    def build(self):
        self._validate_input_nodes(err=True)
        self._create_nodes()
        self._create_attributes()
        self._set_node_values()
        self._connect_nodes()
        return True
