import pygame
from pgzero.actor import Actor, POS_TOPLEFT, ANCHOR_CENTER, transform_anchor
from pgzero.animation import *
from pgzero import loaders
from typing import Union, Tuple
from sizetools import CELL_W, CELL_H
from config import ARROW_KEYS_RESOLUTION, ACTOR_PHASED_OPACITY
from game import game

MAX_ALPHA = 255  # based on pygame

NONE_CELL = (-1000, -1000)
NONE_SURFACE = pygame.Surface((0, 0))

active_inplace_animation_actors = []

def cmp(n1, n2):
	return 1 if n1 > n2 else 0 if n1 == n2 else -1

def product(x_range, y_range, run_by_y=False):
	if run_by_y:
		for x in x_range:
			for y in y_range:
				yield (x, y)
	else:
		for y in y_range:
			for x in x_range:
				yield (x, y)

def apply_diff(orig, diff, subtract=False, factor=1):
	if subtract:
		factor = -factor
	return (orig[0] + diff[0] * factor, orig[1] + diff[1] * factor)

def cell_diff(cell1, cell2):
	return (cell2[0] - cell1[0], cell2[1] - cell1[1])

def cell_dir(cell1, cell2):
	return (cmp(cell2[0], cell1[0]), cmp(cell2[1], cell1[1]))

def cell_to_pos_offset(cell, offset):
	return (CELL_W * (cell[0] + offset[0]), CELL_H * (cell[1] + offset[1]))

def cell_to_pos_00(cell):
	return cell_to_pos_offset(cell, (0, 0))

def cell_to_pos(cell):
	return cell_to_pos_offset(cell, (0.5, 0.5))

def pos_to_cell(pos):
	return (pos[0] // CELL_W, pos[1] // CELL_H)

def cell_distance(cell1, cell2):
	return abs(cell2[0] - cell1[0]) + abs(cell2[1] - cell1[1])

def sort_cells(cells):
	return sorted(cells, key=lambda cell: (cell[1], cell[0]))

@tweener
def example(n):
	return n

class Area:
	# x1, y1, x2, y2, size_x, size_y, x_range, y_range, idx

	@property
	def num_cells(self):
		return len(self.x_range) * len(self.y_range)

	@property
	def cells(self):
		return product(self.x_range, self.y_range)

	@property
	def cell11(self):
		return (self.x1, self.y1)

	@property
	def cell12(self):
		return (self.x1, self.y2)

	@property
	def cell21(self):
		return (self.x2, self.y1)

	@property
	def cell22(self):
		return (self.x2, self.y2)

	def is_cell_evnevn(self, cell):
		return (cell[0] - self.x1) % 2 == 0 and (cell[1] - self.y1) % 2 == 0

	def is_cell_evnodd(self, cell):
		return (cell[0] - self.x1) % 2 == 0 and (cell[1] - self.y1) % 2 == 1

	def is_cell_oddevn(self, cell):
		return (cell[0] - self.x1) % 2 == 1 and (cell[1] - self.y1) % 2 == 0

	def is_cell_oddodd(self, cell):
		return (cell[0] - self.x1) % 2 == 1 and (cell[1] - self.y1) % 2 == 1

	def is_cell_inside(self, cell, margin=0):
		return self.x1 + margin <= cell[0] <= self.x2 - margin and self.y1 + margin <= cell[1] <= self.y2 - margin

	def is_cell_on_margin(self, cell, margin=0):
		if margin > 0:
			return self.is_cell_inside(cell) and not self.is_cell_inside(cell, margin)
		if margin < 0:
			return not self.is_cell_inside(cell) and self.is_cell_inside(cell, margin)
		return False

def make_grayscale_image(image):
	gray_image = pygame.transform.grayscale(image)
	gray_image.fill((60, 60, 60), special_flags=pygame.BLEND_RGB_ADD)
	return gray_image

def colorize_image(image, color):
	image.fill(color, special_flags=pygame.BLEND_RGB_MULT)
	return image

class CellActor(Actor):
	def __init__(self, image:Union[str, pygame.Surface]=None, pos=POS_TOPLEFT, anchor=ANCHOR_CENTER, scale=None, color=None, **kwargs):
		self._image_name = None
		self._default_opacity = 1.0
		self._opacity = self._default_opacity
		self._scale = 1.0
		self._color = None
		self._flip = None
		self._selected = False
		self.cell_to_draw = None
		self._deferred_transform = False
		self._pending_transform = False
		self._mirror = None
		self._observers = {event_name: list() for event_name in ("cell_changed",)}

		self.reset_state()
		self.animation = None
		self.reset_inplace_animation()

		self.defer_transform()
		super().__init__(image, pos, anchor, **kwargs)
		self.scale = scale
		self.color = color
		self.apply_transform()

	def draw(self, cell=None, opacity=None):
		if self.hidden:
			if self.mirror:
				self.mirror.draw(cell, opacity)
			return
		if self.phased and opacity is None and not self._inplace_animation_active:
			opacity = ACTOR_PHASED_OPACITY
		if self.cell_to_draw and not cell:
			cell = self.cell_to_draw
		if cell:
			real_cell = self.c
			self.c = cell
		if opacity is not None:
			real_opacity = self.opacity
			self.opacity = opacity
		super().draw()
		if self.mirror:
			self.mirror.draw(cell, opacity)
		if cell:
			self.c = real_cell
		if opacity is not None:
			self.opacity = real_opacity

	def defer_transform(self):
		self._deferred_transform = True

	def apply_transform(self):
		self._deferred_transform = False
		if self._pending_transform:
			self._transform()

	@property
	def c(self):
		return None if self._cell == NONE_CELL else self._cell

	@property
	def cx(self):
		return self._cell[0]

	@property
	def cy(self):
		return self._cell[1]

	@c.setter
	def c(self, cell):
		old_cell = self._cell
		self._cell = NONE_CELL if cell is None else cell
		self.x, self.y = self.pos = self.get_pos()
		if self.mirror:
			self.mirror.c = self.c
		if old_cell != cell:
			self.emit("cell_changed")

	@property
	def s(self):
		return self._size

	@property
	def sx(self):
		return self._size[0] if self._size else 1

	@property
	def sy(self):
		return self._size[1] if self._size else 1

	@c.setter
	def s(self, size):
		self._size = size

	@property
	def angle(self):
		return self._angle

	@angle.setter
	def angle(self, angle):
		if angle is not None and angle != self._angle:
			self._angle = angle
			self._transform()

	@property
	def opacity(self):
		return self._opacity

	@opacity.setter
	def opacity(self, opacity):
		opacity = min(1.0, max(0.0, opacity))
		if opacity != self._opacity:
			self._opacity = opacity
			self._transform()

	@property
	def scale(self):
		return self._scale

	@scale.setter
	def scale(self, scale):
		if scale is not None and scale != self._scale:
			self._scale = scale
			self._transform()

	@property
	def color(self):
		return self._color

	@color.setter
	def color(self, color):
		if color != self._color:
			self._color = color
			self._transform()

	@property
	def selected(self):
		return self._selected

	@selected.setter
	def selected(self, selected):
		if selected != self._selected:
			self._selected = selected
			self._transform()

	@property
	def flip(self):
		return self._flip

	@flip.setter
	def flip(self, flip):
		if flip != self._flip:
			self._flip = flip
			self._transform()

	@property
	def image(self):
		return self._image_name

	@image.setter
	def image(self, image:Union[str, pygame.Surface]):
		if image is None or isinstance(image, pygame.Surface):
			if hasattr(self, '_orig_surf') and self._orig_surf == image:
				return
			self._image_name = None
			self._surf = self._orig_surf = image or NONE_SURFACE
			self._update_pos()
			self._transform()
		elif isinstance(image, str):
			if self.image == image:
				return
			self._image_name = image
			self._surf = self._orig_surf = loaders.images.load(image)
			self._update_pos()
			self._transform()
		else:
			print("CellActor.image: Unsupported type: " + str(image))
			pass

	@property
	def mirror(self):
		return self._mirror

	@mirror.setter
	def mirror(self, mirror):
		self._mirror = mirror
		if mirror is not None:
			mirror.c = self.c

	def reset_state(self):
		self._cell, self._size, self.hidden, self.phased = NONE_CELL, None, False, False

	def get_state(self):
		return (self.c, self.s, self.hidden, self.phased)

	def restore_state(self, state):
		self.c, self.s, self.hidden, self.phased = state

	def get_pos(self):
		return cell_to_pos(self._cell)

	def sync_pos(self):
		self.pos = self.get_pos()

	def sync_cell(self):
		self.c = pos_to_cell(self.pos)

	def apply_pos_diff(self, diff, subtract=False, factor=1):
		return apply_diff(cell_to_pos(self.c), diff, subtract, factor)

	def move_pos(self, diff, undo=False, factor=1):
		self.pos = self.apply_pos_diff(diff, undo, factor)

	def move(self, diff, undo=False):
		game.remember_obj_state(self)
		self.c = apply_diff(self.c, diff, undo)

	def move_animated(self, diff=None, target=None, enable_animation=True, on_finished=None):
		if diff is None and target is None:
			return
		if diff is None:
			diff = cell_diff(self.c, target)
		if target is None:
			target = apply_diff(self.c, diff)

		old_pos = self.pos
		old_cell = self.c
		self.move(diff)
		if enable_animation:
			distance = cell_distance(old_cell, target)
			animate_time_factor = distance - (distance - 1) / 2
			self.pos = old_pos
			self.animate(animate_time_factor * ARROW_KEYS_RESOLUTION, on_finished=on_finished)
			if self.mirror:
				self.mirror.pos = old_pos
				self.mirror.animate(animate_time_factor * ARROW_KEYS_RESOLUTION)

	def watch(self, event_name, observer):
		method_name = f"on_actor_{event_name}"
		assert hasattr(observer, method_name), f"{observer} must implement {method_name}"
		assert event_name in self._observers, f"Invalid event name {event_name}"
		self._observers[event_name].append(observer)

	def emit(self, event_name):
		for observer in self._observers[event_name]:
			method = getattr(observer, f"on_actor_{event_name}")
			method(self)

	def _transform(self):
		if not hasattr(self, '_orig_surf'):
			return

		if self._deferred_transform:
			self._pending_transform = True
			return
		self._pending_transform = False

		if self._orig_surf == NONE_SURFACE:
			return

		self._surf = self._orig_surf
		p = self.pos

		if self._color is not None:
			self._surf = colorize_image(make_grayscale_image(self._surf), self._color)
		if self._selected:
			self._surf = colorize_image(self._surf.copy(), (192, 192, 192))
		if self._scale != 1:
			size = self._orig_surf.get_size()
			self._surf = pygame.transform.scale(self._surf, (int(size[0] * self._scale), int(size[1] * self._scale)))
		if self._flip and (self._flip[0] or self._flip[1]):
			self._surf = pygame.transform.flip(self._surf, *self._flip)
		if self._angle != 0.0:
			self._surf = pygame.transform.rotate(self._surf, self._angle)

		alpha = int(self._opacity * MAX_ALPHA + 0.5)
		if alpha != MAX_ALPHA:
			alpha_img = pygame.Surface(self._surf.get_size(), pygame.SRCALPHA)
			alpha_img.fill((255, 255, 255, alpha))
			alpha_img.blit(self._surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
			self._surf = alpha_img

		self.width, self.height = self._surf.get_size()
		w, h = self._orig_surf.get_size()
		ax, ay = self._untransformed_anchor
		anchor = transform_anchor(ax, ay, w, h, self._angle)
		self._anchor = (anchor[0] * self._scale, anchor[1] * self._scale)

		self.pos = p

	def reset_inplace(self):
		self.defer_transform()
		self.opacity = self._default_opacity
		self.scale = 1.0
		self.angle = 0.0
		self.flip  = None
		self.apply_transform()

	def is_inplace_animation_active(self):
		return self._inplace_animation_active

	def unset_inplace_animation(self, hard=True):
		if self in active_inplace_animation_actors:
			active_inplace_animation_actors.remove(self)
		self._inplace_animation_active  = False
		self._inplace_animation_opacity = None
		self._inplace_animation_scale   = None
		self._inplace_animation_angle   = None
		self._inplace_animation_flip    = None
		self._inplace_animation_tween   = None
		self._inplace_animation_start_time  = None
		self._inplace_animation_duration    = None
		self._inplace_animation_on_finished = None

	def reset_inplace_animation(self):
		self.unset_inplace_animation()
		self.reset_inplace()

	def activate_inplace_animation(self, start_time, duration, opacity:Tuple[float, float]=None, scale:Tuple[float, float]=None, angle:Tuple[float, float]=None, flip:Tuple[bool, bool, int]=None, tween="linear", on_finished=None):
		self.unset_inplace_animation()

		self.defer_transform()

		is_defined = False
		if opacity:
			self._inplace_animation_opacity = opacity
			self.opacity = opacity[0]
			is_defined = True
		if scale:
			self._inplace_animation_scale = scale
			self.scale = scale[0]
			is_defined = True
		if angle:
			self._inplace_animation_angle = angle
			self.angle = angle[0]
			is_defined = True
		if flip and (flip[0] or flip[1]):
			self._inplace_animation_flip = flip
			is_defined = True
		if not is_defined:
			print("activate_inplace_animation called without opacity, scale or angle or flip, skipping")
			return

		self.apply_transform()

		self._inplace_animation_tween       = tween
		self._inplace_animation_start_time  = start_time
		self._inplace_animation_duration    = duration
		self._inplace_animation_on_finished = on_finished

		self._inplace_animation_active = True
		active_inplace_animation_actors.append(self)

	def update_inplace_animation(self, time):
		if not self.is_inplace_animation_active():
			return

		if self._inplace_animation_start_time == 0:
			self._inplace_animation_start_time = time

		factor = (time - self._inplace_animation_start_time) / self._inplace_animation_duration
		if factor > 1:
			factor = 1
		if factor < 0:
			factor = 0
		factor = TWEEN_FUNCTIONS[self._inplace_animation_tween](factor)

		self.defer_transform()

		if self._inplace_animation_opacity:
			self.opacity = self._inplace_animation_opacity[0] + factor * (self._inplace_animation_opacity[1] - self._inplace_animation_opacity[0])
		if self._inplace_animation_scale:
			self.scale   = self._inplace_animation_scale[0]   + factor * (self._inplace_animation_scale[1]   - self._inplace_animation_scale[0])
		if self._inplace_animation_angle:
			self.angle   = self._inplace_animation_angle[0]   + factor * (self._inplace_animation_angle[1]   - self._inplace_animation_angle[0])
		if self._inplace_animation_flip:
			self.flip = [ False, False ]
			if self._inplace_animation_flip[0] and int((0.999 if factor > 0.999 else factor) * self._inplace_animation_flip[2]) % 2 == self._inplace_animation_flip[2] % 2:
				self.flip[0] = True
			if self._inplace_animation_flip[1] and int((0.999 if factor > 0.999 else factor) * self._inplace_animation_flip[2]) % 2 == self._inplace_animation_flip[2] % 2:
				self.flip[1] = True

		self.apply_transform()

		if factor == 1:
			on_finished = self._inplace_animation_on_finished
			self.unset_inplace_animation()
			if on_finished:
				on_finished()

	def reset_animation(self):
		if self.animation is None:
			return
		self.animation.stop()
		self.animation = None

	def _finish_animation(self, on_finished=None):
		self.animation = None
		if on_finished:
			on_finished()

	def animate(self, duration, tween="linear", pos=None, on_finished=None):
		if pos is None:
			pos = self.get_pos()
		self.animation = animate(self, tween=tween, duration=duration, pos=pos, on_finished=lambda: self._finish_animation(on_finished))

	def is_animated_external(self):
		return self.animation is not None

	def is_animated(self):
		return self.is_inplace_animation_active() or self.is_animated_external()

	def reset_opacity(self):
		self._opacity = self._default_opacity
		self._transform()

	def set_default_opacity(self, default_opacity):
		is_default_opacity = self._opacity == self._default_opacity
		self._default_opacity = default_opacity
		if is_default_opacity and self._opacity != self._default_opacity:
			self.reset_opacity()

def create_actor(image_name, cell):
	actor = CellActor(image_name)
	actor.c = cell
	return actor

def get_actor_on_cell(cell, actors, include_hidden=None, include_phased=None):
	for actor in actors:
		if (cell == actor.c
			and (not actor.hidden or (actor.mirror if include_hidden is None else include_hidden))
			and (not actor.phased or (actor.mirror if include_phased is None else include_phased))
		):
			return actor
	return None

def is_cell_in_actors(cell, actors, include_hidden=None, include_phased=None):
	return get_actor_on_cell(cell, actors, include_hidden, include_phased) is not None

