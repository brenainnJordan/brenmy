"""

import sys

for path in [
    r"D:\Repos\brenmy\sandbox\python\scripts",
    r"D:\Dev\maya\numpy\numpy-1.13.1+mkl-cp27-none-win_amd64"
]:
    if path not in sys.path:
        sys.path.append(path)

from bmSandbox import sym_topo_test_01
reload(sym_topo_test_01)
sym_topo_test_01.sym_topo_test1()


TODO we seem to have an incorrectly mapped edge somehow

Failed to map face_b: f[5247], e[10688], v[5436]
map face_a ref: f[11243], e[22808], v[11564]

mesh = "Head_mirrored8"

for i in [
    "f[5247]", "e[10688]", "vtx[5436]",
    "f[11243]", "e[22808]", "vtx[11564]"
]:
    cmds.select("{}.{}".format(mesh, i), add=True)

"""
from maya import cmds
from maya.api import OpenMaya
import numpy


class QuadMap(object):
    """Maps out the vertex and edge ids into logical descriptors.

    """

    def __init__(self, dag, face_id, edge_0_id, vert_0_id):
        self.dag = dag
        self.face_id = face_id
        self.edge_0 = edge_0_id
        self.vert_0 = vert_0_id

        it_poly = OpenMaya.MItMeshPolygon(self.dag)

        # get face verts and edges
        it_poly.setIndex(self.face_id)

        self.vert_ids = it_poly.getVertices()

        if len(self.vert_ids) != 4:
            raise Exception(
                "Face does not have 4 vertices: {}.f[{}]".format(
                    self.dag.partialPathName(),
                    face_id
                )
            )

        if vert_0_id not in self.vert_ids:
            cmds.select(
                [
                    "{}.f[{}]".format(self.dag.partialPathName(), face_id),
                    "{}.vtx[{}]".format(self.dag.partialPathName(), vert_0_id)
                ],
                add=True
            )

            raise Exception(
                "Vert 0 not found in face vertices: {0}.f[{1}], ({0}.vtx[{2}])".format(
                    self.dag.partialPathName(),
                    face_id, vert_0_id
                )
            )

        self.edge_ids = it_poly.getEdges()

        if len(self.edge_ids) != 4:
            raise Exception(
                "Face does not have 4 edges: {}.f[{}]".format(
                    self.dag.partialPathName(),
                    face_id
                )
            )

        if edge_0_id not in self.edge_ids:
            cmds.select(
                [
                    "{}.f[{}]".format(self.dag.partialPathName(), face_id),
                    "{}.e[{}]".format(self.dag.partialPathName(), edge_0_id)
                ],
                #                 add=True
            )

            raise Exception(
                "Edge 0 not found in face edges: {0}.f[{1}], ({0}.e[{2}])".format(
                    self.dag.partialPathName(),
                    face_id, edge_0_id
                )
            )

        # map edges
        it_edge = OpenMaya.MItMeshEdge(self.dag)
        it_edge.setIndex(self.edge_0)

        connected_edges = it_edge.getConnectedEdges()

        self.adjacent_edges = [
            i for i in connected_edges if i in self.edge_ids
        ]

        if len(self.adjacent_edges) != 2:
            raise Exception(
                "Failed to map adjacent edges: {}.f[{}]".format(
                    self.dag.partialPathName(),
                    face_id
                )
            )

        self.opposite_edge = [
            i for i in self.edge_ids if i is not edge_0_id and i not in self.adjacent_edges
        ][0]

        # vert_0_id must be either one of connected edges
        if vert_0_id == it_edge.vertexId(0):
            self.vert_1 = it_edge.vertexId(1)
        elif vert_0_id == it_edge.vertexId(1):
            self.vert_1 = it_edge.vertexId(0)
        else:
            raise Exception("vert_0 must be a vertex connected to edge_0")

        # identify adjacent edges
        it_vert = OpenMaya.MItMeshVertex(self.dag)
        it_vert.setIndex(self.vert_0)

        vert_0_edges = it_vert.getConnectedEdges()

        # find adjacent edge connected to vert 0
        self.vert_0_adjacent_edge = [
            i for i in vert_0_edges if i in self.adjacent_edges
        ]

        if not len(self.vert_0_adjacent_edge):
            raise Exception(
                "Failed to map vert_0_adjacent_edge: {}.f[{}]".format(
                    self.dag.partialPathName(),
                    face_id
                )
            )

        self.vert_0_adjacent_edge = self.vert_0_adjacent_edge[0]

        # find adjacent edge connected to vert 1
        self.vert_1_adjacent_edge = [
            i for i in self.adjacent_edges if i != self.vert_0_adjacent_edge
        ]

        if not len(self.vert_1_adjacent_edge):
            raise Exception(
                "Failed to map vert_1_adjacent_edge: {}.f[{}]".format(
                    self.dag.partialPathName(),
                    face_id
                )
            )

        self.vert_1_adjacent_edge = self.vert_1_adjacent_edge[0]

        # identify remaining verts
        it_edge.setIndex(self.vert_0_adjacent_edge)

        if it_edge.vertexId(0) == self.vert_0:
            self.vert_2 = it_edge.vertexId(1)
        else:
            self.vert_2 = it_edge.vertexId(0)

        self.vert_3 = [
            i for i in self.vert_ids if i not in [
                self.vert_0, self.vert_1, self.vert_2
            ]
        ][0]


class SymTopo(object):
    """

    """

    def __init__(self):
        # get selected edges
        # assuming middle edges are currently selected
        self.sel = OpenMaya.MGlobal.getActiveSelectionList()

        self.dag, self.comp_obj = self.sel.getComponent(0)

        self.middle_edge_component = OpenMaya.MFnSingleIndexedComponent(
            self.comp_obj
        )

        print self.middle_edge_component.componentType
        print OpenMaya.MFn.kMeshEdgeComponent == self.middle_edge_component.componentType

        self.middle_edges = self.middle_edge_component.getElements()
        self.middle_verts = []

        # initialize iterators
        self.it_edge = OpenMaya.MItMeshEdge(self.dag)
        self.it_poly = OpenMaya.MItMeshPolygon(self.dag)
        self.it_vert = OpenMaya.MItMeshVertex(self.dag)
        self.it_face_vert = OpenMaya.MItMeshFaceVertex(self.dag)

        # begin mapping
        self.mapped_verts = []
        self.mapped_edges = []
        self.mapped_faces = []

        self.vertex_mapping = []
        self.edge_mapping = []
        self.face_mapping = []

        self.faces_a = []
        self.faces_b = []

        self.verts_a = []
        self.verts_b = []

        self.edges_a = []
        self.edges_b = []

        # map middle verts/edges to themselves
        for edge_id in self.middle_edges:
            self.it_edge.setIndex(edge_id)
            vert_0 = self.it_edge.vertexId(0)
            vert_1 = self.it_edge.vertexId(1)

            self.add_edge_mapping(edge_id, edge_id)

            for vert in vert_0, vert_1:
                if vert in self.mapped_verts:
                    continue

                self.middle_verts.append(vert)
                self.add_vertex_mapping(vert, vert)

        # start with first edge
        print "first edge: {}".format(self.middle_edges[0])

        self.map_center_edge(self.middle_edges[0])

        # map first face
        print "first faces: {} {}".format(*self.face_mapping[0])

        try:
            self.map_quad_faces(*self.face_mapping[0])
        except:
            print "poop"
            print self.face_mapping
            raise

    def map_center_edge(self, edge_id):
        # get connected faces
        # this should be 2 faces on either side of edge
        # so this is an easy map
        it_edge = OpenMaya.MItMeshEdge(self.dag)
        it_edge.setIndex(edge_id)

        face_ids = it_edge.getConnectedFaces()

        # only thing is we have nothing to indicate
        # which "direction" this mapping is going from and to
        # we can just pick one and go from there
        self.add_face_mapping(face_ids[0], face_ids[1])

    def map_quad_faces(self, face_a, face_b):
        it_poly = OpenMaya.MItMeshPolygon(self.dag)

        # get face a edges
        it_poly.setIndex(face_a)
        edge_ids_a = it_poly.getEdges()

        if len(edge_ids_a) != 4:
            raise Exception("poop")

        # look for mapped edges and go from there
        for edge_id in edge_ids_a:

            if edge_id in self.mapped_edges:
                mapped_edge = self.get_mapped_edge(edge_id)

                if mapped_edge is None:
                    raise Exception("Failed to find mapped edge")

                it_edge = OpenMaya.MItMeshEdge(self.dag)
                it_edge.setIndex(edge_id)

                vert_0 = it_edge.vertexId(0)

                mapped_vert_0 = self.get_mapped_vertex(vert_0)

                if mapped_vert_0 is None:
                    # TODO
                    raise Exception("Failed to find mapped vert")

                try:
                    quad_map_a = QuadMap(
                        self.dag, face_a, edge_id, vert_0
                    )
                except:
                    print "Failed to map face_a"
                    raise

                try:
                    quad_map_b = QuadMap(
                        self.dag, face_b, mapped_edge, mapped_vert_0
                    )
                except:

                    print "Failed to map face_b: f[{}], e[{}], v[{}]".format(
                        face_b, mapped_edge, mapped_vert_0
                    )

                    print "map face_a ref: f[{}], e[{}], v[{}]".format(
                        face_a, edge_id, vert_0
                    )

#                     cmds.select(
#                         [
#                             "{}.f[{}]".format(self.dag.partialPathName(), i)
#                             for i in self.mapped_faces
#                         ],
#                         add=True
#                     )
                    raise

                for vert_a, vert_b in [
                    (
                        quad_map_a.vert_2,
                        quad_map_b.vert_2
                    ),
                    (
                        quad_map_a.vert_3,
                        quad_map_b.vert_3
                    )
                ]:
                    if vert_a not in self.verts_a:
                        self.add_vertex_mapping(vert_a, vert_b)

                for edge_a, edge_b in [
                    (
                        quad_map_a.vert_0_adjacent_edge,
                        quad_map_b.vert_0_adjacent_edge
                    ),
                    (
                        quad_map_a.vert_1_adjacent_edge,
                        quad_map_b.vert_1_adjacent_edge
                    ),
                    (
                        quad_map_a.opposite_edge,
                        quad_map_b.opposite_edge
                    ),
                ]:
                    if edge_a in self.edges_a:
                        continue

                    self.add_edge_mapping(edge_a, edge_b)

                    # continue mapping faces connected to mapped edges
                    it_edge.setIndex(edge_a)
                    faces_a = it_edge.getConnectedFaces()

                    it_edge.setIndex(edge_b)
                    faces_b = it_edge.getConnectedFaces()

                    if len(faces_a) == 1 or len(faces_b) == 1:
                        # we must be on mesh boundary
                        continue

                    if len(faces_a) != 2 or len(faces_b) != 2:
                        raise Exception(
                            "More than two faces connected to edge")

                    face_a_next = faces_a[0] if faces_a[0] != face_a else faces_a[1]
                    face_b_next = faces_b[0] if faces_b[0] != face_b else faces_b[1]

                    if face_a_next in self.faces_a + self.faces_b:
                        continue

                    if face_b_next in self.faces_b + self.faces_a:
                        continue

                    self.add_face_mapping(face_a_next, face_b_next)
                    self.map_quad_faces(face_a_next, face_b_next)

                return

    @staticmethod
    def get_mapped_index(index, mapping):
        """Return corresponding mapped index
        """
        for i in mapping:
            if index == i[0]:
                return i[1]
            elif index == i[1]:
                return i[0]

        return None

    def get_mapped_face(self, face_id):
        return self.get_mapped_index(face_id, self.face_mapping)

    def get_mapped_vertex(self, vert_id):
        return self.get_mapped_index(vert_id, self.vertex_mapping)

    def get_mapped_edge(self, edge_id):
        return self.get_mapped_index(edge_id, self.edge_mapping)

    def add_edge_mapping(self, edge_a, edge_b):
        for edge in edge_a, edge_b:
            if edge not in self.mapped_edges:
                self.mapped_edges.append(edge)

        self.edge_mapping.append((edge_a, edge_b))
        self.edges_a.append(edge_a)
        self.edges_b.append(edge_b)
        return True

    def add_vertex_mapping(self, vert_a, vert_b):
        for vert in vert_a, vert_b:
            if vert not in self.mapped_verts:
                self.mapped_verts.append(vert)

        self.vertex_mapping.append((vert_a, vert_b))
        self.verts_a.append(vert_a)
        self.verts_b.append(vert_b)
        return True

    def add_face_mapping(self, face_a, face_b):
        self.mapped_faces.append(face_a)
        self.mapped_faces.append(face_b)
        self.face_mapping.append((face_a, face_b))
        self.faces_a.append(face_a)
        self.faces_b.append(face_b)
        return True


def sym_topo_test1():
    sym_topo = SymTopo()
    print sym_topo.vertex_mapping
    print sym_topo.face_mapping


def mirror_sym_topo_sl():
    # get objects
    sel = OpenMaya.MGlobal.getActiveSelectionList()
    dag, comp_obj = sel.getComponent(0)

    # get points
    m_mesh = OpenMaya.MFnMesh(dag)
    points = m_mesh.getPoints()
    points = numpy.array(points)

    # get rid of redundant 4th column
    points = numpy.delete(points, 3, axis=1)

    # map topo
    sym_topo = SymTopo()

    # get points_a and mirror column 0 (x-axis)
    a_ids = [i for i in sym_topo.verts_a if i not in sym_topo.middle_verts]
    points_a = points[a_ids]

    points_a[:, 0] *= -1.0

    b_ids = [i for i in sym_topo.verts_b if i not in sym_topo.middle_verts]

    mirrored_points = numpy.array(points)
    mirrored_points[b_ids] = points_a

    # set mid points x value to 0.0
    mid_points = points[sym_topo.middle_verts]
    mid_points[:, 0] = 0.0
    mirrored_points[sym_topo.middle_verts] = mid_points

    # set points
    m_mesh.setPoints(
        OpenMaya.MPointArray(mirrored_points.tolist())
    )
