"""Build nodes to intersect a ray from a transform to a plane defined by a second transform.

Based on tutorial from Marco D'ambros:
https://vimeo.com/59896276

"""

from brenmy.build import bmCmdsBuild


class BmPlaneIntersectorBuild(bmCmdsBuild.BmCmdsBuildBase):
    def __init__(self, name, plane_transform, ray_transform):
        super(BmPlaneIntersectorBuild, self).__init__(name)

        self._plane_transform = plane_transform
        self._ray_transform = ray_transform

        self._create_output_transform = True
        self._attribute_node = None
        self._ray_vector = [0,0,1]
        self._plane_normal = [0, 1, 0]

    def create_output_transform(self):
        return self._create_output_transform

    def set_create_output_transform(self, value):
        self._create_output_transform = int(value)

    def plane_normal(self):
        return self._plane_normal

    def set_plane_normal(self, value):
        """TODO check value"""
        self._plane_normal = value

    def ray_vector(self):
        return self._ray_vector

    def set_ray_vector(self, value):
        """TODO check value"""
        self._ray_vector = value

    def attribute_node(self):
        return self._attribute_node

    def set_attribute_node(self, value):
        self._attribute_node = value

    def build_output_transform(self):
        pass

    def _create_nodes(self):
        # create nodes
        self._origin_decomp = self.create_node("origin", "decomposeMatrix")
        self._plane_decomp = self.create_node("plane", "decomposeMatrix")

        self._origin_ray_vector_product = self.create_node("originRay", "vectorProduct")
        self._plane_vector_product = self.create_node("planeNormal", "vectorProduct")

        # vector from origin to plane transform
        self._origin_plane_vector = self.create_node("originPlaneVector", "plusMinusAverage")

        # dot product between plane normal and origin plane vector
        self._op_pn_dot_product = self.create_node("opPnDot", "vectorProduct")

        # dot product between ray vector and plane normal
        self._ray_plane_dot_product = self.create_node("rayPlaneDot", "vectorProduct")

        # check if ray and plane are parallel to avoid dividing by zero
        self._angle_check_condition = self.create_node("angleCheck", "condition")

        # divide above dot products to give us the distance from origin to plane along ray
        self._ray_dot_divide = self.create_node("rayDotDivide", "multiplyDivide")

        # multiply normalized ray with divide result
        self._intersect_mult = self.create_node("intersectMult", "multiplyDivide")

        # offset intersect result by origin
        self._intersect_offset = self.create_node("intersectOffset", "plusMinusAverage")

    def _set_node_values(self):
        self.set_attr(self._origin_ray_vector_product, "input1", *self._ray_vector)
        self.set_attr(self._origin_ray_vector_product, "normalizeOutput", True)
        self.set_attr(self._origin_ray_vector_product, "operation", 3) # vecto matrix mult

        self.set_attr(self._plane_vector_product, "input1", *self._plane_normal)
        self.set_attr(self._plane_vector_product, "normalizeOutput", True)
        self.set_attr(self._plane_vector_product, "operation", 3)  # vecto matrix mult

        self.set_attr(self._origin_plane_vector, "operation", 2) # subtract

        self.set_attr(self._angle_check_condition, "operation", 0) # equal
        self.set_attr(self._angle_check_condition, "colorIfTrue", 1, 0, 0)
        self.set_attr(self._angle_check_condition, "colorIfFalse", 2, 0, 0)


    def _connect_nodes(self):
        self.connect_attr(self._ray_transform, "worldMatrix[0]", self._origin_decomp, "inputMatrix")
        self.connect_attr(self._ray_transform, "worldMatrix[0]", self._origin_ray_vector_product, "matrix")

        self.connect_attr(self._plane_transform, "worldMatrix[0]", self._plane_decomp, "inputMatrix")
        self.connect_attr(self._plane_transform, "worldMatrix[0]", self._plane_vector_product, "matrix")

        self.connect_attr(self._plane_decomp, "outputTranslate", self._origin_plane_vector, "input3D[0]")
        self.connect_attr(self._origin_decomp, "outputTranslate", self._origin_plane_vector, "input3D[1]")

        self.connect_attr(self._origin_plane_vector, "output3D", self._op_pn_dot_product, "input1")
        self.connect_attr(self._plane_vector_product, "output", self._op_pn_dot_product, "input2")

        self.connect_attr(self._origin_ray_vector_product, "output", self._ray_plane_dot_product, "input1")
        self.connect_attr(self._plane_vector_product, "output", self._ray_plane_dot_product, "input2")

        self.connect_attr(self._ray_plane_dot_product, "outputX", self._angle_check_condition, "firstTerm")

        self.connect_attr(self._angle_check_condition, "outColorR", self._ray_dot_divide, "operation")
        self.connect_attr(self._op_pn_dot_product, "output", self._ray_dot_divide, "input1")
        self.connect_attr(self._ray_plane_dot_product, "output", self._ray_dot_divide, "input2")

        self.connect_attr(self._origin_ray_vector_product, "output", self._intersect_mult, "input1")
        self.connect_attr(self._ray_dot_divide, "output", self._intersect_mult, "input2")

        self.connect_attr(self._origin_decomp, "outputTranslate", self._intersect_offset, "input3D[0]")
        self.connect_attr(self._intersect_mult, "output", self._intersect_offset, "input3D[1]")

    def build(self):
        res = super(BmPlaneIntersectorBuild, self).build()
        return res
