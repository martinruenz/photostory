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

bl_info = {
    "name": "Photostory JSON format",
    "author": "Martin Rünz",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "File > Import-Export",
    "description": "Import a photostory and generate an according scene",
    "warning": "",
    "category": "Import-Export"
}

import os
from mathutils import Vector
from itertools import chain
import json
import bpy
import random
import bmesh

from bpy_extras.image_utils import load_image
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, FloatProperty

if "bpy" in locals():
    import importlib

    if "layout" in locals():
        importlib.reload(layout)
    if "helpers_views" in locals():
        importlib.reload(helpers_views)
    if "helpers_geometry" in locals():
        importlib.reload(helpers_geometry)
    if "world_map" in locals():
        importlib.reload(world_map)

from . import layout
from . import world_map
from .helpers_views import *
from .helpers_geometry import *

#
# def is_video(path):
#     if path.endswith(('.avi', '.avi'))

class Photo(layout.Rectangle):
    def __init__(self, image=None):
        """
        :param image: bpy.types.Image see: https://docs.blender.org/api/current/bpy.types.Image.html
        """
        layout.Rectangle.__init__(self)
        self.object = None
        self.texture = None
        self.texture_node = None
        self.type = "UNKNOWN"
        self.set_image(image)

    def set_image(self, image):
        """
        :param image: bpy.types.Image see: https://docs.blender.org/api/current/bpy.types.Image.html
        """
        self.image = image
        print("setting image ", image.filepath)
        if image is not None:
            self.width = image.size[0]
            self.height = image.size[1]

    def add_deformation(self, max_edge_transition=20):
        if not self.object:
            print("Warning, no photo available yet.")
            return

        override = enter_editmode(self.object)

        # Subdivide
        # Alternative: bmesh.ops.subdivide_edges
        bpy.ops.mesh.select_all(override, action='SELECT')
        bpy.ops.mesh.subdivide(override, number_cuts=20)
        bpy.ops.mesh.select_all(override, action='DESELECT')

        # Modify corners
        mesh = bmesh.from_edit_mesh(self.object.data)
        mesh.verts.ensure_lookup_table()
        for i in range(4):
            mesh.verts[i].select = True
            bpy.ops.transform.translate(override, value=(0, 0, random.random()*max_edge_transition),
                                        constraint_axis=(False, False, True), orient_type='GLOBAL',
                                        mirror=False, use_proportional_edit=True, proportional_edit_falloff='SHARP',
                                        proportional_size=200)
            mesh.verts[i].select = False

        # Finish editing
        leave_editmode()
        self.object.select_set(False)


class Slide(layout.Size):
    def __init__(self, size, json, duration):
        layout.Size.__init__(self, size.width, size.height)
        self.photos = []
        self.photos_background = []
        self.texts = []
        #self.duration = 4.5 if kwargs.get("duration") is None else kwargs.get("duration")
        self.duration = duration
        self.longest_video_frames = 0
        self.json = json
        self.root = bpy.data.objects.new("slide", None)
        bpy.context.view_layer.active_layer_collection.collection.objects.link(self.root)

    def get_type(self):
        return self.json["type"]

    def has_video(self):
        return self.longest_video_frames > 0

    def start_videos_at(self, frame):
        for p in chain(self.photos, self.photos_background):
            if p.type == "MOVIE":
                p.texture.image_user.frame_start = frame
                p.texture_node.image_user.frame_start = frame

    def generate_layout(self, canvas_rect):
        # for p in self.photos:
        #     print("{} {}: ".format(p.width, p.height, p.image.filepath))

        # bg_scale = 0.66 * layout.generate_layout(self.photos, canvas_rect)
        #
        # if len(self.photos_background) > 0:
        #     layout.scale_layout(self.photos, 0.8)
        # layout.center_layout(self.photos, canvas_rect)
        #
        # # Evenly distribute background pictures
        # if len(self.photos_background) > 0:
        #     angle = 2 * math.pi / len(self.photos_background)
        layout.generate_layout_1(self.photos, self.photos_background, canvas_rect)


        # Randomly place background objects
        # bg_rects = layout.get_background_rectangles(self.photos, canvas_rect)
        # for bg_photo in self.photos_background:
        #     p = layout.sample_in_rectangles(bg_rects)
        #     bg_photo.width *= bg_scale
        #     bg_photo.height *= bg_scale
        #     bg_photo.x = p[0] - bg_photo.width / 2
        #     bg_photo.y = p[1] - bg_photo.height / 2

    def add_randomization(self, rotation_sigma=0.02):
        original_pivot = bpy.context.tool_settings.transform_pivot_point
        bpy.context.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
        execution_context = get_override('VIEW_3D')

        for p in self.photos:
            if p.object is None:
                continue
            enter_editmode(p.object, execution_context)
            bpy.ops.mesh.select_all(execution_context, action='SELECT')
            bpy.ops.transform.rotate(execution_context,
                                     value=random.normalvariate(0, rotation_sigma), orient_axis='Z', constraint_axis=(False, False, True),
                                     orient_type='GLOBAL', mirror=False, use_proportional_edit=False,
                                     proportional_edit_falloff='SMOOTH', proportional_size=1)
            bpy.ops.mesh.select_all(execution_context, action='DESELECT')
            leave_editmode()

        for p in self.photos_background:
            if p.object is None:
                continue
            enter_editmode(p.object, execution_context)
            bpy.ops.mesh.select_all(execution_context, action='SELECT')
            bpy.ops.transform.rotate(execution_context, value=random.normalvariate(0, 6 * rotation_sigma),
                                     orient_axis='Z', constraint_axis=(False, False, True),
                                     orient_type='GLOBAL', mirror=False, use_proportional_edit=False,
                                     proportional_edit_falloff='SMOOTH', proportional_size=1)
            bpy.ops.mesh.select_all(execution_context, action='DESELECT')
            leave_editmode()

        bpy.context.tool_settings.transform_pivot_point = original_pivot


class PhotostoryImporter(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.photostory"
    bl_label = "Import Photostory"
    filter_glob = StringProperty(default="*.json", options={'HIDDEN'})
    setup_scene = BoolProperty(name="Setup scene",
                               description="Setup scenes properties (start/end frame, clipping)",
                               default=True)
    unroll_map = BoolProperty(name="Unroll map",
                                   description="Add an unroll animation when the map is shown for the first GPS slide",
                                   default=True)
    skip_duplicates = BoolProperty(name="Skip duplicates",
                               description="Skip frames that are identical to previous (creating placeholders)",
                               default=True)
    default_slide_duration = FloatProperty(name="Default slide duration",
                                           description="Default slide duration (might be overwritten by json)",
                                           default=4.5)

    def execute(self, context):

        self.images = {}
        self.slides = []
        self.duplicate_frames = []
        self.world_map = None
        self.camera = None
        self.scene = bpy.context.scene
        self.canvas = layout.Rectangle(0, 0, self.scene.render.resolution_x, self.scene.render.resolution_y)
        self.max_wh = max(self.canvas.height, self.canvas.width)
        self.camera_origin = Vector((self.canvas.width / 2, self.canvas.height / 2, self.max_wh / 2))
        self.assets_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "assets")

        # self.renderer = 'INTERNAL'

        # "Hidden" settings
        self.use_orthographic_camera = False
        self.transition_time = 0.8
        self.photo_rotation_sigma = 0.02
        self.photo_max_edge_transition = 20
        self.offset_slides = 0.08 * self.canvas.width
        self.frames_transition = int(self.transition_time * self.scene.render.fps)
        self.zoom_map_duration = 3

        # Create camera
        cam_data = bpy.data.cameras.new("camera_data")
        if self.use_orthographic_camera:
            cam_data.type = 'ORTHO'
            cam_data.ortho_scale = self.max_wh
        else:
            cam_data.type = 'PERSP'
            cam_data.ortho_scale = self.max_wh
            cam_data.lens_unit = 'FOV'
            cam_data.angle = 1.57254
        cam_data.clip_end = 100000
        self.camera = bpy.data.objects.new("Camera", cam_data)
        self.camera.location = self.camera_origin
        bpy.context.view_layer.active_layer_collection.collection.objects.link(self.camera)

        # Setup scene
        if self.properties.setup_scene:
            # Adjust far clipping of 3D views
            a = get_area_3d().spaces.active
            a.clip_end = max(100000, a.clip_end)

            # Create world, if not existing
            if bpy.context.scene.world is None:
                print("Creating new world data-block...")
                bpy.context.scene.world = bpy.data.worlds.new("World")

            # Enable ambient occlusion
            bpy.context.scene.world.light_settings.use_ambient_occlusion = True
            bpy.context.scene.world.light_settings.ao_factor = 1
            bpy.context.scene.camera = self.camera

        # Create lamp
        if bpy.ops.object.light_add.poll():
            bpy.ops.object.light_add(type='SUN', location=(0, 0, 5000))
        # bpy.ops.object.lamp_add(type='SUN', view_align=False, location=(0, 0, 5000), layers=(
        #     True, False, False, False, False, False, False, False, False, False, False, False, False, False, False,
        #     False,
        #     False, False, False, False))
        # bpy.context.object.data.use_specular = False # Handled by material already

        print("Generating photostory...")
        print("- Canvas size: {}x{}".format(self.canvas.width, self.canvas.height))

        print("- Loading json...")
        with open(self.properties.filepath) as data_file:
            slides_desc = json.load(data_file)
            d = slides_desc.get("default_slide_duration")
            if d is not None:
                self.properties.default_slide_duration = float(d)

        # Parse all slides and store image paths
        images_paths = set()
        num_image_paths = 0
        for slide_desc in slides_desc["slides"]:
            if slide_desc["type"] == "photo_slide":
                slide_desc["background_paths"] = [p if os.path.isabs(p) else os.path.join(os.path.dirname(self.properties.filepath), p) for p in slide_desc["background_paths"]]
                slide_desc["foreground_paths"] = [p if os.path.isabs(p) else os.path.join(os.path.dirname(self.properties.filepath), p) for p in slide_desc["foreground_paths"]]
                for image_path in chain(slide_desc["background_paths"], slide_desc["foreground_paths"]):
                    num_image_paths += 1
                    images_paths.add(image_path)

        # Load all images/videos (no duplicates)
        print("- Loading images/videos ({} unique of {} paths) ...".format(len(images_paths), num_image_paths))
        for p in images_paths:
            path = os.path.abspath(p)
            if path in self.images and self.images[path] is not None:
                continue
            img = load_image(path, None, recursive=False)
            if img is not None:
                self.images[path] = img
                print("-- Loaded:", path)
            else:
                warn = "Loadind image {} failed".format(path)
                print("WARNING", warn)
                self.report({'WARNING'}, warn)

        # Create title slide
        #FIXME Introduce 'text_slide'
        #self.slides.append(self.create_title_slide(self.canvas, "Vietnam\n2018"))

        # Create (photo) slides
        current_frame = 1
        for i, slide_desc in enumerate(slides_desc["slides"]):
            if slide_desc["type"] == "photo_slide":
                slide = self.create_photo_slide(self.canvas,
                                                slide_desc,
                                                self.photo_rotation_sigma,
                                                self.photo_max_edge_transition)
            elif slide_desc["type"] == "gps_slide":
                if self.world_map is None:
                    self.create_map()
                slide = Slide(self.canvas, slide_desc, duration=self.properties.default_slide_duration)

            slide.root.location = Vector((i * (self.canvas.width+self.offset_slides), 0, 0))
            self.slides.append(slide)


        # Create background
        self.create_background(len(self.slides))
        # self.create_background(i+1)


        # Create animation
        bpy.context.view_layer.update()
        for i, slide in enumerate(self.slides):

            # Set start location of frame
            # TODO add optional variation
            # previous_camera_location = self.camera.location
            start_location = slide.root.matrix_world @ self.camera_origin
            self.camera.location = start_location
            self.camera.keyframe_insert("location", index=-1, frame=current_frame)
            slide.start_videos_at(current_frame)

            if slide.get_type() == "gps_slide":

                # Move map to current slide
                self.world_map.set_location(slide.root.location, current_frame-self.frames_transition)

                # Add unroll animation, when showing map for the first time
                if self.properties.unroll_map and not self.world_map.has_unroll_animation():
                    current_frame = self.world_map.add_unroll_animation(current_frame)

                zoom_in_offset = bpy.context.scene.render.fps * self.zoom_map_duration
                current_frame += int(zoom_in_offset)
                self.camera.keyframe_insert("location", index=-1, frame=current_frame)

                current_frame = self.world_map.animate_route(slide.json["gps_coordinates"], self.camera, current_frame)

                #current_frame += 0.7 * zoom_in_offset

                # Set end location of frame
                # TODO add optional variation
                # current_frame += max(slide.longest_video_frames, slide.duration * self.scene.render.fps)
                # self.camera.keyframe_insert("location", index=-1, frame=current_frame)

            else:
                # Set end location of frame

                num_frames = max(slide.longest_video_frames, slide.duration * self.scene.render.fps)
                current_frame += int(num_frames)

                # Compute end location of slide
                end_location = start_location  # Todo: Allow variations here

                print(type(current_frame), type(num_frames), type(self.duplicate_frames))

                # Identify duplicate / identical frames
                if end_location == start_location and not slide.has_video():
                    self.duplicate_frames += list(range(int(current_frame - num_frames + 1), int(current_frame)))

                # Insert keyframe for end location
                self.camera.location = end_location
                self.camera.keyframe_insert("location", index=-1, frame=current_frame)

            current_frame += self.frames_transition

        if self.properties.setup_scene:
            bpy.context.scene.frame_end = current_frame

        # Create placeholder for duplicate frames (in order not to render those)
        # print("The following {} frames are duplicates and don't have to be rendered:".format(len(self.duplicate_frames)), self.duplicate_frames)
        print("There are {} frames that are duplicates and don't have to be rendered.".format(len(self.duplicate_frames)))
        if self.properties.skip_duplicates and len(self.duplicate_frames) > 0:
            if os.path.exists(bpy.context.scene.render.filepath):
                bpy.context.scene.render.use_overwrite = False
                print("Creating placeholder files ....")
                for f in self.duplicate_frames:
                    p = bpy.context.scene.render.filepath + "{:04d}".format(f)
                    if bpy.context.scene.render.use_file_extension:
                        p += bpy.context.scene.render.file_extension
                    open(p, 'a').close()
            else:
                print("WARNING: Unable to create placeholder files as output directoy does not exist:")
                print(bpy.context.scene.render.filepath)

        print("Photostory ready!")
        return {'FINISHED'}

    def create_title_slide(self, canvas_rect, text):
        slide = Slide(canvas_rect)  # fixme

        # Create text
        with In3D():
            bpy.ops.object.text_add(view_align=False, enter_editmode=True, location=(0, 0, 0))
            bpy.ops.font.select_all()
            bpy.ops.font.delete(type='NEXT_OR_SELECTION')
            bpy.ops.font.text_insert(text=text)
            text_object = bpy.context.active_object
            text_object.data.align_x = 'RIGHT' #'CENTER'
            text_object.data.size = 200
            text_object.data.extrude = 10
            leave_editmode()

        # Get / Create material
        material = bpy.data.materials.get("title_material")
        if material is None:
            material = bpy.data.materials.new(name="title_material")
            material.diffuse_color = (0, 0.8, 0.095)

        text_object.data.materials.append(material)
        text_object.parent = slide.root
        text_object.location = Vector((canvas_rect.width / 2, canvas_rect.height / 2, 0))
        slide.texts.append(text_object)

        return slide

    def create_photo_slide(self, canvas_rect, slide_desc, rotation_sigma, max_edge_transition):
        slide = Slide(canvas_rect, json=slide_desc, duration=self.properties.default_slide_duration)

        # Add photos to slide
        for p in slide_desc["foreground_paths"]:
            # print("Appending photo: ", self.images[p])
            slide.photos.append(Photo(self.images[os.path.abspath(p)]))
        for p in slide_desc["background_paths"]:
            # print("Appending photo: ", self.images[p])
            slide.photos_background.append(Photo(self.images[os.path.abspath(p)]))

        # Create layout
        slide.generate_layout(self.canvas)

        # Create photo objects
        for p in chain(slide.photos, slide.photos_background):
            self.create_photo_object(p, slide.root)

            # Check for videos
            if p.type == "MOVIE":
                if p.texture.image.frame_duration > slide.longest_video_frames:
                    slide.longest_video_frames = p.texture.image.frame_duration

        # Edit foreground photos
        for p in slide.photos:
            p.add_deformation(max_edge_transition)
            p.object.location.z = 1

        # Edit background photos
        for i, p in enumerate(slide.photos_background):
            p.object.location.z = i / len(slide.photos_background)

        slide.add_randomization(rotation_sigma)

        return slide

    def create_photo_object(self, photo, parent=None):
        # image = obj_image_load(context_imagepath_map, line, DIR, use_image_search, relpath)

        # Create mesh and object
        mesh_data = create_plane_meshdata(photo.width, photo.height, 0.025)
        photo.object = bpy.data.objects.new("photo", mesh_data)

        # Load texture
        photo.texture = bpy.data.textures.new(name="photo_texture", type='IMAGE')
        photo.texture.image = self.images[photo.image.filepath]

        # Create material (internal, no nodes)
        material = bpy.data.materials.new(name="photo_material")
        material.specular_intensity = 0
        photo.object.data.materials.append(material)

        # Add nodes setup as well:

        # Cycles
        material.use_nodes = True
        mat_nodes = material.node_tree.nodes
        mat_links = material.node_tree.links
        mat_nodes.clear()
        node_t = mat_nodes.new('ShaderNodeTexImage')
        node_t.image = photo.texture.image
        node_t.extension = 'CLIP'
        node_t.location = (0, 0)
        photo.texture_node = node_t
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

        if hasattr(bpy.types, 'ShaderNodeMaterial'):
            # Internal
            node_m = mat_nodes.new('ShaderNodeMaterial')
            node_m.location = (0, 500)
            node_m.material = material
            node_o = mat_nodes.new('ShaderNodeOutput')
            node_o.location = (300, 500)
            mat_links.new(node_m.outputs['Color'], node_o.inputs['Color'])

        if photo.texture.image.source == "MOVIE":
            photo.type = "MOVIE"
            self.setup_video_image_user(photo.texture, photo.texture.image_user)
            self.setup_video_image_user(photo.texture, photo.texture_node.image_user)
        else:
            photo.type = "PICTURE"

        # Location
        photo.object.location = Vector((photo.x, photo.y, 0))

        if parent is not None:
            photo.object.parent = parent

        bpy.context.view_layer.active_layer_collection.collection.objects.link(photo.object)

    def setup_video_image_user(self, texture, image_user):
        image_user.frame_duration = texture.image.frame_duration - 1  # -1 to avoid white texture at the end of video
        image_user.use_auto_refresh = True

    def create_background(self, num_slides, bg_type="White"):

        # Create mesh and object
        border_x = 2 * self.canvas.width
        border_y = 2 * self.canvas.height
        bg_width = (self.canvas.width+self.offset_slides) * num_slides + 2 * border_x
        bg_height = self.canvas.height + 2 * border_y
        mesh_data = create_plane_meshdata(bg_width, bg_height, -1)
        background = bpy.data.objects.new("background", mesh_data)

        # Load texture
        texture = bpy.data.textures.new(name="bg_texture", type='IMAGE')
        u = 1
        if bg_type == "Wood":
            texture.image = load_image(os.path.join(self.assets_dir, "floor.png"), None, recursive=False)
            u = bg_width / texture.image.size[0]

        # Add uv map
        mesh_data.uv_layers.new()
        mesh_data.uv_layers.active.data[0].uv = (0, 0)
        mesh_data.uv_layers.active.data[1].uv = (u, 0)
        mesh_data.uv_layers.active.data[2].uv = (u, 1)
        mesh_data.uv_layers.active.data[3].uv = (0, 1)

        # Create material
        material = bpy.data.materials.new(name="bg_material")
        material.specular_intensity = 0
        background.data.materials.append(material)

        # Location
        background.location = Vector((-border_x, -border_y, -5))
        bpy.context.view_layer.active_layer_collection.collection.objects.link(background)
        return background

    def create_map(self):
        map_rect = self.canvas.best_fit(layout.Rectangle(0, 0, 21600, 10800))
        self.world_map = world_map.WorldMap(map_rect.width,
                                            map_rect.height,
                                            os.path.join(self.assets_dir, "world.topo.bathy.200409.3x21600x10800.jpg"),
                                            os.path.join(self.assets_dir, "gebco_08_rev_elev_21600x10800.png"))
        self.world_map.object.location = Vector((map_rect.x, 1.5 * self.canvas.height, 1))


class PhotostoryImporterTestPanel(bpy.types.Panel):
    bl_label = "Photostory Importer TestPanel"
    bl_idname = "OBJECT_PT_photostory"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        self.layout.operator("import_scene.photostory")


def menu_func_import(self, context):
    self.layout.operator(PhotostoryImporter.bl_idname, text="Photostroy (.json)")


def register():
    bpy.utils.register_class(PhotostoryImporter)
    # bpy.utils.register_class(PhotostoryImporterTestPanel)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(PhotostoryImporter)
    # bpy.utils.unregister_class(PhotostoryImporterTestPanel)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
