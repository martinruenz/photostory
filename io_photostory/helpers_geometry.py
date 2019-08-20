#!/usr/bin/env python3
# ====================================================================
# Copyright 2018 by Martin Rünz <contact@martinruenz.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
# ====================================================================

import bpy
import math
from mathutils import Vector


def create_plane_meshdata(w, h, uv_border=0):
    verts = [
        (0.0, 0.0, 0.0),
        (w, 0.0, 0.0),
        (w, h, 0.0),
        (0.0, h, 0.0)
    ]
    faces = [(0, 1, 2, 3)]
    mesh_data = bpy.data.meshes.new("plane")
    mesh_data.from_pydata(verts, [], faces)

    if uv_border >= 0:
        border_width_u = uv_border
        border_width_v = border_width_u * w / h
        mesh_data.uv_layers.new()
        mesh_data.uv_layers.active.data[0].uv = (-border_width_u, -border_width_v)
        mesh_data.uv_layers.active.data[1].uv = (1 + border_width_u, -border_width_v)
        mesh_data.uv_layers.active.data[2].uv = (1 + border_width_u, 1 + border_width_v)
        mesh_data.uv_layers.active.data[3].uv = (-border_width_u, 1 + border_width_v)

    mesh_data.update()
    return mesh_data


def create_spiral_meshdata(center=(0, 0, 0), offset=1, points_per_round=20, rounds=3, extend=0, invert_direction=False):

    verts = []
    for i in range(points_per_round * rounds + 1):
        p = i / points_per_round
        t = 2 * math.pi * p
        r = offset * p #+ p
        verts.append(Vector((r * math.sin(t) + center[0], r * math.cos(t) + center[1], center[2])))

    if extend > 0:
        tangent = Vector((r * math.cos(t), -r * math.sin(t), 0.0))
        verts.append(Vector(verts[len(verts) - 1]) + extend * tangent.normalized())

    if invert_direction:
        for i, v in enumerate(verts):
            verts[i] = verts[i]-verts[len(verts)-1]
        verts.reverse()

    edges = []
    for i in range(len(verts) - 1):
        edges.append([i, i + 1])

    mesh_data = bpy.data.meshes.new("spiral")
    mesh_data.from_pydata(verts, edges, [])

    return mesh_data, verts[0], verts[len(verts)-1]
