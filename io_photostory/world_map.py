#!/usr/bin/env python3
# ====================================================================
# Copyright 2017 by Martin Rünz <contact@martinruenz.de>
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
import bmesh
import math
from mathutils import Vector, Matrix
from bpy_extras.image_utils import load_image

if "bpy" in locals():
    import importlib
    if "helpers_geometry" in locals():
        importlib.reload(helpers_geometry)
    if "helpers_views" in locals():
        importlib.reload(helpers_views)

from .helpers_geometry import *
from .helpers_views import *

def get_latlong(input):
    if type(input) is list:
        if len(input) == 2:
            return float(input[0]), float(input[1])
    if type(input) is str:
        ll = input.split()
        if len(ll) == 2:
            return float(ll[0].rstrip(',')), float(ll[1])
    raise RuntimeError("Invalid latitude, longitude format")


def latlong_to_xy(lat, long, height, width):
    y = height * (lat+90)/180
    x = width * (long+180)/360
    return x, y


def get_path_length(path):
    mesh = path.to_mesh(bpy.context.scene, True, "RENDER")
    return sum((mesh.vertices[e.vertices[0]].co - mesh.vertices[e.vertices[1]].co).length for e in mesh.edges)


class WorldMap:

    animation_dash_material = None

    def __init__(self, width, height, equirectangular_texture, displacement_texture=None):
        self.width = width
        self.height = height
        self.unroll_spline = None
        self.routes = []

        # Static members
        if WorldMap.animation_dash_material is None:
            WorldMap.animation_dash_material = bpy.data.materials.new(name="animation_dash_material")
            WorldMap.animation_dash_material.specular_intensity = 0.2
            WorldMap.animation_dash_material.diffuse_color = (0.85, 0.01, 0)

        # Create mesh and object
        mesh_data = create_plane_meshdata(width, height)
        self.object = bpy.data.objects.new("world_map", mesh_data)
        self.object.location = Vector((0, 0, 1))

        # Load texture
        texture = bpy.data.textures.new(name="photo_texture", type='IMAGE')
        texture.image = load_image(equirectangular_texture, None, recursive=False)

        # Create material
        material = bpy.data.materials.new(name="photo_material")
        material.specular_intensity = 0
        mtex = material.texture_slots.add()
        mtex.texture = texture
        mtex.texture.extension = 'CLIP'
        mtex.texture_coords = 'UV'
        mtex.use_map_color_diffuse = True
        self.object.data.materials.append(material)

        # Add nodes setup as well:

        # Cycles
        material.use_nodes = True
        mat_nodes = material.node_tree.nodes
        mat_links = material.node_tree.links
        mat_nodes.clear()
        node_t = mat_nodes.new('ShaderNodeTexImage')
        node_t.image = texture.image
        node_t.extension = 'CLIP'
        node_t.location = (0, 0)
        node_bsdf_photo = mat_nodes.new('ShaderNodeBsdfDiffuse')
        node_bsdf_photo.location = (300, 0)
        node_bsdf_white = mat_nodes.new('ShaderNodeBsdfDiffuse')
        node_bsdf_white.location = (300, -300)
        node_mix = mat_nodes.new('ShaderNodeMixShader')
        node_mix.location = (600, -150)
        node_om = mat_nodes.new('ShaderNodeOutputMaterial')
        node_om.location = (900, 0)
        mat_links.new(node_t.outputs['Color'], node_bsdf_photo.inputs['Color'])
        mat_links.new(node_bsdf_white.outputs['BSDF'], node_mix.inputs[1])
        mat_links.new(node_bsdf_photo.outputs['BSDF'], node_mix.inputs[2])
        mat_links.new(node_t.outputs['Alpha'], node_mix.inputs['Fac'])
        mat_links.new(node_mix.outputs['Shader'], node_om.inputs['Surface'])

        # Internal
        node_m = mat_nodes.new('ShaderNodeMaterial')
        node_m.location = (0, 500)
        node_m.material = material
        node_o = mat_nodes.new('ShaderNodeOutput')
        node_o.location = (300, 500)
        mat_links.new(node_m.outputs['Color'], node_o.inputs['Color'])

        if displacement_texture is not None:
            # Add subdivide
            # bpy.ops.mesh.subdivide()
            self.object.modifiers.new(name="worldmap_subdivide", type='SUBSURF')
            subdivide = self.object.modifiers["worldmap_subdivide"]
            subdivide.subdivision_type = 'SIMPLE'
            subdivide.levels = 8
            subdivide.render_levels = 9

            # Add displacement
            self.object.modifiers.new(name="worldmap_displace", type='DISPLACE')
            displace = self.object.modifiers["worldmap_displace"]
            displace.strength = 18
            displace.mid_level = 0
            displace.texture_coords = 'UV'
            displ_texture = bpy.data.textures.new(name="worldmap_displace_texture", type='IMAGE')
            displ_texture.image = load_image(displacement_texture, None, recursive=False)
            displace.texture = displ_texture

            # Add smoothing
            self.object.modifiers.new(name="worldmap_smooth", type='SMOOTH')
            smooth = self.object.modifiers["worldmap_smooth"]
            smooth.factor = 1.5

        bpy.context.scene.objects.link(self.object)

    def get_local_coord(self, lat, long):
        x, y = latlong_to_xy(lat, long, self.height, self.width)
        return Vector((x, y, 1))  # TODO correct z


    def add_unroll_animation(self, current_frame, duration=4):
        """
        :param current_frame: Current frame
        :param duration: Duration of animation in seconds
        :return: New current frame after animation
        """
        execution_context = get_override('VIEW_3D')

        # Generate unroll spline
        rounds = 5
        offset = 0.05 * self.height
        unroll_meshdata, vs, ve = create_spiral_meshdata(offset=offset, rounds=rounds, extend=0.1 * self.height, invert_direction=False)
        self.unroll_spline = bpy.data.objects.new("unroll_spline", unroll_meshdata)
        bpy.context.scene.objects.link(self.unroll_spline)
        self.unroll_spline.select = True
        bpy.context.scene.objects.active = self.unroll_spline
        bpy.ops.object.convert(execution_context, target='CURVE')
        bpy.ops.transform.rotate(execution_context, value=1.5*math.pi, axis=(1, 0, 0), constraint_axis=(True, False, False),
                                 constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED',
                                 proportional_edit_falloff='SMOOTH', proportional_size=1)

        self.unroll_spline.data.transform(Matrix.Translation(-ve))
        unroll_spline_length = get_path_length(self.unroll_spline)
        self.unroll_spline.location = self.object.location + Vector((self.width, 0.5 * self.height, 1))

        s = self.width / unroll_spline_length
        bpy.ops.transform.resize(execution_context, value=(s, s, s), constraint_axis=(False, False, False),
                                 constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED',
                                 proportional_edit_falloff='SMOOTH', proportional_size=1)

        # Add modifier to map
        self.object.modifiers.new(name="unroll_curve", type='CURVE')
        unroll_mod = self.object.modifiers["unroll_curve"]
        unroll_mod.object = self.unroll_spline

        # Create animation
        unroll_mod.show_render = True
        unroll_mod.show_viewport = True
        unroll_mod.keyframe_insert("show_render", index=-1, frame=current_frame)
        unroll_mod.keyframe_insert("show_viewport", index=-1, frame=current_frame)

        map_location_backup = self.object.location.copy()
        self.set_location(Vector((self.unroll_spline.location[0], self.object.location[1], self.object.location[2])),
                          current_frame)

        self.unroll_spline.keyframe_insert("location", index=-1, frame=current_frame)
        current_frame += int(bpy.context.scene.render.fps * duration)
        self.unroll_spline.location = self.unroll_spline.location - Vector((self.width, 0, 0))
        self.unroll_spline.keyframe_insert("location", index=-1, frame=current_frame)

        # Cleanup
        unroll_mod.show_render = False
        unroll_mod.show_viewport = False
        unroll_mod.keyframe_insert("show_render", index=-1, frame=current_frame)
        unroll_mod.keyframe_insert("show_viewport", index=-1, frame=current_frame)
        self.set_location(map_location_backup, current_frame)

        return current_frame

    def has_unroll_animation(self):
        return self.unroll_spline is not None

    def set_location(self, location, frame, ignore_z=True):
        if ignore_z:
            self.object.location = Vector((location[0], location[1], 1))
        else:
            self.object.location = location.copy()
        self.object.keyframe_insert("location", index=-1, frame=frame)

        # Set interpolation-mode to constant => Jump between positions
        for c in self.object.animation_data.action.fcurves:
            if c.data_path == 'location':
                last_kf = None
                for kf in c.keyframe_points:
                    if int(kf.co[0]) == int(frame) and last_kf is not None:
                        last_kf.interpolation = 'CONSTANT'
                    last_kf = kf

    def add_marker(self, lat, long):
        mesh_data = bpy.data.meshes.new('worldmap_marker_sphere')
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, diameter=0.001 * self.width)
        bm.to_mesh(mesh_data)
        bm.free()
        sphere_marker = bpy.data.objects.new("worldmap_marker", mesh_data)
        sphere_marker.location = self.get_local_coord(lat, long)
        sphere_marker.parent = self.object
        sphere_marker.data.materials.append(WorldMap.animation_dash_material)
        bpy.context.scene.objects.link(sphere_marker)

    def animate_route(self, locations, camera, current_frame, duration=-1):
        """

        :param locations: list of lat,long tuples
        :param camera: camera object
        :param current_frame: current_frame before
        :param duration:
        :return: new current_frame
        """

        # Get local coordinates
        locations = [get_latlong(l) for l in locations]
        locations = [self.get_local_coord(l[0], l[1]) for l in locations]

        # Create spline
        curve_data = bpy.data.curves.new('route_data', 'CURVE')
        curve_data.dimensions = '3D'
        curve_data.resolution_u = 13
        curve_data.render_resolution_u = 13
        spline = curve_data.splines.new(type='BEZIER')
        spline.bezier_points.add(len(locations)-1)
        for i, loc in enumerate(locations):
            spline.bezier_points[i].co = loc

            # Set (tangent) handles for bezier points
            if i > 0:
                v = 0.3 * (locations[i-1]-loc)
                h = v.length
                spline.bezier_points[i].handle_left = loc + v + Vector((0, 0, h))
            if i < len(locations)-1:
                v = 0.3 * (locations[i+1]-loc)
                h = v.length
                spline.bezier_points[i].handle_right = loc + v + Vector((0, 0, h))

        curve = bpy.data.objects.new('route', curve_data)
        curve.parent = self.object
        spline_length = get_path_length(curve)
        bpy.context.scene.objects.link(curve)

        # Create animation

        if duration == -1:
            duration = len(locations) * 1.1

        # Generate array of dashes
        dash_diameter = 0.0006 * self.width
        dash_offset = 0.3 * dash_diameter
        num_dashes = spline_length / (dash_diameter+dash_offset)
        mesh_data = create_plane_meshdata(dash_diameter, dash_diameter)
        dash_object = bpy.data.objects.new("route_dash", mesh_data)
        dash_object.modifiers.new(name="dash_array", type='ARRAY')
        array_mod = dash_object.modifiers["dash_array"]
        array_mod.use_constant_offset = True
        array_mod.constant_offset_displace[0] = dash_offset
        dash_object.modifiers.new(name="dash_curve", type='CURVE')
        curve_mod = dash_object.modifiers["dash_curve"]
        curve_mod.object = curve
        dash_object.data.materials.append(WorldMap.animation_dash_material)
        dash_object.parent = self.object
        self.routes.append(dash_object)
        bpy.context.scene.objects.link(dash_object)

        # Animate creation of dashes
        bpy.context.scene.update()  # Make sure matrix_world is up-to-date
        array_mod.count = 0
        array_mod.keyframe_insert("count", index=-1, frame=current_frame)
        camera.location = self.object.matrix_world * (locations[0] + Vector((0, 0, spline_length)))
        camera.keyframe_insert("location", index=-1, frame=current_frame)
        current_frame += int(bpy.context.scene.render.fps * duration)

        array_mod.count = num_dashes
        array_mod.keyframe_insert("count", index=-1, frame=current_frame)
        camera.location = self.object.matrix_world * (locations[len(locations)-1] + Vector((0, 0, spline_length)))
        camera.keyframe_insert("location", index=-1, frame=current_frame)

        if True:
            current_frame += int(bpy.context.scene.render.fps * 3)
            camera.location = self.object.matrix_world * (locations[len(locations) - 1] + Vector((0, 0, 4 * spline_length)))
            camera.keyframe_insert("location", index=-1, frame=current_frame)


        return current_frame