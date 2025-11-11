import atexit
from common import warn
from debug import debug
from profiler import profiler
from load import fetch_letslogic_collections, fetch_letslogic_collection, detect_map_file
from sokobanparser import parse_sokoban_levels

# Process common options and args.
# Options: --debug, --run-profiler, --list-collections, --list-ll-collections, --reverse-barrel-mode
# Args (multiple): map-file, sokoban-map-file, coll-id, level-id, "letslogic:<coll-id>", "clipboard:", level-index
def process_cmdargs(cmdargs, extra_custom_collection_config=None):
	debug.configure(cmdargs.debug)

	if cmdargs.run_profiler:
		profiler.start()
		atexit.register(lambda: profiler.stop())

	if cmdargs.list_ll_collections:
		collections = fetch_letslogic_collections()
		max_id_len = max(len(c_id) for c_id in collections)
		for c_id, c in collections.items():
			print("%s - %s (%d)" % (c_id.ljust(max_id_len), c['title'], c['levels']))
		exit()

	from collectiontools import all_collections, is_valid_level_id, get_collection_by_id, get_collection_level_config_by_id, create_custom_collection

	if cmdargs.list_collections:
		numeric = cmdargs.use_numeric
		max_id_len = max(len(c.get_id(numeric)) for c in all_collections)
		for collection in all_collections:
			print("%s - %s levels (%d)" % (collection.get_id(numeric).ljust(max_id_len), collection.name, len(collection.level_configs)))
		exit()

	custom_collection = create_custom_collection(extra_custom_collection_config)
	custom_collection.config["reverse-barrel-mode"] = cmdargs.reverse_barrel_mode

	level_configs = []
	level_indexes = []
	for arg in cmdargs.args:
		if arg.isdigit():
			level_indexes.append(int(arg))
		elif is_valid_level_id(arg):
			collection, _, level_config = get_collection_level_config_by_id(arg)
			level_configs.append(collection.with_level_config_defaults(level_config))
		elif collection := get_collection_by_id(arg):
			for level_config in collection.level_configs:
				level_configs.append(collection.with_level_config_defaults(level_config))
		elif arg == "stdin:" or arg == "-":
			level_configs.extend(parse_stdin_levels(arg, custom_collection.config) or [])
		elif arg == "clipboard:":
			level_configs.extend(parse_clipboard_levels(arg, custom_collection.config) or [])
		elif arg.startswith("letslogic:"):
			if map_string := fetch_letslogic_collection(arg[10:]):
				level_configs.extend(parse_sokoban_levels(map_string, custom_collection.config))
		elif map_info := detect_map_file(arg):
			is_sokoban_map, error, puzzle_type, size = map_info
			if is_sokoban_map:
				level_configs.extend(parse_sokoban_levels(arg, custom_collection.config))
				continue
			if error:
				warn("Ignoring map-file %s: Not a sokoban map and %s" % (arg, error))
				continue
			level_configs.append({
				'puzzle-type': puzzle_type,
				'map-size': size,
				'map-file': arg,
				'name': "%s map %s" % (puzzle_type, arg),
			})
		else:
			warn("Ignoring unknown argument %s" % arg)

	if level_indexes:
		valid_level_idxs = []
		invalid_level_indexes = []
		for level_index in level_indexes:
			if 1 <= level_index <= len(level_configs):
				valid_level_idxs.append(level_index - 1)
			else:
				invalid_level_indexes.append(level_index)
		if invalid_level_indexes:
			warn("Requested level indexes %s are not in the given levels" % invalid_level_indexes)
		level_configs = [level_configs[idx] for idx in valid_level_idxs]

	return level_configs, custom_collection

def parse_map_string_levels(map_string, input_id_str, content_id_str, config={}):
	error_prefix = f"Ignoring '{input_id_str}', "
	if not map_string:
		warn(error_prefix + f"since {content_id_str} is empty")
		return None
	map_info = detect_map_file(None, map_string=map_string)
	if not map_info:
		warn(error_prefix + f"no map in {content_id_str}")
		return None
	is_sokoban_map, error, puzzle_type, size = map_info
	if is_sokoban_map:
		level_configs = parse_sokoban_levels(map_string, config)
		if not level_configs:
			warn(error_prefix + "no levels in sokoban map")
		return level_configs
	if error:
		warn(error_prefix + "Not a sokoban map and %s" % error)
		return None
	return [{
		'puzzle-type': puzzle_type,
		'map-size': size,
		'map-string': map_string,
		'name': f"%s map from {content_id_str}" % puzzle_type,
		'bg-image': config.get('bg-image'),
		'music': config.get('music'),
		'theme': config.get('theme'),
	}]

def parse_stdin_levels(input_id_str, config={}):
	from sys import stdin
	return parse_map_string_levels("".join(stdin.readlines()), input_id_str, 'stdin', config)

def parse_clipboard_levels(input_id_str, config={}):
	from clipboard import clipboard
	return parse_map_string_levels(clipboard.get(), input_id_str, 'clipboard', config)
