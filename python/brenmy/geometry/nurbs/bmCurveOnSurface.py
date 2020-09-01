"""

Note that the curveVarGroup node in maya is just super convoluted.
The node will create new transform nodes at runtime if it thinks it needs to.
As such it should NOT be used for rigging!

When connecting the output to a nurbsCurve node, it seems to prompt the node to make it's own nurbs curves,
making ours redundant.

It is possible to connect the output(s) of curveVarGroup to other nodes such as curveFromSurfaceCoS node,
without connecting a nurbsCurve, and it partly works, but it seems like if the number of outputs changes
it doesn't update the multi attr output, and also seems to break existing outputs.

So with that in mind it's only really useful as a one-off operation.

"""

from maya import cmds

from brenpy.core import bpObjects
from brenpy.core import bpTypedObjects
from brenmy.build import bmBuild

# TODO rework bmCmdsBuild to use value dependants etc.

class BmProjectCurveOnSurface(bpObjects.BpValueDependant):
    def __init__(self, *args, **kwargs):

        # parse kwargs
        name = self.parse_kwarg("name", kwargs, bpObjects.BpTypeFilter(basestring), dependency=False)

        # note that we can use any curve input (eg nurbsCurve, or projectCurve etc.)
        curve_node = self.parse_kwarg("curve_node", kwargs, bpObjects.BpTypeFilter(basestring), dependency=False)

        curve_attr = self.parse_kwarg(
            "curve_attr", kwargs, bpObjects.BpTypeFilter(basestring), dependency=False, default_value="worldSpace[0]"
        )

        # but also note that we can only use a nurbsSurface input
        # because we'll be parenting transforms to it
        surface = self.parse_kwarg("surface", kwargs, bpObjects.BpTypeFilter(basestring), dependency=False)

        use_surface_local = self.parse_kwarg(
            "use_surface_local", kwargs, bpObjects.BpTypeFilter(bool), dependency=False, default_value=False
        )

        # TODO use normal option

        # TODO better filter eg bpTypedObjects.BP_FLOAT_ARRAY_FILTER
        direction = self.parse_kwarg(
            "direction", kwargs, bpObjects.BpTypeFilter((list, tuple)), dependency=False, default_value=(0,1,0)
        )

        enable_curve_outputs = self.parse_kwarg(
            "enable_curve_outputs", kwargs, bpObjects.BpTypeFilter(bool), dependency=False, default_value=True
        )

        # enable_cfs_outputs = self.parse_kwarg(
        #     "enable_cfs_outputs", kwargs, bpObjects.BpTypeFilter(bool), dependency=False, default_value=True
        # )

        # should we use the native maya command, or make nodes from scratch?
        use_cmd = self.parse_kwarg(
            "use_cmd", kwargs, bpObjects.BpTypeFilter(bool), dependency=False, default_value=True
        )

        super(BmProjectCurveOnSurface, self).__init__(*args, **kwargs)

        self.add_loose_dependency(name)
        self.add_loose_dependency(curve_node)
        self.add_loose_dependency(curve_attr)
        self.add_loose_dependency(surface)
        self.add_loose_dependency(use_surface_local)
        self.add_loose_dependency(direction)
        self.add_loose_dependency(enable_curve_outputs)
        # self.add_loose_dependency(enable_cfs_outputs)
        self.add_loose_dependency(use_cmd)

        # outputs
        self._built = False
        self._building = False
        self._var_node = None
        self._project_node = None
        self._output_cfs_nodes = []
        self._output_transforms = []
        self._output_shapes = []
        self._has_multiple_outputs = False

    def name(self):
        return self.get_loose_dependency("name")

    def curve_node(self):
        return self.get_loose_dependency("curve_node")

    def curve_attr(self):
        return self.get_loose_dependency("curve_attr")

    def surface(self):
        return self.get_loose_dependency("surface")

    def use_surface_local(self):
        return self.get_loose_dependency("use_surface_local")

    def direction(self):
        return self.get_loose_dependency("direction")

    def enable_curve_outputs(self):
        return self.get_loose_dependency("enable_curve_outputs")

    # called explicitly after refreshing outputs
    # def enable_cfs_outputs(self):
    #     return self.get_loose_dependency("enable_cfs_outputs")

    def use_cmd(self):
        return self.get_loose_dependency("use_cmd")

    def get_surface_shape(self):
        res = cmds.listRelatives(self.surface().get(), type="nurbsSurface")
        if res:
            return res[0]
        else:
            return None

    def built(self):
        return self._built

    def building(self):
        return self._building

    def var_node(self):
        return self._var_node

    def project_node(self):
        return self._project_node

    def output_cfs_nodes(self):
        return self._output_cfs_nodes

    def output_transforms(self):
        return self._output_transforms

    def output_shapes(self):
        return self._output_shapes

    def has_multiple_outputs(self):
        return self._has_multiple_outputs

    def refresh_outputs(self):
        """Populate output list with current transforms created by var group node.

        Note this seems to be the only reliable way to keep track of these,
        and must be called after other stuff in the scene has prompted the node to update.

        Also note this is kinda flaky.

        This seems to be consistent whether using the native maya command,
        or by creating nodes from scratch.
        """
        self._output_transforms = cmds.listRelatives(self._var_node)

        self._output_shapes = [
            cmds.listRelatives(i) for i in self._output_transforms
        ]

        print "TEST", self._output_transforms
        return True

    def _build_cmd(self):
        """maya built-in command
        However I don't think we can give it other inputs?
        """
        var_node, project_node = cmds.projectCurve(
            self.curve_node().get(),
            self.surface().get(),
            useNormal=False,
            direction=self.direction().get(),
            name=self.name().get()
        )

        self._var_node = "{}_curveVarGroup".format(self.name().get())
        cmds.rename(var_node, self._var_node)

        self._project_node = "{}_projectCurve".format(self.name().get())
        cmds.rename(project_node, self._project_node)

        return True

    def _create_curve_output(self, output_index):
        output_transform = "{}{}".format(self.name().get(), output_index)

        cmds.createNode(
            "transform", name=output_transform, parent=self.var_node()
        )

        output_shape = cmds.createNode(
            "nurbsCurve", name="{}Shape".format(output_transform), parent=output_transform
        )

        cmds.connectAttr(
            "{}.local[{}]".format(self.var_node(), output_index),
            "{}.create".format(output_shape)
        )

        return output_transform, output_shape

    def _create_cfs_output(self, output_index):
        cfs_node = cmds.createNode(
            "curveFromSurfaceCoS", name="{}{}_curveFromSurfaceCoS".format(self.name().get(), output_index)
        )

        if self.use_surface_local().get():
            cmds.connectAttr(
                "{}.local".format(self.get_surface_shape()),
                "{}.inputSurface".format(cfs_node)
            )
        else:
            cmds.connectAttr(
                "{}.worldSpace[0]".format(self.get_surface_shape()),
                "{}.inputSurface".format(cfs_node)
            )

        cmds.connectAttr(
            "{}.local[{}]".format(self.var_node(), output_index),
            "{}.curveOnSurface".format(cfs_node)
        )

        return cfs_node

    def create_cfs_outputs(self):
        for i, output_transform in enumerate(self.output_transforms()):
            node = self._create_cfs_output(i)
            self._output_cfs_nodes.append(node)

        return True

    def _build_nodes(self):
        """Build nodes from scratch.
        Note this is almost working, but we're stuck at creating the outputs,
        as this is handled internally by the var group node (ffs.)
        """

        # project onto surface
        project_node = cmds.createNode("projectCurve", name="{}_projectCurve".format(self.name().get()))
        self._project_node = project_node

        cmds.connectAttr(
            "{}.{}".format(self.curve_node().get(), self.curve_attr().get()),
            "{}.inputCurve".format(project_node)
        )

        if self.use_surface_local().get():
            cmds.connectAttr(
                "{}.local".format(self.surface().get()),
                "{}.inputSurface".format(project_node)
            )
        else:
            cmds.connectAttr(
                "{}.worldSpace[0]".format(self.surface().get()),
                "{}.inputSurface".format(project_node)
            )

        cmds.setAttr("{}.useNormal".format(project_node), False)
        cmds.setAttr("{}.direction".format(project_node), *self.direction().get())

        # min_tol = cmds.attributeQuery("tolerance", node=project_node, min=True)[0]
        # cmds.setAttr("{}.tolerance".format(project_node), min_tol)

        # attach to surface
        # note that createNode will return a weird name when creating curveVarGroup
        # eg. "saucer_surfaceShape->plateDivision0COS_curveVarGroup"
        # but also note that this can actually be passed into maya commands, so just wtf.
        var_node = "{}_curveVarGroup".format(self.name().get())
        self._var_node = var_node

        cmds.createNode("curveVarGroup", name=var_node, parent=self.get_surface_shape())

        cmds.connectAttr("{}.outputCurve".format(project_node), "{}.create".format(var_node))

        # create outputs
        # note there could be more than one if the projected curve crosses a surface boundary

        # calling get attr on the first output seems to be the only way to prompt
        # the node into creating an output curve
        _ = cmds.getAttr("{}.local[0]".format(var_node))

        # # subsequent calls fails to create additional curves where they would be created later
        # # calling dgdirty or refresh also fails
        # _ = cmds.getAttr("{}.local[1]".format(var_node))
        # _ = cmds.getAttr("{}.local[2]".format(var_node))

        return True

    def build(self):
        if self.built() or self.building():
            raise bmBuild.BmBuildError("Build failed")

        self._building = True

        # TODO validate user values

        if self.use_cmd().get():
            self._build_cmd()
        else:
            self._build_nodes()

        self._building = False
        self._built = True
