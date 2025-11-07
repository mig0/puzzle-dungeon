from constants import *
from cellactor import *
from objects import *
from common import *
from debug import *
from image import *
from theme import *
from draw import *
from room import *
from game import game
from flags import flags
from time import time
from grid import grid
from pgzero import clock
from random import randint, random, sample, shuffle, choice, choices
from numpy import ndarray, arange, array_equal, ix_, argwhere, copyto
from solution import solution
from translate import t, concatenate_items
from sizetools import import_size_constants
from puzzleinfo import PuzzleInfo
from statusmessage import set_status_message

class Puzzle:
	@classmethod
	def canonic_name(cls):
		return cls.__name__.lower().removesuffix("puzzle")

	@classmethod
	def config_name(cls):
		return None if cls == Puzzle else cls.canonic_name() + '_puzzle'

	@classmethod
	def get_info(cls):
		return PuzzleInfo(cls.canonic_name())

	def __init__(self, Globals):
		self.map = None
		self.Globals = Globals
		self.area = Area()
		self.config = game.level.puzzle_config
		self.load_map_special_cell_types = {CELL_SPECIAL0: 'str'}
		grid.reset()
		self.init()

	def init(self):
		pass

	def assert_config(self):
		return True

	def has_border(self):
		return game.level.has_border and game.level.map_file is None and game.level.map_string is None

	def is_long_generation(self):
		return False

	def is_finish_cell_required(self):
		return False

	def has_start(self):
		return False

	def has_finish(self):
		return self.is_finish_cell_required()

	def has_plate(self):
		return False

	def has_portal(self):
		return False

	def has_gate(self):
		return False

	def has_locks(self):
		return False

	def has_sand(self):
		return False

	def has_odirs(self):
		return False

	def has_glass(self):
		return False

	def has_trap(self):
		return False

	def has_beam(self):
		return False

	def is_virtual(self):
		return False

	def is_goal_to_kill_enemies(self):
		return not self.is_virtual() and not self.has_finish() and not self.is_goal_to_be_solved()

	def is_goal_to_be_solved(self):
		return False

	def die(self, msg):
		die("%s fatal error: %s" % (self.__class__.__name__, msg))

	def parse_config_num(self, config_key, default):
		num = self.config.get(config_key, default)
		if type(num) in (tuple, range):
			num = choice(num)
		return num

	def get_map_cells(self, *cell_types):
		cells = []
		for cy in MAP_Y_RANGE:
			for cx in MAP_X_RANGE:
				if self.map[cx, cy] in cell_types:
					cells.append((cx, cy))
		return cells

	def get_area_cells(self, *cell_types):
		return [cell for cell in self.area.cells if self.map[cell] in cell_types]

	def get_room_cells(self, *cell_types):
		return [cell for cell in room.cells if self.map[cell] in cell_types]

	def _fit_room_size(self, request_odd=False):
		def round_odd(n):
			return (n - 1) // 2 * 2 + 1
		return (round_odd(room.size_x), round_odd(room.size_y)) if request_odd else room.size

	def set_area_from_config(self, min_size=None, default_size=None, request_odd_size=False, align_to_center=False):
		max_size = self._fit_room_size(request_odd_size)
		if min_size is None:
			min_size = (3, 3) if request_odd_size else (2, 2)

		size = list(self.config.get("size", default_size or max_size))
		if size[0] < min_size[0]:
			size[0] = min_size[0]
		if size[1] < min_size[1]:
			size[1] = min_size[1]
		if size[0] > max_size[0]:
			size[0] = max_size[0]
		if size[1] > max_size[1]:
			size[1] = max_size[1]

		size_x, size_y = size
		x1 = room.x1 + (room.size_x - size_x) // 2 \
			+ ((room.size_x - size_x) % 2 * ((room.idx + 1 if room.idx is not None else 0) % 2) if align_to_center and flags.NUM_ROOMS == 4 else 0) \
			+ ((room.size_x - size_x) % 2 * ((room.idx + 1 if room.idx is not None else 0) % 3) if align_to_center and flags.NUM_ROOMS == 9 else 0)
		y1 = room.y1 + (room.size_y - size_y) // 2 \
			+ ((room.size_y - size_y) % 2 * (1 - ((room.idx if room.idx is not None else 2) // 2) % 2) if align_to_center and flags.NUM_ROOMS == 4 else 0) \
			+ ((room.size_y - size_y) % 2 * int(1.5 - ((room.idx if room.idx is not None else 3) // 3) % 3) if align_to_center and flags.NUM_ROOMS == 9 else 0)
		self.area.set(x1, y1, x1 + size_x - 1, y1 + size_y - 1)

	def is_in_area(self, cell):
		return is_cell_in_area(cell, self.area.x_range, self.area.y_range)

	def is_in_room(self, cell):
		return is_cell_in_room(cell)

	def set_area_border_walls(self, width=1):
		for cell in room.cells:
			if self.area.is_cell_on_margin(cell, -width if width > 0 else -100):
				self.map[cell] = CELL_WALL

	def set_area_cells(self, cell_type, add_border_walls=False):
		for cell in self.area.cells:
			self.map[cell] = cell_type
		if add_border_walls:
			self.set_area_border_walls()

	def get_random_cell_in_area(self):
		return (choice(self.area.x_range), choice(self.area.y_range))

	def get_random_matching_cell_in_area(self, cell_types, obstacles=[]):
		bad_cells = {}
		while True:
			cell = self.get_random_cell_in_area()
			if cell not in obstacles and self.map[cell] in cell_types:
				return cell
			bad_cells[cell] = True
			if len(bad_cells) == self.area.num_cells:
				return None

	def get_random_floor_cell_in_area(self, obstacles=[]):
		return self.get_random_matching_cell_in_area(CELL_FLOOR_TYPES, obstacles)

	def get_random_wall_cell_in_area(self, obstacles=[]):
		return self.get_random_matching_cell_in_area(CELL_WALL_TYPES, obstacles)

	def convert_to_floor(self, cell):
		self.Globals.convert_to_floor_if_needed(cell)

	def generate_best_random_setups(self, max_setups, max_good_setups, max_time, generate_random_setup):
		start_time = time()
		num_setups = 0
		num_good_setups = 0
		best_setup = None
		best_weight = None

		while (num_setups < max_setups and num_good_setups < max_good_setups and (not best_setup or time() < start_time + max_time)):
			result = generate_random_setup()
			if result:
				weight, setup = result
				num_good_setups += 1
				if not best_setup or weight > best_weight:
					best_weight = weight
					best_setup = setup
			num_setups += 1

		return best_setup

	def on_set_theme(self):
		pass

	def set_map(self):
		self.map = game.map
		self.on_create_map()

	def on_create_map(self):
		pass

	def on_load_map(self, special_cell_values, extra_values):
		pass

	def get_map_extra_values(self):
		return ()

	def on_set_room(self):
		pass

	def on_enter_room(self):
		pass

	def set_finish_cell(self, accessible_cells, finish_cell):
		self.accessible_cells = accessible_cells
		self.finish_cell = finish_cell

	def generate_room(self):
		pass

	def on_generate_map(self):
		pass

	def is_lost(self):
		return False

	def is_solved(self):
		return False

	def store_level(self, stored_level):
		pass

	def restore_level(self, stored_level):
		pass

	def modify_cell_types_to_draw(self, cell, cell_types):
		pass

	def get_cell_image_to_draw(self, cell, cell_type):
		return None

	def on_draw_map(self):
		pass

	def on_draw(self):
		pass

	def press_cell(self, cell, button=None):
		return False

	def on_press_key(self, keyboard):
		pass

	def on_update(self, level_time):
		pass

	def on_leave_cell(self):
		pass

	def on_prepare_enter_cell(self):
		pass

	def on_enter_cell(self):
		pass

	def on_cursor_enter_cell(self):
		pass

	def finish(self):
		pass

	def is_char_phased(self):
		return False

	def on_undo_move(self):
		pass

	def prepare_solution(self):
		return None

class VirtualPuzzle(Puzzle):
	def is_virtual(self):
		return True

import os, pkgutil
for _, module, _ in pkgutil.iter_modules([os.path.dirname(__file__)]):
	__import__(__name__ + "." + module)

def get_all_puzzle_classes():
	return [Puzzle] + Puzzle.__subclasses__() + VirtualPuzzle.__subclasses__()

def create_puzzle(Globals):
	if not Puzzle.__subclasses__():
		print("Internal bug. Didn't find any Puzzle subclasses")
		quit()

	puzzle_class = next(pc for pc in get_all_puzzle_classes() if pc.__name__ == game.level.puzzle_type)

	puzzle = puzzle_class(Globals)

	if not puzzle.assert_config():
		print("Level %s: Requested %s, but config is incompatible, so ignoring it" % (game.level.get_id(), puzzle.__class__.__name__))
		puzzle = Puzzle(Globals)

	return puzzle

