from maya import cmds
from brenmy.build import bmCmdsBuild
from brenpy.core import bpObjects
from brenpy.core import bpTypedObjects


class BmNurbsTessellate(bmCmdsBuild.BmCmdsBuildBase):
    def __init__(self, *args, **kwargs):

        surface = self.parse_node_kwarg("surface", kwargs)

        polygon_type = self.parse_kwarg(
            "polygon_type", kwargs, bpTypedObjects.BP_INT_FILTER, dependency=False, default_value=1
        )

        super(BmNurbsTessellate, self).__init__(*args, **kwargs)

        self.add_node_dependency(surface)
        self.add_loose_dependency(polygon_type)

    def surface(self):
        return self.get_node_dependency("surface")

    def polygon_type(self):
        return self.get_loose_dependency("polygon_type")

    def _create_nodes(self):
        self._nurbs_tessellate = self.create_node("nurbsTessellate", name=None)

        self._transform = self.create_node("transform", name=None, use_type_suffix=False)

        self._mesh = self.create_node(
            "mesh", name=None, parent=self._transform, type_separator=None, type_suffix="Shape"
        )

        return True

    def _set_node_values(self):
        if self.polygon_type().get() is not None:
            self.set_attr(self._nurbs_tessellate, "polygonType", self.polygon_type().get())

    def _connect_nodes(self):
        self.connect_attr(
            self.surface().get(), "worldSpace[0]",
            self._nurbs_tessellate, "inputSurface"
        )

        self.connect_attr(
            self._nurbs_tessellate, "outputPolygon",
            self._mesh, "inMesh"
        )

        return True
