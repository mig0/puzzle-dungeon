import os
from copy import deepcopy
from common import warn, die
from config import DEFAULT_NUM_ENEMIES
from sizetools import get_default_map_size
from cmdargs import cmdargs

special_config_keys = ('bg-image', 'cloud-mode', 'music', 'puzzle-type', 'theme')

class Level:
	def __init__(self):
		self.unset()

	def unset(self):
		self.collection = None
		self.index = None
		self.config = None

	def is_set(self):
		return self.collection is None or self.index is not None or self.config is None

	def set_from_level(self, level):
		self.set_from_config(level.collection, level.index, level.config)

	def set_from_config(self, collection, index, config):
		self.collection = collection
		self.index = index
		self.config = config

		# reset all fields to defaults
		self.actors_always_revealed = False
		self.bg_image = collection.config.get('bg-image') or None
		self.bg_image_crop = False
		self.char_health = None
		self.char_power = None
		self.cloud_mode = collection.config.get('cloud-mode') or False
		self.disable_win = False
		self.enemy_key_drop = False
		self.four_rooms = False
		self.goal = None
		self.has_border = True
		self.has_finish = False
		self.has_start = False
		self.map_file = None
		self.map_size = get_default_map_size()
		self.map_string = None
		self.music = collection.config.get('music') or "valiant_warriors"
		self.name = None
		self.nine_rooms = False
		self.num_enemies = DEFAULT_NUM_ENEMIES
		self.grid_maze = False
		self.random_maze = False
		self.spiral_maze = False
		self.puzzle_type = collection.config.get('puzzle-type') or 'Puzzle'
		self.puzzle_config = {}
		self.reverse_barrel_mode = collection.config.get('reverse-barrel-mode') or False
		self.stopless = False
		self.theme = collection.config.get('theme') or "default"
		self.time_limit = None
		self.title = None
		self.use_clock = False

		# apply config fields
		for key, value in config.items():
			if value is None and key in special_config_keys:
				continue
			field = key.replace("-", "_")
			if hasattr(self, field):
				default = getattr(self, field)
				expected_type = type(default) if default is not None or value is None else \
					int if any(map(key.endswith, ("-power", "-limit", "-health"))) else str
				if expected_type != type(value):
					warn("Ignoring config %s=%s in level %s; expected type %s" %
						(key, str(value), self.get_id(), expected_type.__name__))
				else:
					setattr(self, field, value)
			else:
				warn("Ignoring unknown config %s=%s in level %s" %
					(key, str(value), self.get_id()))

	def to_config(self):
		return {k.replace("_", "-"): v for k, v in vars(self).items() if k not in ('collection', 'index', 'config')}

	def get_id(self, numeric=False):
		if not self.is_set():
			return ''
		return self.collection.get_id(numeric) + self.collection.get_padded_level_index_suffix(self.index)

	def has_id(self, id):
		if not self.is_set():
			return id == ''
		collection_id, level_index = parse_level_id(id)
		if not collection_id or level_index != self.index:
			return False
		return self.collection.has_id(collection_id)

class Collection:
	def __init__(self, id, config):
		self.id = id
		self.config = config

		self.name = config.get('name', id)
		self.icon = config.get('icon', 'default/cloud')
		self.magic_n = config.get('magic-n', None)
		self.n = config.get('n')

		self.level_configs = config.get('levels', None)

	@property
	def num_levels(self):
		return len(self.level_configs or [])

	def get_id(self, numeric=False):
		return str(self.n) if numeric else self.id

	def has_id(self, id):
		return self.n == int(id) if id.isnumeric() else self.id == id

	def has_level_id(self, level_id):
		collection_id, level_index = parse_level_id(level_id)
		return collection_id and self.has_id(collection_id) and 1 <= int(level_index) <= self.num_levels

	def get_padded_level_index_suffix(self, level_index):
		width = len(str(self.num_levels)) if self.level_configs else 1
		return ".%0*d" % (width, level_index)

	def get_level_id(self):
		return self.get_id() + self.get_padded_level_index_suffix(1)

	def with_level_config_defaults(self, level_config):
		level_config = deepcopy(level_config)
		for key in ('bg-image', 'cloud-mode', 'music', 'puzzle-type', 'reverse-barrel-mode', 'theme'):
			if level_config.get(key) is None and self.config.get(key) is not None:
				level_config[key] = self.config[key]
		return level_config

def parse_level_id(level_id, assert_valid=False):
	parts = level_id.rsplit('.', 1)
	if len(parts) != 2 or not parts[1].isnumeric():
		collection_id, level_index = None, 0
	else:
		collection_id, level_index = parts[0], int(parts[1])
	if assert_valid and not collection_id:
		die("Can't parse level id %s" % level_id, True)
	return collection_id, level_index
