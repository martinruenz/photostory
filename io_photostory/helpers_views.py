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

"""
Blender area types:
‘EMPTY’, ‘VIEW_3D’, ‘TIMELINE’, ‘GRAPH_EDITOR’, ‘DOPESHEET_EDITOR’, ‘NLA_EDITOR’, ‘IMAGE_EDITOR’, ‘CLIP_EDITOR’,
‘SEQUENCE_EDITOR’, ‘NODE_EDITOR’, ‘TEXT_EDITOR’, ‘LOGIC_EDITOR’, ‘PROPERTIES’, ‘OUTLINER’, ‘USER_PREFERENCES’, ‘INFO’,
‘FILE_BROWSER’, ‘CONSOLE’

Blender context modes:
‘EDIT_MESH’, ‘EDIT_CURVE’, ‘EDIT_SURFACE’, ‘EDIT_TEXT’, ‘EDIT_ARMATURE’, ‘EDIT_METABALL’, ‘EDIT_LATTICE’, ‘POSE’,
‘SCULPT’, ‘PAINT_WEIGHT’, ‘PAINT_VERTEX’, ‘PAINT_TEXTURE’, ‘PARTICLE’, ‘OBJECT’
"""

class InView:
    """
    This class tries to change the current area to a specific (derived) type.
    It only works if 'bpy.context.area' is not None.
    """
    def __init__(self, view):
        self.view = view

    def __enter__(self):
        self.original_areatype = bpy.context.area.type
        bpy.context.area.type = self.view
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        bpy.context.area.type = self.original_areatype


class In3D(InView):
    def __init__(self):
        InView.__init__(self, 'VIEW_3D')


class InProperties(InView):
    def __init__(self):
        InView.__init__(self, 'PROPERTIES')


def get_override(area_type):
    """
    Searches areas in all windows for the provided 'area_type' and returns an override dict
    Example: get_override('VIEW_3D')
    :param area_type: String, which identifies the view
    :return: override dict for requested type, or exception is thrown
    """
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == area_type:
                region = None
                for r in area.regions:
                    if r.type == 'WINDOW':
                        region = r
                        break

                return {'window': window, 'screen': window.screen, 'area': area, 'region': region, 'scene': bpy.context.scene}
    raise RuntimeError("Target area type not available:", area_type)


def get_area(area_type):
    """
    Searches areas in all windows for the provided 'area_type'
    Example: get_area('VIEW_3D')
    :param area_type: String, which identifies the view
    :return: bpy.types.Area of requested type, or exception is thrown
    """
    return get_override(area_type)['area']


def get_area_3d():
    return get_area('VIEW_3D')


def get_area_properties():
    return get_area('PROPERTIES')


def enter_editmode(obj, execution_context=None):
    if bpy.context.mode != 'OBJECT':
        leave_editmode()

    if execution_context is None:
        execution_context = get_override('VIEW_3D')

    # with In3D():
    bpy.ops.object.select_all(execution_context, action='DESELECT')
    bpy.context.scene.objects.active = obj
    bpy.ops.object.mode_set(execution_context, mode='EDIT', toggle=False)
    return execution_context


def leave_editmode(execution_context=None):
    if execution_context is None:
        execution_context = get_override('VIEW_3D')
    bpy.ops.object.mode_set(execution_context, mode='OBJECT', toggle=False)


def select_only(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select = True

