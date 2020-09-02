from maya import cmds
from brenmy.build import bmCmdsBuild
from brenpy.core import bpObjects
from brenpy.core import bpTypedObjects

class PolygonType():
    triangles = 0
    quads = 1

class Format():
    count = 0
    fit = 1
    general = 2
    cvs = 3

class UVType():
    # maya attr starts from 1!
    surf_isoparms_3d = 1
    surf_isoparms = 2
    span_isoparms = 3

class BmNurbsTessellate(bmCmdsBuild.BmCmdsBuildBase):
    """

from brenmy.geometry.nurbs import bmNurbsTessellate

tessellate = bmNurbsTessellate.BmNurbsTessellate(
    name="test",
    surface="plateSurface_2_9",
    polygon_type=bmNurbsTessellate.PolygonType.quads,
    format=bmNurbsTessellate.Format.general,
    u_type=bmNurbsTessellate.UVType.surf_isoparms,
    v_type=bmNurbsTessellate.UVType.surf_isoparms,
    u_number=6,
    v_number=3,
)

tessellate.build()

    """

    DEFAULT_DEPENDENCIES = [
            ("surface_attr", bpTypedObjects.BP_BASESTRING_FILTER, "worldSpace[0]"),
            ("polygon_type", bpTypedObjects.BP_INT_FILTER, PolygonType.quads),
            ("format", bpTypedObjects.BP_INT_FILTER, Format.count),
            ("u_type", bpTypedObjects.BP_INT_FILTER, UVType.surf_isoparms),
            ("v_type", bpTypedObjects.BP_INT_FILTER, UVType.surf_isoparms),
            ("u_number", bpTypedObjects.BP_INT_FILTER, 8),
            ("v_number", bpTypedObjects.BP_INT_FILTER, 8),
        ]

    def __init__(self, *args, **kwargs):

        surface = self.parse_node_kwarg("surface", kwargs)

        super(BmNurbsTessellate, self).__init__(*args, **kwargs)

        self.add_node_dependency(surface)

    def surface(self):
        return self.get_node_dependency("surface")

    def surface_attr(self):
        return self.get_dependency("surface_attr")

    def polygon_type(self):
        return self.get_dependency("polygon_type")

    def format(self):
        return self.get_dependency("format")

    def _create_nodes(self):
        self._nurbs_tessellate = self.create_node("nurbsTessellate", name=None)

        self._transform = self.create_node("transform", name=None, use_type_suffix=False)

        self._mesh = self.create_node(
            "mesh", name=None, parent=self._transform, type_separator=None, type_suffix="Shape"
        )

        return True

    def _set_node_values(self):
        for attr, dependency_name in [
            ("polygonType", "polygon_type"),
            ("format", "format"),
            ("uType", "u_type"),
            ("vType", "v_type"),
            ("uNumber", "u_number"),
            ("vNumber", "v_number"),
        ]:
            value = self.get_dependency(dependency_name).get()

            if value is None:
                continue

            self.set_attr(self._nurbs_tessellate, attr, value)

    def _connect_nodes(self):
        self.connect_attr(
            self.surface().get(), self.surface_attr().get(),
            self._nurbs_tessellate, "inputSurface"
        )

        self.connect_attr(
            self._nurbs_tessellate, "outputPolygon",
            self._mesh, "inMesh"
        )

        # apply initial shading
        cmds.sets(self._mesh, edit=True, forceElement="initialShadingGroup")

        return True

    def output_tessellate_node(self):
        return self._nurbs_tessellate

    def output_polygon_attr(self):
        return "{}.{}".format(self._nurbs_tessellate, "outputPolygon")

    def output_mesh(self):
        return self._mesh
