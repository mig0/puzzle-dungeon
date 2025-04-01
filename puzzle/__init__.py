from constants import *
from cellactor import *
from objects import *
from flags import flags
from random import randint, random, shuffle, choice
from numpy import ndarray, arange, array_equal, ix_, argwhere, copyto
from solution import solution
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

	def __init__(self, level, Globals):
		self.map = None
		self.room = None
		self.level = level
		self.Globals = Globals
		self.area = Area()
		self.config_name = self.__class__.config_name()
		self.config = {} if type(level.get(self.config_name)) != dict else dict(level[self.config_name])
		self.load_map_special_cell_types = {CELL_SPECIAL0: 'str'}
		self.init()

	def init(self):
		pass

	def assert_config(self):
		return True

	def has_border(self):
		return self.level.get("has_border", True) and self.level.get("map_file") is None and self.level.get("map_string") is None

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

	def has_dirs(self):
		return False

	def is_goal_to_kill_enemies(self):
		return not self.has_finish() and not self.is_goal_to_be_solved()

	def is_goal_to_be_solved(self):
		return False

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

	def get_room_cells(self, *cell_types):
		return [ cell for cell in self.get_map_cells(*cell_types) if self.is_in_room(cell) ]

	def set_area_from_config(self, min_size=None, default_size=None, request_odd_size=False, align_to_center=False):
		max_size = flags.ROOM_SIZE(self.room.idx, request_odd_size)
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

		self.area.size = size
		self.area.size_x = size[0]
		self.area.size_y = size[1]
		self.area.x1 = self.room.x1 + (self.room.size_x - self.area.size_x) // 2 \
			+ ((self.room.size_x - self.area.size_x) % 2 * ((self.room.idx + 1 if self.room.idx is not None else 0) % 2) if align_to_center and flags.NUM_ROOMS == 4 else 0) \
			+ ((self.room.size_x - self.area.size_x) % 2 * ((self.room.idx + 1 if self.room.idx is not None else 0) % 3) if align_to_center and flags.NUM_ROOMS == 9 else 0)
		self.area.x2 = self.area.x1 + self.area.size_x - 1
		self.area.y1 = self.room.y1 + (self.room.size_y - self.area.size_y) // 2 \
			+ ((self.room.size_y - self.area.size_y) % 2 * (1 - ((self.room.idx if self.room.idx is not None else 2) // 2) % 2) if align_to_center and flags.NUM_ROOMS == 4 else 0) \
			+ ((self.room.size_y - self.area.size_y) % 2 * int(1.5 - ((self.room.idx if self.room.idx is not None else 3) // 3) % 3) if align_to_center and flags.NUM_ROOMS == 9 else 0)
		self.area.y2 = self.area.y1 + self.area.size_y - 1
		self.area.x_range = range(self.area.x1, self.area.x2 + 1)
		self.area.y_range = range(self.area.y1, self.area.y2 + 1)

	def is_in_area(self, cell):
		return self.Globals.is_cell_in_area(cell, self.area.x_range, self.area.y_range)

	def is_in_room(self, cell):
		return self.Globals.is_cell_in_area(cell, self.room.x_range, self.room.y_range)

	def set_area_border_walls(self):
		for x in self.area.x_range:
			self.map[x, self.area.y1 - 1] = CELL_WALL
			self.map[x, self.area.y2 + 1] = CELL_WALL
		for y in range(self.area.y1 - 1, self.area.y2 + 2):
			self.map[self.area.x1 - 1, y] = CELL_WALL
			self.map[self.area.x2 + 1, y] = CELL_WALL

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

	def on_set_theme(self):
		pass

	def set_map(self, map):
		self.map = map
		self.on_create_map()

	def on_create_map(self):
		pass

	def on_load_map(self, special_cell_values, extra_values):
		pass

	def get_map_extra_values(self):
		return ()

	def on_set_room(self):
		pass

	def set_room(self, room):
		self.room = room
		self.on_set_room()

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

	def on_draw(self, mode):
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

	def finish(self):
		pass

	def prepare_solution(self):
		return None

import os, pkgutil
for _, module, _ in pkgutil.iter_modules([os.path.dirname(__file__)]):
	__import__(__name__ + "." + module)

def get_all_puzzle_subclasses():
	return Puzzle.__subclasses__()

def create_puzzle(level, Globals):
	if not Puzzle.__subclasses__():
		print("Internal bug. Didn't find any Puzzle subclasses")
		quit()

	puzzle_class = Puzzle
	for cls in get_all_puzzle_subclasses():
		if cls.config_name() in level:
			puzzle_class = cls

	puzzle = puzzle_class(level, Globals)

	if not puzzle.assert_config():
		print("Level #%s: Requested %s, but config is incompatible, so ignoring it" % (level.get("n"), puzzle.__class__.__name__))
		puzzle = Puzzle(level, Globals)

	return puzzle

