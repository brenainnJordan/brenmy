"""stuff
"""

from maya import cmds

from brenpy.core import bpObjects
from brenpy.core import bpTypedObjects

from brenpy.core import bpDebug
from brenmy.build import bmBuild


class BmNodeDependencyReference(bpObjects.BpValueLooseDependencyReference):
    def __init__(self, *args, **kwargs):
        super(BmNodeDependencyReference, self).__init__(*args, **kwargs)

    def valid(self):
        if self.get() is None:
            return False

        return cmds.objExists(self.get())


class BmCmdsBuildBase(
    bpDebug.BpDebugObject,
    bpObjects.BpValueDependant
):
    def __init__(self, *args, **kwargs):
        name = self.parse_kwarg("name", kwargs, bpTypedObjects.BP_BASESTRING_FILTER, dependency=True)

        super(BmCmdsBuildBase, self).__init__(*args, **kwargs)

        self.add_dependency(name)

        self._node_dependencies = []
        self._built_nodes = []

        # status
        self._is_built = False
        self._is_building = False

        # TODO
        self._name_rule = None

    @classmethod
    def parse_node_kwarg(cls, key_word, kwargs):
        reference = cls.parse_kwarg(
            key_word, kwargs, bpTypedObjects.BP_BASESTRING_FILTER, dependency=False, default_value=None
        )

        node_reference = BmNodeDependencyReference(name=key_word, type_filter=bpTypedObjects.BP_BASESTRING_FILTER)
        node_reference.set(reference.get())

        return node_reference

    def add_node_dependency(self, value):
        res = self.add_loose_dependency(value)

        if res:
            self._node_dependencies.append(value)

        return res

    def get_node_dependency(self, name):
        return self.get_loose_dependency(name)

    def node_dependencies(self):
        return self._node_dependencies

    def name(self):
        return self.get_dependency("name")

    def built_nodes(self):
        return self._built_nodes

    def create_node(
            self, node_type, name=None, name_separator="_", parent=None,
            use_type_suffix=True, type_suffix=None, type_separator="_"
    ):
        """
        TODO check node type
            check name (enforce name rules where neccesary, eg camelCase vs underscores etc.)

        """

        if name is not None:
            if name_separator is not None:
                node_name = name_separator.join([self.name().get(), name])
            else:
                node_name = "{}{}".format(self.name().get(), name)
        else:
            node_name = self.name().get()

        if use_type_suffix:
            if type_suffix is None:
                type_suffix = node_type

            if type_separator is not None:
                node_name = type_separator.join([node_name, type_suffix])
            else:
                node_name = "{}{}".format(node_name, type_suffix)

        node = cmds.createNode(node_type, name=node_name, parent=parent)

        self.debug("Node created: {}".format(node), level=self.LEVELS.mid())

        self._built_nodes.append(node)

        return node

    def set_attr(self, node, long_name, *args, **kwargs):
        self.debug(
            "setAttr: {}.{} {}, {}".format(node, long_name, args, kwargs), level=self.LEVELS.low()
        )

        cmds.setAttr(
            "{}.{}".format(node, long_name),
            *args, **kwargs
        )

        return True

    def connect_attr(self, src_node, src_attr, dst_node, dst_attr, **kwargs):
        self.debug(
            "connectAttr: {}.{} -> {}.{}, {}".format(src_node, src_attr, dst_node, dst_attr, kwargs),
            level=self.LEVELS.low()
        )

        cmds.connectAttr(
            "{}.{}".format(src_node, src_attr),
            "{}.{}".format(dst_node, dst_attr),
            **kwargs
        )
        return True

    def _validate_input_nodes(self, err=True):
        for node_dependency in self.node_dependencies():
            if not node_dependency.valid():
                msg = "Node dependency invalid: {} ({})".format(node_dependency.name(), node_dependency.get())
                if err:
                    raise bmBuild.BmBuildError(msg)
                else:
                    self.debug(msg, level=self.LEVELS.mid())
                    return False
            else:
                self.debug(
                    "Node dependency valid: {} {}".format(node_dependency.name(), node_dependency.get()),
                    level=self.LEVELS.low()
                )

        return True

    def _create_nodes(self):
        pass

    def _create_attributes(self):
        pass

    def _set_node_values(self):
        pass

    def _connect_nodes(self):
        pass

    def is_built(self):
        return self._is_built

    def is_building(self):
        return self._is_building

    def build(self):
        if self.is_built():
            raise bmBuild.BmBuildError("Cannot build once already built")

        if self.is_building():
            raise bmBuild.BmBuildError("Cannot build while still building")

        self._is_building = True
        self.debug("Beginning build: {}".format(self.name().get()))

        self._validate_input_nodes(err=True)
        self._create_nodes()
        self._create_attributes()
        self._set_node_values()
        self._connect_nodes()

        self._is_building = False
        self._is_built = True

        self.debug("Build complete: {}".format(self.name().get()))

        return True
