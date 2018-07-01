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

import copy
import random
import numpy as np
from mathutils import Vector


class Size:
    def __init__(self, w=0, h=0):
        self.size = Vector((w, h))

    @property
    def width(self):
        return self.size[0]

    @width.setter
    def width(self, w):
        self.size[0] = w

    @property
    def height(self):
        return self.size[1]

    @height.setter
    def height(self, h):
        self.size[1] = h

    def __str__(self):
        return "[{}x{}]".format(self.width, self.height)


class Position:
    def __init__(self, x=0, y=0):
        self.position = Vector((x, y))

    @property
    def x(self):
        return self.position[0]

    @x.setter
    def x(self, v):
        self.position[0] = v

    @property
    def y(self):
        return self.position[1]

    @y.setter
    def y(self, v):
        self.position[1] = v

    def __str__(self):
        return "[{},{}]".format(self.x, self.y)

class Ray:
    def __init__(self, position=Vector((0,0)), direction=Vector((0,0))):
        self.position = position
        self.direction = direction

    def get_point(self, direction_scaling):
        return self.position + self.direction * direction_scaling


class Rectangle(Size, Position):
    def __init__(self, x=0, y=0, w=0, h=0):
        Size.__init__(self, w, h)
        Position.__init__(self, x, y)

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.width

    @property
    def top(self):
        return self.y

    @property
    def bottom(self):
        return self.y + self.height

    @property
    def center(self):
        return Position(0.5 * self.left + 0.5 * self.right,
                        0.5 * self.top + 0.5 * self.bottom)

    @center.setter
    def center(self, c):
        self.position = c - 0.5 * self.size

    @property
    def area(self):
        return self.width * self.height

    @property
    def is_positive(self):
        return self.right > self.left and self.bottom > self.top

    def __str__(self):
        return "Rectangle({} {})".format(Position.__str__(self), Size.__str__(self))

    def aspect(self):
        if self.height == 0:
            return 0
        return self.width / self.height

    def scale(self, factor):
        self.position *= factor
        self.size *= factor

    def set_rect(self, rect):
        self.position = rect.position.copy()
        self.size = rect.size.copy()

    def best_fit(self, rect):
        """
        Scale rect to fit into this rectangle with the largest possible area
        """
        result = Rectangle()
        if rect.aspect() > self.aspect():
            result.width = self.width
            result.height = self.width / rect.aspect()
        else:
            result.height = self.height
            result.width = self.height * rect.aspect()
        result.x = self.x + 0.5 * (self.width - result.width)
        result.y = self.y + 0.5 * (self.height - result.height)
        return result

    def intersection(self, other):
        intersection_left = max(self.left, other.left)
        intersection_right = min(self.right, other.right)
        intersection_top = max(self.top, other.top)
        intersection_bottom = min(self.bottom, other.bottom)
        return Rectangle(intersection_left,
                         intersection_top,
                         intersection_right - intersection_left,
                         intersection_bottom - intersection_top)

    def intersects(self, other, margin=0):
        intersection = self.intersection(other)
        return intersection.width > margin and intersection.height > margin

    @staticmethod
    def merge(rect1, rect2):
        x = min(rect1.x, rect2.x)
        y = min(rect1.y, rect2.y)
        w = max(rect1.right, rect2.right) - x
        h = max(rect1.bottom, rect2.bottom) - y
        return Rectangle(x, y, w, h)

    @staticmethod
    def bounding_box(rectangles):
        if len(rectangles) < 1:
            raise RuntimeError("'bounding_box' requires at least 1 input rectangle")
        result = rectangles[0]
        for r in rectangles[1:]:
            result = Rectangle.merge(result, r)
        return result

    @staticmethod
    def get_largest(rectangles):
        if len(rectangles) < 1:
            raise RuntimeError("'get_largest' requires at least 1 input rectangle")
        largest_area = rectangles[0].area
        largest = rectangles[0]
        for r in rectangles[1:]:
            area = r.area
            if area > largest_area:
                largest_area = area
                largest = r
        return largest


    # @staticmethod
    # def from_path(path):
    #     image = Image()
    #     image.path = path
    #     # This is lazy and does not read the whole image from disc
    #     #header = PIL.Image.open(path)
    #     with PIL.Image.open(path) as header:
    #         image.width, image.height = header.size
    #     return image



def is_valid_configuration(existing_rectangles, rectangle):
    if rectangle.x < 0 or rectangle.y < 0:
        return False
    for r in existing_rectangles:
        if r.intersects(rectangle, margin=0.5):
            return False
    return True


# def generate_layout(rectangles, canvas):
def arrange_rects_in_canvas_1(rectangles, canvas):
    """

    :param rectangles: List of rectangles, which need to be arranged. Edited in place.
    :param canvas: Canvas for arrangement
    :return Scale factor, applied to rectangles
    """

    if len(rectangles) == 0:
        return 1

    if canvas.width <= 0 or canvas.height <= 0:
        raise RuntimeError("Invalid canvas size.")

    rectangles[0].x = 0
    rectangles[0].y = 0
    aspect_ratio = canvas.width / canvas.height
    bounding_box = rectangles[0]

    for i, rect in enumerate(rectangles[1:], 1):
        best_aspect_diff = 0
        best_config = None

        for rect_n in rectangles[:i]:
            # Possible configurations for new rectangle
            test_configurations = [
                Rectangle(rect_n.right, rect_n.top, rect.width, rect.height),
                Rectangle(rect_n.right, rect_n.bottom - rect.height, rect.width, rect.height),
                Rectangle(rect_n.left, rect_n.bottom, rect.width, rect.height),
                Rectangle(rect_n.right - rect.width, rect_n.bottom, rect.width, rect.height)
            ]

            # Find best configuration
            for ic, c in enumerate(test_configurations):
                if is_valid_configuration(rectangles[:i], c):
                    aspect = Rectangle.merge(c,bounding_box).aspect()
                    aspect_diff = abs(aspect_ratio - aspect)
                    if best_config is None or aspect_diff < best_aspect_diff:
                        best_config = c
                        best_aspect_diff = aspect_diff

        bounding_box = Rectangle.merge(best_config, bounding_box)
        rect.set_rect(best_config)

    # Scale created layout to fit canvas
    factor = min(canvas.width / bounding_box.width, canvas.height / bounding_box.height)
    for r in rectangles:
        r.x *= factor
        r.y *= factor
        r.width *= factor
        r.height *= factor

    return factor


def arrange_rects_in_background_1(rects, foreground_rects, canvas):
    # Evenly distribute background pictures
    if len(rects) <= 0:
        return

    angle_offset = 2 * np.pi / len(rects)
    center = Vector((0.5 * canvas.width, 0.5 * canvas.height))
    angle = 0
    largest_fg_area = Rectangle.get_largest(foreground_rects).area
    for r in rects:
        a = angle + random.normalvariate(0, np.pi * 0.07)
        ray = Ray(center, Vector((np.sin(a), np.cos(a))))
        t = intersect_ray_rectangle(ray, canvas)
        border_point = ray.get_point(t)
        ray = Ray(border_point, -ray.direction)
        t = intersect_ray_rectangles(ray, foreground_rects)
        if t is None:
            fg_point = center
        else:
            fg_point = ray.get_point(t)

        pos = 0.5 * fg_point + 0.5 * border_point
        r.scale(1.2 * np.sqrt(largest_fg_area / r.area))
        r.center = pos
        angle += angle_offset



def generate_layout_1(foreground_rects, background_rects, canvas):
    bg_scale = 0.85 * arrange_rects_in_canvas_1(foreground_rects, canvas)

    if len(background_rects) > 0:
        scale_layout(foreground_rects, 0.85)
    center_layout(foreground_rects, canvas)

    arrange_rects_in_background_1(background_rects, foreground_rects, canvas)


def center_layout(rectangles, canvas):
    """
    Adjust the position of each rectangle in 'rectangles' in order to center them in the canvas. Edited in place.
    :param rectangles: List of rectangles
    :param canvas:
    """
    if len(rectangles) < 1:
        return
    bb = Rectangle.bounding_box(rectangles)
    ox = (canvas.width - bb.width) / 2 - bb.x
    oy = (canvas.height - bb.height) / 2 - bb.y
    for r in rectangles:
        r.x += ox
        r.y += oy


def scale_layout(rectangles, factor):
    for r in rectangles:
        r.scale(factor)


def get_background_rectangles(rectangles, canvas):
    """
    Subtract foreground rectangles from the canvas and return resulting background rectangles.
    :param rectangles: Foreground rectangles.
    :param canvas:
    :return: List of rectangles filling the background
    """
    background_rectangles = [copy.copy(canvas)]
    for rect in rectangles:
        idx_offset = 0
        for i in range(len(background_rectangles)):
            idx_bg = i-idx_offset
            bg_rect = background_rectangles[idx_bg]
            intersection = rect.intersection(bg_rect)
            if intersection.is_positive:
                if rect.left > bg_rect.left:
                    background_rectangles.append(Rectangle(bg_rect.left, bg_rect.top, rect.left - bg_rect.left, bg_rect.height))
                if rect.right < bg_rect.right:
                    background_rectangles.append(Rectangle(rect.right, bg_rect.top, bg_rect.right - rect.right, bg_rect.height))
                if rect.top > bg_rect.top:
                    background_rectangles.append(Rectangle(intersection.left, bg_rect.top, intersection.width, rect.top - bg_rect.top))
                if rect.bottom < bg_rect.bottom:
                    background_rectangles.append(Rectangle(intersection.left, rect.bottom, intersection.width, bg_rect.bottom - rect.bottom))

                del background_rectangles[idx_bg]
                idx_offset += 1

    return background_rectangles


def sample_in_rectangles(rectangles):
    """
    Sample a random point from a list of rectangles
    :param rectangles: Input rectangles
    :return: Random 2D point (x,y)
    """
    if len(rectangles) == 0:
        raise RuntimeError("Called 'sample_in_rectangles' with empty list.")

    areas = [r.area for r in rectangles]
    total_area = sum(areas)

    x = random.random() * total_area
    a = 0
    for i, ai in enumerate(areas):
        a += ai
        if x <= a:
            break

    rect = rectangles[i]
    return (rect.x + random.random() * rect.width,
            rect.y + random.random() * rect.height)


def intersect_ray_segment(ray, seg_p0, seg_p1):
    """
    Intersect a ray with a line segment
    :param ray_p: mathutils.Vector Starting point of ray
    :param ray_d: mathutils.Vector Direction of ray
    :param seg_p0: mathutils.Vector Starting point of segment
    :param seg_p1: mathutils.Vector End point of segmenet
    :return:
    """
    try:
        a = np.array([[ray.direction[0], seg_p1[0] - seg_p0[0]],
                      [ray.direction[1], seg_p1[1] - seg_p0[1]]])
        b = np.array([seg_p1[0] - ray.position[0],
                      seg_p1[1] - ray.position[1]])
        x = np.linalg.solve(a, b)
        if x[0] >= 0 and 1 >= x[1] >= 0:
            return x[0]
    except np.linalg.linalg.LinAlgError:
        pass
    return None


def intersect_ray_rectangle(ray, rect):
    segments = [((rect.left, rect.top), (rect.right, rect.top)),
                ((rect.right, rect.top), (rect.right, rect.bottom)),
                ((rect.left, rect.bottom), (rect.right, rect.bottom)),
                ((rect.left, rect.top), (rect.left, rect.bottom))]
    d = None
    for s in segments:
        sd = intersect_ray_segment(ray, s[0], s[1])
        if sd is not None:
            if d is None or sd < d:
                d = sd
    return d


def intersect_ray_rectangles(ray, rects):
    d = None
    for r in rects:
        rd = intersect_ray_rectangle(ray, r)
        if rd is not None:
            if d is None or rd < d:
                d = rd
    return d