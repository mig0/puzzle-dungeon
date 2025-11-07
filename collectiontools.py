import os
import copy
from config import DATA_DIR
from common import die, warn, load_tabbed_yaml
from level import Collection, parse_level_id
from sokobanparser import parse_sokoban_levels

def _find_all_collections(dir_path, id, all_collections=None):
	if all_collections is None:
		all_collections = []

	config_path = dir_path + '/config'
	if os.path.isfile(config_path):
		config = load_tabbed_yaml(config_path)
		collection = Collection(id, config)
		collections = []
		sokoban_map_files_by_id = {}
		if sokoban_map_files_by_sub_id := config.get('sokoban-map-files'):
			del config['sokoban-map-files']
			if type(sokoban_map_files_by_sub_id) == tuple:
				sokoban_map_files_by_sub_id_tuple = sokoban_map_files_by_sub_id
				width = len(str(len(sokoban_map_files_by_sub_id_tuple)))
				sokoban_map_files_by_sub_id = {}
				for i, sokoban_map_file in enumerate(sokoban_map_files_by_sub_id_tuple):
					sub_id = "%0*d" % (width, i + 1)
					sokoban_map_files_by_sub_id[sub_id] = sokoban_map_file
			for sub_id, sokoban_map_file in sokoban_map_files_by_sub_id.items():
				c = copy.copy(collection)
				c.id += '/%s' % sub_id
				c.name += ' - %s' % sub_id
				collections.append(c)
				sokoban_map_files_by_id[c.id] = sokoban_map_file
		elif collection.level_configs is not None or config.get('sokoban-map-file'):
			collections.append(collection)
		for collection in collections:
			if sokoban_map_file := config.get('sokoban-map-file') or sokoban_map_files_by_id.get(collection.id):
				if 'sokoban-map-file' in config:
					del config['sokoban-map-file']
				collection.level_configs = parse_sokoban_levels(sokoban_map_file)
			if collection.num_levels == 0:
				warn("Ignoring collection %s with no levels" % collection.id)
			else:
				all_collections.append(collection)
		if not collections:
			warn("Ignoring collection %s with no levels and no sokoban-map-files" % collection.id)

	with os.scandir(dir_path) as entries:
		for entry in entries:
			if entry.is_dir():
				entry_id = id + ('/' if id else '') + entry.name
				_find_all_collections(dir_path + '/' + entry.name, entry_id, all_collections)

	return all_collections

def _find_and_sort_all_collections():
	collections = _find_all_collections(DATA_DIR + '/levels', '')

	# assign unique integer 'n' with magic-n fill logic
	def sort_collection_by_magic_n(c):
		# None goes last; otherwise by magic_n numeric; tie-breaker by id
		return (c.magic_n or 1000, c.id)

	collections.sort(key=sort_collection_by_magic_n)

	used_n = set()
	next_n = 1

	for collection in collections:
		if collection.magic_n is not None and next_n < collection.magic_n:
			next_n = collection.magic_n
		while next_n in used_n:
			next_n += 1
		collection.n = next_n
		used_n.add(next_n)
		next_n += 1

	return sorted(collections, key=lambda c: c.n)

all_collections = _find_and_sort_all_collections()

def is_valid_level_id(level_id):
	for collection in all_collections:
		if collection.has_level_id(level_id):
			return True
	return False

def get_collection_by_id(collection_id):
	return next((c for c in all_collections if c.has_id(collection_id)), None)

def get_collection_level_config_by_id(level_id, assert_valid=False):
	collection_id, level_index = parse_level_id(level_id, assert_valid)
	if not collection_id:
		return (None, None, None)
	collection = get_collection_by_id(collection_id)
	if collection and 1 <= level_index <= collection.num_levels:
		return collection, level_index, collection.level_configs[level_index - 1]
	if assert_valid:
		if not collection:
			die("Unexisting collection for level_id %s" % level_id, True)
		die("Level is out of range in collection for level_id %s" % level_id, True)
	return (None, None, None)

def create_custom_collection(extra_custom_collection_config=None):
	custom_collection_config = {
		'icon': 'default/trap0',
		'name': 'Custom collection',
		'n': 0,
	}
	if extra_custom_collection_config:
		custom_collection_config |= extra_custom_collection_config
	return Collection("custom", custom_collection_config)

