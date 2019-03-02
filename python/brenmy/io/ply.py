'''
Created on 10 Nov 2018

@author: Bren
'''

from maya import cmds


class PlyData(object):
    def __init__(self):
        self._vertex_positions = []
        self._vertex_normals = []
        self._vertex_colors = []

    def vertex_positions(self):
        return self._vertex_positions

    def vertex_normals(self):
        return self._vertex_normals

    def vertex_colors(self):
        return self._vertex_colors

    def read(self, file_path):
        f = open(file_path, 'r')
        lines = f.readlines()

        header = True

        for line in lines:
            if line.endswith("\n"):
                line = line[:-2]

            if not header:
                l = line.split(' ')
                fL = [float(i) for i in l]
                self._vertex_positions.append(fL[0:3])
                self._vertex_normals.append(fL[3:6])
                self._vertex_colors.append(fL[6:9])

            if 'end_header' in line:
                header = False


def import_ply_as_n_particles(ply_file):
    ply_data = PlyData()
    ply_data.read(ply_file)

    particle = cmds.nParticle(position=ply_data.vertex_positions())

    for i, color in enumerate(ply_data.vertex_colors()):
        cmds.nParticle(
            particle, edit=True, attribute="rgbPP",
            id=i, vectorValue=color
        )
