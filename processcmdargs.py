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
		elif arg == "clipboard:":
			level_configs.extend(parse_clipboard_levels("clipboard:", custom_collection.config) or [])
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
