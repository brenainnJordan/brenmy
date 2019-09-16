"""

import sys

path = r"D:\Repos\brenmy\sandbox\python\scripts"
if path not in sys.path:
    sys.path.append(path)

from bmSandbox import sym_topo_test_01
reload(sym_topo_test_01)
sym_topo_test_01.sym_topo_test1()

"""

from maya.api import OpenMaya


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
        self.edge_ids = it_poly.getEdges()

        # map edges
        it_edge = OpenMaya.MItMeshEdge(self.dag)
        it_edge.setIndex(self.edge_0)

        connected_edges = it_edge.getConnectedEdges()

        self.adjacent_edges = [
            i for i in connected_edges if i in self.edge_ids]

        self.opposite_edge = [
            i for i in connected_edges if i in self.edge_ids and i not in self.adjacent_edges
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

        vert_0_edges = it_vert.connectedEdges()

        self.vert_0_adjacent_edge = [
            i for i in vert_0_edges if i in self.adjacent_edges
        ][0]

        self.vert_1_adjacent_edge = [
            i for i in self.adjacent_edges if i != self.vert_0_adjacent_edge
        ][0]

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

        self.middle_edge_component_ids = self.middle_edge_component.getElements()

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

        # map middle verts/edges to themselves
        for edge_id in self.middle_edge_component_ids:
            self.it_edge.setIndex(edge_id)
            vert_0 = self.it_edge.vertexId(0)
            vert_1 = self.it_edge.vertexId(1)

            self.mapped_edges.append(edge_id)
            self.edge_mapping.append((edge_id, edge_id))

            for vert in vert_0, vert_1:
                if vert in self.mapped_verts:
                    continue

                self.mapped_verts.append(vert)
                self.vertex_mapping.append((vert, vert))

        # start with first edge
        self.map_center_edge(self.middle_edge_component_ids[0])

        # map first face
        self.map_faces(*self.face_mapping[0])

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
        self.mapped_faces += face_ids
        self.face_mapping.append((face_ids[0], face_ids[1]))

    def map_faces(self, face_id_0, face_id_1):
        it_poly = OpenMaya.MItMeshPolygon(self.dag)

        # get face 0 verts and edges
        it_poly.setIndex(face_id_0)

        vert_ids_0 = it_poly.getVertices()
        edge_ids_0 = it_poly.getEdges()

        mapped_vert_ids_0 = [
            i for i in vert_ids_0 if i in self.mapped_verts
        ]

        mapped_edge_ids_0 = [
            i for i in edge_ids_0 if i in self.mapped_edges
        ]

        # get face 1 verts and edges
        it_poly.setIndex(face_id_1)

        vert_ids_1 = it_poly.getVertices()
        edge_ids_1 = it_poly.getEdges()

        mapped_vert_ids_1 = [
            i for i in vert_ids_1 if i in self.mapped_verts
        ]

        mapped_edge_ids_1 = [
            i for i in edge_ids_1 if i in self.mapped_edges
        ]

#         # see which verts and edges correspond
#         mapped_verts = []
#         mapped_edges = []
#
#         for vert_id in mapped_vert_ids_0:
#             mapped_vert = self.get_mapped_vertex(vert_id)
#             mapped_verts.append((vert_id, mapped_vert))
#
        # look for edge correspondances
        for edge_id in edge_ids_0:
            # TODO move to face mapping class
            # eg.
            # FaceMap(face_id, edge_0_id, vetex_0_id)

            it_edge = OpenMaya.MItMeshEdge(self.dag)
            it_edge.setIndex(edge_id)

            connected_edges = it_edge.getConnectedEdges()

            adjacent_edges = [i for i in connected_edges if i in edge_ids_0]

            opposite_edge = [
                i for i in connected_edges if i in edge_ids_0 and i not in adjacent_edges
            ][0]

            vert_0 = it_edge.vertexId(0)
            vert_1 = it_edge.vertexId(1)

            it_vert = OpenMaya.MItMeshVertex(self.dag)
            it_vert.setIndex(vert_0)

            vert_0_edges = it_vert.connectedEdges()

            vert_0_adjacent_edge = [
                i for i in vert_0_edges if i in adjacent_edges
            ][0]

            vert_1_adjacent_edge = [
                i for i in adjacent_edges if i != vert_0_adjacent_edge
            ][0]

            it_edge.setIndex(vert_0_adjacent_edge)

            if it_edge.vertexId(0) == vert_0:
                vert_2 = it_edge.vertexId(1)
            else:
                vert_2 = it_edge.vertexId(0)

            vert_3 = [
                i for i in vert_ids_0 if i not in [vert_0, vert_1, vert_2]
            ][0]

            if edge_id in self.mapped_edges:
                continue

            # find edges connected to mapped edges

            # see if this edge is connected to a mapped edge
            for connected_edge in connected_edges:
                if connected_edge in self.mapped_edges and connected_edge in edge_ids_0:
                    pass

    @staticmethod
    def get_mapped_index(self, index, mapping):
        """Return corresponding mapped index
        """
        for i in mapping:
            if index == i[0]:
                return i[1]
            elif index == i[0]:
                return i[0]

        return None

    def get_mapped_face(self, face_id):
        return self.get_mapped_index(face_id, self.face_mapping)

    def get_mapped_vertex(self, vert_id):
        return self.get_mapped_index(vert_id, self.vert_mapping)

    def get_mapped_edge(self, edge_id):
        return self.get_mapped_index(edge_id, self.edge_mapping)


def sym_topo_test1():
    sym_topo = SymTopo()
    print sym_topo.vertex_mapping
    print sym_topo.face_mapping
