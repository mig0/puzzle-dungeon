import os
from common import warn
from config import DEFAULT_NUM_ENEMIES
from sizetools import DEFAULT_MAP_SIZE

class Level:
	def __init__(self):
		self.unset()

	def unset(self):
		self.collection = None
		self.index = None
		self.config = None

	def is_set(self):
		return self.index is not None

	def set_from_level(self, level):
		self.set_from_config(level.collection, level.index, level.config)

	def set_from_config(self, collection, index, config):
		self.collection = collection
		self.index = index
		self.config = config

		# reset all fields to defaults
		self.actors_always_revealed = False
		self.allow_barrel_pull = False
		self.bg_image = None
		self.bg_image_crop = False
		self.char_health = None
		self.char_power = None
		self.cloud_mode = False
		self.disable_win = False
		self.enemy_key_drop = False
		self.four_rooms = False
		self.goal = None
		self.has_border = True
		self.has_finish = False
		self.has_start = False
		self.map_file = None
		self.map_size = DEFAULT_MAP_SIZE
		self.music = "valiant_warriors"
		self.name = None
		self.nine_rooms = False
		self.num_enemies = DEFAULT_NUM_ENEMIES
		self.grid_maze = False
		self.random_maze = False
		self.spiral_maze = False
		self.stopless = False
		self.theme = "default"
		self.time_limit = None
		self.title = None
		self.use_clock = False
		self.map_string = None
		self.puzzle_type = collection.puzzle_type
		self.puzzle_config = {}

		# apply config fields
		for key, value in config.items():
			field = key.replace("-", "_")
			if hasattr(self, field):
				default = getattr(self, field)
				expected_type = type(default) if default is not None or value is None else \
					int if any(map(key.endswith, ("-power", "-limit", "-health"))) else str
				if expected_type != type(value):
					warn("Ignoring level config %s=%s in %s/config; expected type %s" %
						(key, str(value), collection.id, expected_type.__name__))
				else:
					setattr(self, field, value)
			else:
				warn("Ignoring unknown level config %s=%s in %s/config" %
					(key, str(value), collection.id), True)

	def get_id(self, numeric=False):
		return self.collection.get_id(numeric) + self.collection.get_padded_level_index_suffix(self.index)

	def has_id(self, id):
		collection_id, level_index = id.rsplit('.', 1)
		if int(level_index) != self.index:
			return False
		return self.collection.has_id(collection_id)

class Collection:
	def __init__(self, id, config):
		self.id = id
		self.config = config

		self.name = config.get('name', id)
		self.icon = config.get('icon', 'default/cloud')
		self.puzzle_type = config.get('puzzle-type', 'Puzzle')
		self.magic_n = config.get('magic-n', None)
		self.n = None

		self.level_configs = config.get('levels', None)

	@property
	def num_levels(self):
		return len(self.level_configs or [])

	def get_id(self, numeric=False):
		return str(self.n) if numeric else self.id

	def has_id(self, id):
		return self.n == int(id) if id.isnumeric() else self.id == id

	def has_level_id(self, level_id):
		collection_id, level_index = level_id.rsplit('.', 1)
		return self.has_id(collection_id) and 1 <= int(level_index) <= self.num_levels

	def get_padded_level_index_suffix(self, level_index):
		width = len(str(self.num_levels)) if self.level_configs else 1
		return ".%0*d" % (width, level_index)

	def get_level_id(self):
		return self.get_id() + self.get_padded_level_index_suffix(1)

