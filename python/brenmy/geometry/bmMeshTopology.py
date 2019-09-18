"""

import sys

for path in [
    r"D:\Repos\brenmy\python",
    r"D:\Dev\maya\numpy\numpy-1.13.1+mkl-cp27-none-win_amd64"
]:
    if path not in sys.path:
        sys.path.append(path)

from brenmy.geometry import bmMeshTopology
reload(bmMeshTopology)
bmMeshTopology.mirror_sym_topo_sl(reverse=False)


TODO test properly that MeshDataCache actually improves performance enough to make it worthwhile.

"""

from maya import cmds
from maya.api import OpenMaya
import numpy
import sys

import time


class MeshDataCache(object):
    """MeshDataCache base class.

    Intended to store connected vertices etc.

    Provides faster random access lookup instead of
    using MFn-iterator.setIndex(i) etc.

    """
    ITERATOR = None

    def __init__(self, mesh=None):
        if self.ITERATOR is None:
            raise Exception("Cannot instance base class")

        self._mesh = None
        self._dag = None

        self.data = []
        self.vertices = []
        self.edges = []
        self.faces = []

        if mesh is not None:
            self.set_mesh(mesh)

    def set_mesh(self, mesh):
        sel = OpenMaya.MSelectionList()
        sel.add(mesh)
        self._dag = sel.getDagPath(0)
        self._iterator = self.ITERATOR(self._dag)

    def clear(self):
        self.data = []
        self.vertices = []
        self.edges = []
        self.faces = []

    def debug(self):
        print "DEBUG {}".format(self.__class__.__name__)

        for name, data in [
            ("vertices", self.vertices),
            ("edges", self.edges),
            ("faces", self.faces)
        ]:
            print "\t{}: {}".format(name, data[:100])

    def _append_vertices(self):
        pass

    def _append_edges(self):
        pass

    def _append_faces(self):
        pass

    def _next(self):
        self._iterator.next()

    def create_cache(self):
        if self._dag is None:
            raise Exception(
                "Cannot cache while mesh is None"
            )

        self.clear()

        self._iterator.setIndex(0)

        while not self._iterator.isDone():
            self._append_vertices()
            self._append_edges()
            self._append_faces()
            self._next()

        self._iterator.reset()


class VertexDataCache(MeshDataCache):
    """Stores vertex-connected edges and faces and surrounding vertices.
    """
    ITERATOR = OpenMaya.MItMeshVertex

    def __init__(self, mesh=None):
        super(VertexDataCache, self).__init__(mesh=mesh)

    def _append_edges(self):
        self.edges.append(
            list(self._iterator.getConnectedEdges())
        )

    def _append_faces(self):
        self.faces.append(
            list(self._iterator.getConnectedFaces())
        )

    def _append_vertices(self):
        self.vertices.append(
            list(self._iterator.getConnectedVertices())
        )


class EdgeDataCache(MeshDataCache):
    """Stores edge-connected vertices, faces and surrounding edges.
    """
    ITERATOR = OpenMaya.MItMeshEdge

    def __init__(self, mesh=None):
        super(EdgeDataCache, self).__init__(mesh=mesh)

    def _append_vertices(self):
        self.vertices.append(
            [self._iterator.vertexId(0), self._iterator.vertexId(1)]
        )

    def _append_faces(self):
        self.faces.append(
            list(self._iterator.getConnectedFaces())
        )

    def _append_edges(self):
        self.edges.append(
            list(self._iterator.getConnectedEdges())
        )


class FaceDataCache(MeshDataCache):
    """Stores face-connected vertices, edges and surrounding faces.
    """
    ITERATOR = OpenMaya.MItMeshPolygon

    def __init__(self, mesh=None):
        super(FaceDataCache, self).__init__(mesh=mesh)

    def _next(self):
        self._iterator.next(True)

    def _append_vertices(self):
        """Append vertices belonging to current face"""
        self.vertices.append(
            list(self._iterator.getVertices()))

    def _append_edges(self):
        """Append edges belonging to current face"""
        self.edges.append(
            list(self._iterator.getEdges())
        )

    def _append_faces(self):
        """Append faces surrounding current face"""
        self.faces.append(
            list(self._iterator.getConnectedFaces())
        )


class MeshCache(object):
    """Cache mesh data for faster lookup
    """

    def __init__(self, mesh):
        self._mesh = mesh
        self.vertices = VertexDataCache(mesh=mesh)
        self.edges = EdgeDataCache(mesh=mesh)
        self.faces = FaceDataCache(mesh=mesh)

    def debug(self):
        for i in self.vertices, self.edges, self.faces:
            i.debug()


class FaceMap(object):
    """Map vertices and edges by tracing the outline of a polygon face.

    User indicates direction of travel,
    by providing a starting vertex and starting edge to travel along.

    Starting vertex must be connected to starting edge.

    Number of sides does not matter, as trace will continue until
    all vertices and edges are mapped.
    """

    DEBUG_MODE = False

    def __init__(self, dag, face_id, edge_0_id, vert_0_id):

        print "POOPOPOPOPOPOOOOP"

        self.dag = dag
        self.face_id = face_id
        self.edge_0 = edge_0_id
        self.vert_0 = vert_0_id

        it_poly = OpenMaya.MItMeshPolygon(self.dag)

        # get face verts and edges
        it_poly.setIndex(self.face_id)

        self.vert_ids = it_poly.getVertices()
        self.edge_ids = it_poly.getEdges()

        # validate user input
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

        if edge_0_id not in self.edge_ids:
            raise Exception(
                "Edge 0 not found in face edges: {0}.f[{1}], ({0}.e[{2}])".format(
                    self.dag.partialPathName(),
                    face_id, edge_0_id
                )
            )

        # start tracing
        self.traced_verts = [vert_0_id]
        self.traced_edges = [edge_0_id]

        self._it_vert = OpenMaya.MItMeshVertex(self.dag)
        self._it_edge = OpenMaya.MItMeshEdge(self.dag)

        self._trace(edge_0_id, vert_0_id)

        if self.DEBUG_MODE:
            print "Face map: {}".format(face_id)
            print "\ttraced edges: ", self.traced_edges
            print "\ttraced verts: ", self.traced_verts

    def _trace(self, edge_id, vert_id):
        """Recursively walk edges.
        """
        self._it_edge.setIndex(edge_id)

        # identify vertex id at other end of edge
        if vert_id == self._it_edge.vertexId(0):
            next_vert = self._it_edge.vertexId(1)
        elif vert_id == self._it_edge.vertexId(1):
            next_vert = self._it_edge.vertexId(0)
        else:
            raise Exception(
                "Vertex not connected to edge: e[{}], vtx[{}]".format(
                    edge_id, vert_id)
            )

        # identify edge id continuing along face perimeter
        self._it_vert.setIndex(next_vert)

        connected_edges = [
            i for i in self._it_vert.getConnectedEdges() if i in self.edge_ids
        ]

        if len(connected_edges) != 2:
            print "connected edges: ", connected_edges
            print "edges: ", self.edge_ids
            raise Exception(
                "Failed to trace edge: e[{}], vtx[{}]".format(edge_id, vert_id)
            )

        if edge_id == connected_edges[0]:
            next_edge = connected_edges[1]
        elif edge_id == connected_edges[1]:
            next_edge = connected_edges[0]
        else:
            # in theory this should be impossible
            raise Exception(
                "Edge not connected to vertex: e[{}], vtx[{}]".format(
                    edge_id, next_vert)
            )

        # continue tracing provided  we haven't completed the loop
        if next_edge in self.traced_edges or next_vert in self.traced_verts:
            return

        self.traced_verts.append(next_vert)
        self.traced_edges.append(next_edge)

        self._trace(next_edge, next_vert)


class CachedFaceMap(object):
    """Map vertices and edges by tracing the outline of a polygon face.

    User indicates direction of travel,
    by providing a starting vertex and starting edge to travel along.

    Starting vertex must be connected to starting edge.

    Number of sides does not matter, as trace will continue until
    all vertices and edges are mapped.

    Utilises Mesh Cache for speed

    """

    def __init__(self, cache, face_id, edge_0_id, vert_0_id):
        self.cache = cache
        self.face_id = face_id
        self.edge_0 = edge_0_id
        self.vert_0 = vert_0_id

        self.vert_ids = cache.faces.vertices[self.face_id]
        self.edge_ids = cache.faces.edges[self.face_id]

        # skip validating user input for speed

        # start tracing
        self.traced_verts = [vert_0_id]
        self.traced_edges = [edge_0_id]

        self._trace(edge_0_id, vert_0_id)

    def _trace(self, edge_id, vert_id):
        """Recursively walk edges.
        """
        verts = self.cache.edges.vertices[edge_id]

        # identify vertex id at other end of edge
        next_vert = verts[1] if vert_id == verts[0] else verts[0]

        # check if trace is complete
        if next_vert in self.traced_verts:
            return

        # identify edge id continuing along face perimeter
        connected_edges = [
            i for i in self.cache.vertices.edges[next_vert] if i in self.edge_ids
        ]

        next_edge = connected_edges[1] if edge_id == connected_edges[0] else connected_edges[0]

        self.traced_verts.append(next_vert)
        self.traced_edges.append(next_edge)

        self._trace(next_edge, next_vert)


class SymTopo(object):
    """

    """
    DEBUG_MODE = False
    DEBUG_DELAY = 0.001

    USE_CACHE = True

    def __init__(self, mesh, middle_edges):

        self.mesh = mesh
        self.middle_edges = middle_edges
        self.middle_verts = []

        # initialize iterators
        print "creating mesh cache..."
        start_time = time.time()
        self.cache = MeshCache(mesh=mesh)
        self.cache.vertices.create_cache()
        self.cache.edges.create_cache()
        self.cache.faces.create_cache()
        self.cache.debug()
        end_time = time.time()
        print "done creating mesh cache...({} seconds)".format(end_time - start_time)

        # begin mapping
        self.faces_a = []
        self.faces_b = []

        self.verts_a = []
        self.verts_b = []

        self.edges_a = []
        self.edges_b = []

        # map middle verts/edges to themselves
        for edge_id in self.middle_edges:
            if self.USE_CACHE:
                vert_0, vert_1 = self.cache.edges.vertices[edge_id]
            else:
                self.it_edge.setIndex(edge_id)
                vert_0 = self.it_edge.vertexId(0)
                vert_1 = self.it_edge.vertexId(1)

            self.add_edge_mapping(edge_id, edge_id)

            for vert in vert_0, vert_1:
                if vert in self.verts_a:
                    #                 if vert in self.mapped_verts:

                    continue

                self.middle_verts.append(vert)
                self.add_vertex_mapping(vert, vert)

        # start with first edge
#         print "first edge: {}".format(self.middle_edges[0])

        self.map_center_edge(self.middle_edges[0])

        # map first face
#         print "first faces: {} {}".format(*self.face_mapping[0])

        # increase recursion limit
        old_recursion_limit = sys.getrecursionlimit()

        if self.USE_CACHE:
            new_recursion_limit = len(self.cache.faces.vertices)
        else:
            new_recursion_limit = self.it_vert.count()

        sys.setrecursionlimit(new_recursion_limit)

        start_time = time.time()

        try:
            self.map_faces_cache(self.faces_a[0], self.faces_b[0])
#             self.map_faces(*self.face_mapping[0])
#             self.map_quad_faces(*self.face_mapping[0])
            sys.setrecursionlimit(old_recursion_limit)
        except:
            print "poop"
            sys.setrecursionlimit(old_recursion_limit)
            raise

        end_time = time.time()

        print "SymTopo initialized in {} seconds".format(end_time - start_time)

    def map_center_edge(self, edge_id):
        # get connected faces
        # this should be 2 faces on either side of edge
        # so this is an easy map

        if self.USE_CACHE:
            face_ids = self.cache.edges.faces[edge_id]
        else:
            it_edge = OpenMaya.MItMeshEdge(self.dag)
            it_edge.setIndex(edge_id)

            face_ids = it_edge.getConnectedFaces()

        # only thing is we have nothing to indicate
        # which "direction" this mapping is going from and to
        # we can just pick one and go from there
        self.add_face_mapping(face_ids[0], face_ids[1])

    def map_faces(self, face_a, face_b):
        it_poly = OpenMaya.MItMeshPolygon(self.dag)

        # get face a edges
        it_poly.setIndex(face_a)
        edge_ids_a = it_poly.getEdges()

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
                    map_a = FaceMap(
                        self.dag, face_a, edge_id, vert_0
                    )
                except:
                    print "Failed to map face_a"
                    raise

                try:
                    map_b = FaceMap(
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

                for vert_a, vert_b in zip(map_a.traced_verts, map_b.traced_verts):
                    if vert_a not in self.verts_a and vert_b not in self.verts_b:
                        self.add_vertex_mapping(vert_a, vert_b)

                for edge_a, edge_b in zip(map_a.traced_edges, map_b.traced_edges):

                    if edge_a in self.edges_a or edge_b in self.edges_b:
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

                    if self.DEBUG_MODE:
                        cmds.select(
                            "{}.f[{}]".format(
                                self.dag.partialPathName(), face_a_next),
                            "{}.f[{}]".format(
                                self.dag.partialPathName(), face_b_next),
                            add=True
                        )

                        cmds.refresh()
                        time.sleep(self.DEBUG_DELAY)

                    if self.USE_CACHE:
                        self.map_faces_cache(face_a_next, face_b_next)
                    else:
                        self.map_faces(face_a_next, face_b_next)

                return

    def map_faces_cache(self, face_a, face_b):

        edge_ids_a = self.cache.faces.edges[face_a]

        # look for mapped edges and go from there
        for edge_id in edge_ids_a:

            if edge_id in self.edges_a:
                # get mapped edge
                mapped_edge = self.edges_b[self.edges_a.index(edge_id)]

                vert_0 = self.cache.edges.vertices[edge_id][0]

                mapped_vert_0 = self.verts_b[self.verts_a.index(vert_0)]

                map_a = CachedFaceMap(
                    self.cache, face_a, edge_id, vert_0
                )

                map_b = CachedFaceMap(
                    self.cache, face_b, mapped_edge, mapped_vert_0
                )

                for vert_a, vert_b in zip(map_a.traced_verts, map_b.traced_verts):
                    if vert_a in self.verts_a:
                        continue

                    self.add_vertex_mapping(vert_a, vert_b)

                for edge_a, edge_b in zip(map_a.traced_edges, map_b.traced_edges):
                    if edge_a in self.edges_a:
                        continue

                    self.add_edge_mapping(edge_a, edge_b)

                    # continue mapping faces connected to mapped edges
                    faces_a = self.cache.edges.faces[edge_a]

                    if len(faces_a) == 1:
                        # we must be on mesh boundary
                        continue

                    faces_b = self.cache.edges.faces[edge_b]

                    face_a_next = faces_a[0] if faces_a[0] != face_a else faces_a[1]
                    face_b_next = faces_b[0] if faces_b[0] != face_b else faces_b[1]

                    # seeing as we have already checked if this edge is mapped
                    # that gives us a reliable indicator if the next face
                    # is already mapped
                    # so there is no need to check again

                    self.add_face_mapping(face_a_next, face_b_next)

                    # continue mapping
                    self.map_faces_cache(face_a_next, face_b_next)

                return

    def add_edge_mapping(self, edge_a, edge_b):
        self.edges_a.append(edge_a)
        self.edges_b.append(edge_b)
        return True

    def add_vertex_mapping(self, vert_a, vert_b):
        self.verts_a.append(vert_a)
        self.verts_b.append(vert_b)
        return True

    def add_face_mapping(self, face_a, face_b):
        self.faces_a.append(face_a)
        self.faces_b.append(face_b)
        return True


def mirror_sym_topo_sl(reverse=False):
    """Use SymTopo class and numpy to mirror mesh based on scene selection.

    User must first select full middle edge loop.

    """
    # get selected edges
    # assuming middle edges are currently selected
    sel = OpenMaya.MGlobal.getActiveSelectionList()

    dag, comp_obj = sel.getComponent(0)

    middle_edge_component = OpenMaya.MFnSingleIndexedComponent(
        comp_obj
    )

    if middle_edge_component.componentType != OpenMaya.MFn.kMeshEdgeComponent:
        raise Exception("Please select full middle edge loop")

    middle_edges = middle_edge_component.getElements()

    old_points, mirrored_points = mirror_sym_topo(
        dag.partialPathName(), middle_edges, reverse=reverse
    )

    return old_points, mirrored_points


def mirror_sym_topo(mesh, middle_edges, reverse=False):
    """Use SymTopo class and numpy to mirror mesh.
    """
    # get objects
    sel = OpenMaya.MSelectionList()
    sel.add(mesh)
    dag = sel.getDagPath(0)

    # get points
    m_mesh = OpenMaya.MFnMesh(dag)
    points = m_mesh.getPoints()
    points = numpy.array(points)

    # get rid of redundant 4th column
    points = numpy.delete(points, 3, axis=1)

    # map topo
    sym_topo = SymTopo(mesh, middle_edges)

    # get points_a and mirror column 0 (x-axis)
    a_ids = [i for i in sym_topo.verts_a if i not in sym_topo.middle_verts]
    b_ids = [i for i in sym_topo.verts_b if i not in sym_topo.middle_verts]
    points_a = points[a_ids]
    points_b = points[b_ids]

    # determine direction of mapping
    # by comparing average x values
    mean_a = numpy.mean(points_a, axis=0)
    mean_b = numpy.mean(points_b, axis=0)

    # if mapping is reversed
    # then reverse back before continuing
    if mean_a[0] < mean_b[0]:
        temp_points_a = numpy.array(points_a)
        temp_ids_a = list(a_ids)

        points_a = numpy.array(points_b)
        points_b = temp_points_a

        a_ids = list(b_ids)
        b_ids = temp_ids_a

    if not reverse:
        src_points = points_a
        dst_ids = b_ids
    else:
        src_points = points_b
        dst_ids = a_ids

    mirrored_points = numpy.array(points)

    src_points[:, 0] *= -1.0
    mirrored_points[dst_ids] = src_points

    # set mid points x value to 0.0
    mid_points = points[sym_topo.middle_verts]
    mid_points[:, 0] = 0.0
    mirrored_points[sym_topo.middle_verts] = mid_points

    # set points
    m_mesh.setPoints(
        OpenMaya.MPointArray(mirrored_points.tolist())
    )

    return points, mirrored_points
