from constants import *
from sizetools import DEFAULT_MAP_SIZE, get_fitting_map_size, import_size_constants
from common import die
from load import detect_map_file

class Flags:
	def parse_level(self, level):
		self.is_random_maze    = level.random_maze
		self.is_spiral_maze    = level.spiral_maze
		self.is_grid_maze      = level.grid_maze
		self.is_four_rooms     = level.four_rooms
		self.is_nine_rooms     = level.nine_rooms
		self.is_cloud_mode     = level.cloud_mode
		self.is_enemy_key_drop = level.enemy_key_drop
		self.is_stopless       = level.stopless
		self.is_reverse_barrel = level.reverse_barrel_mode
		self.has_start         = level.has_start
		self.has_finish        = level.has_finish
		self.is_cheat_mode     = CHEAT_MODE

		self.is_any_maze = self.is_random_maze or self.is_spiral_maze or self.is_grid_maze

		if self.is_four_rooms:
			self.NUM_ROOMS = 4
		elif self.is_nine_rooms:
			self.NUM_ROOMS = 9
		else:
			self.NUM_ROOMS = 1

		self.MULTI_ROOMS = self.NUM_ROOMS > 1

		if level.map_size is None:
			if level.map_string or level.map_file:
				map_info = detect_map_file(level.map_file, map_string=level.map_string)
				if map_info is None:
					die("Internal error: Can't detect map file")
				is_sokoban_map, error, puzzle_type, size = map_info
				if not size:
					die("Internal error: Can't detect map file size")
				level.map_size = size
		if level.map_size is None:
			level.map_size = DEFAULT_MAP_SIZE if self.MULTI_ROOMS else get_fitting_map_size()

	def apply_sizes(self):
		import_size_constants()

		if self.is_four_rooms:
			self.ROOM_X1 = ROOM_4_X1
			self.ROOM_X2 = ROOM_4_X2
			self.ROOM_Y1 = ROOM_4_Y1
			self.ROOM_Y2 = ROOM_4_Y2
			self.ROOM_BORDERS_X = ROOM_4_BORDERS_X
			self.ROOM_BORDERS_Y = ROOM_4_BORDERS_Y
		elif self.is_nine_rooms:
			self.ROOM_X1 = ROOM_9_X1
			self.ROOM_X2 = ROOM_9_X2
			self.ROOM_Y1 = ROOM_9_Y1
			self.ROOM_Y2 = ROOM_9_Y2
			self.ROOM_BORDERS_X = ROOM_9_BORDERS_X
			self.ROOM_BORDERS_Y = ROOM_9_BORDERS_Y
		else:
			self.ROOM_X1 = [PLAY_X1]
			self.ROOM_X2 = [PLAY_X2]
			self.ROOM_Y1 = [PLAY_Y1]
			self.ROOM_Y2 = [PLAY_Y2]
			self.ROOM_BORDERS_X = []
			self.ROOM_BORDERS_Y = []

flags = Flags()
