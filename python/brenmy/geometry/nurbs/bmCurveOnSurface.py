"""Stuff
"""

from maya import cmds

from brenpy.core import bpObjects
from brenpy.core import bpTypedObjects
from brenmy.build import bmBuild

# TODO rework bmCmdsBuild to use value dependants etc.

class BmCurveOnSurface(bpObjects.BpValueDependant):
    def __init__(self, *args, **kwargs):

        # parse kwargs
        name = self.parse_kwarg("name", kwargs, bpObjects.BpTypeFilter(str), dependency=False)

        curve = self.parse_kwarg("curve", kwargs, bpObjects.BpTypeFilter(str), dependency=False)

        use_curve_local = self.parse_kwarg(
            "use_curve_local", kwargs, bpObjects.BpTypeFilter(bool), dependency=False, default_value=False
        )

        surface = self.parse_kwarg("surface", kwargs, bpObjects.BpTypeFilter(str), dependency=False)

        use_surface_local = self.parse_kwarg(
            "use_surface_local", kwargs, bpObjects.BpTypeFilter(bool), dependency=False, default_value=False
        )

        normal = self.parse_kwarg(
            "normal", kwargs, bpTypedObjects.BP_FLOAT_ARRAY_FILTER, dependency=False, default_value=(0,1,0)
        )

        create_curve_outputs = self.parse_kwarg(
            "create_curve_outputs", kwargs, bpObjects.BpTypeFilter(bool), dependency=False, default_value=False
        )

        create_cfs_outputs = self.parse_kwarg(
            "create_cfs_outputs", kwargs, bpObjects.BpTypeFilter(bool), dependency=False, default_value=False
        )

        super(BmCurveOnSurface, self).__init__(*args, **kwargs)

        self.add_loose_dependency(name)
        self.add_loose_dependency(curve)
        self.add_loose_dependency(use_curve_local)
        self.add_loose_dependency(surface)
        self.add_loose_dependency(use_surface_local)
        self.add_loose_dependency(normal)
        self.add_loose_dependency(create_curve_outputs)
        self.add_loose_dependency(create_cfs_outputs)

        # outputs
        self._built = False
        self._building = False
        self._var_node = None
        self._project_node = None
        self._cfs_nodes = []
        self._output_transforms = []
        self._output_shapes = []
        self._has_multiple_outputs = False

    def name(self):
        return self.get_loose_dependency("name")

    def curve(self):
        return self.get_loose_dependency("curve")

    def surface(self):
        return self.get_loose_dependency("surface")

    def normal(self):
        return self.get_loose_dependency("normal")

    def use_curve_local(self):
        return self.get_loose_dependency("use_curve_local")

    def use_surface_local(self):
        return self.get_loose_dependency("use_surface_local")

    def create_curve_outputs(self):
        return self.get_loose_dependency("create_curve_outputs")

    def create_cfs_outputs(self):
        return self.get_loose_dependency("create_cfs_outputs")

    def surface_shape(self):
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

    def cfs_nodes(self):
        return self._cfs_nodes

    def output_transforms(self):
        return self._output_transforms

    def output_shapes(self):
        return self._output_shapes

    def has_multiple_outputs(self):
        return self._has_multiple_outputs
    
    def build(self):

        if self.built() or self.building():
            raise bmBuild.BmBuildError("Build failed")

        self._building = True

        # TODO validate user values

        # project onto surface
        project_node = cmds.createNode("projectCurve", name="{}_projectCurve".format(self.name().get()))
        self._project_node = project_node

        if self.use_curve_local().get():
            cmds.connectAttr("{}.local".format(self.curve().get()), "{}.inputCurve".format(project_node))
        else:
            cmds.connectAttr("{}.worldSpace[0]".format(self.curve().get()), "{}.inputCurve".format(project_node))

        if self.use_surface_local().get():
            cmds.connectAttr("{}.local".format(self.surface().get()), "{}.inputSurface".format(project_node))
        else:
            cmds.connectAttr("{}.worldSpace[0]".format(self.surface().get()), "{}.inputSurface".format(project_node))

        cmds.setAttr("{}.useNormal".format(project_node), False)
        cmds.setAttr("{}.direction".format(project_node), *self.normal().get())

        min_tol = cmds.attributeQuery("tolerance", node=project_node, min=True)[0]
        cmds.setAttr("{}.tolerance".format(project_node), min_tol)

        # attach to surface
        var_node = cmds.createNode(
            "curveVarGroup", name="{}_curveVarGroup".format(self.name()), parent=self.surface_shape()
        )
        self._var_node = var_node

        cmds.connectAttr("{}.outputCurve".format(project_node), "{}.create".format(var_node))

        # create outputs
        # note there could be more than one if the projected curve crosses a surface boundary

        for i, output_attr in cmds.listAttr("{}.local".format(var_node), multi=True):

            if i > 0:
                self._has_multiple_outputs = True

            # create curve output
            if self.create_curve_outputs().get():
                output_transform = cmds.createNode(
                    "transform", name="{}{}".format(self.name().get(), i), parent=var_node
                )

                self._output_transforms.append(output_transform)

                output_shape = cmds.createNode(
                    "nurbsCurve", name="{}Shape".format(output_transform), parent=output_transform
                )

                self._output_shapes.append(output_shape)

                cmds.connectAttr(
                    "{}.{}".format(var_node, output_attr),
                    "{}.create".format(output_shape)
                )

            # create curve from surface node
            if self.create_cfs_outputs().get():
                cfs_node = cmds.createNode(
                    "curveFromSurfaceCoS", name="{}{}_curveFromSurfaceCoS".format(self.name(), i)
                )

                self._cfs_nodes.append(cfs_node)

                if self.use_surface_local():
                    cmds.connectAttr(
                        "{}.local".format(self.surface_shape().get()),
                        "{}.inputSurface".format(cfs_node)
                    )
                else:
                    cmds.connectAttr(
                        "{}.worldSpace[0]".format(self.surface_shape().get()),
                        "{}.inputSurface".format(cfs_node)
                    )

                cmds.connectAttr(
                    "{}.local[0]".format(var_node),
                    "{}.curveOnSurface".format(cfs_node)
                )

        self._building = False
        self._built = True

        return True
