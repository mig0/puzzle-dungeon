from constants import *
from random import randint

CHAR_CELL_TYPES = {
	'#': CELL_WALL,
	'.': CELL_PLATE,
	'@': ACTOR_CHARS["char"],
	'+': ACTOR_ON_PLATE_CHARS["char"],
	'$': ACTOR_CHARS["barrel"],
	'*': ACTOR_ON_PLATE_CHARS["barrel"],
	' ': CELL_FLOOR,
}

CHAR_ALIASES = {
	'p': '@',
	'P': '+',
	'b': '$',
	'B': '*',
	'-': ' ',
	'_': ' ',
}

for ch, ch0 in CHAR_ALIASES.items():
	CHAR_CELL_TYPES[ch] = CHAR_CELL_TYPES[ch0]

CHAR_TRANSLATION = dict((ord(ch), (cell_type)) for ch, cell_type in CHAR_CELL_TYPES.items())

def is_map_line(line):
	is_all_floor = True
	for ch in line:
		if ch not in CHAR_CELL_TYPES.keys():
			return False
		if CHAR_CELL_TYPES[ch] != CELL_FLOOR:
			is_all_floor = False
	return not is_all_floor

SOKOBAN_MAP_PREFIX = "maps/sokoban/"

def create_map_string(lines):
	min_size_x = 13
	min_size_y = 13

	# convert all lines to our map chars
	lines = [line.translate(CHAR_TRANSLATION) for line in lines]

	# calculate the actual size of lines in the given map
	real_size_y = len(lines)
	real_size_x = max(map(len, lines))

	# fill every line to be of length real_size_x
	for i, line in enumerate(lines):
		if len(line) < real_size_x:
			lines[i] = line + CELL_FLOOR * (real_size_x - len(line))

	# calculate intended size_x, size_y
	size_y = max(min_size_y, real_size_y)
	size_x = max(min_size_x, real_size_x)

	# fill missing rows, centered
	if real_size_y < size_y:
		num_rows_before = (size_y - real_size_y) // 2
		num_rows_after = size_y - real_size_y - num_rows_before
		floor_row = CELL_FLOOR * real_size_x
		lines = [floor_row] * num_rows_before + lines + [floor_row] * num_rows_after

	# fill missing columns, centered
	if real_size_x < size_x:
		for i, line in enumerate(lines):
			num_cols_before = (size_x - real_size_x) // 2
			num_cols_after = size_x - real_size_x - num_cols_before
			lines[i] = CELL_FLOOR * num_cols_before + lines[i] + CELL_FLOOR * num_cols_after

	sig_line = "# Dungeon Sokoban auto-generated map %dx%d" % (size_x, size_y)

	return (size_x, size_y), '\n'.join([sig_line] + lines) + '\n'

def parse_sokoban_levels(major, filename):
	levels = []

	full_filename = SOKOBAN_MAP_PREFIX + filename
	file = open(full_filename, "r", encoding="utf-8")
	if not file:
		print("Can't open file %s with sokoban levels" % full_filename)
		return levels

	is_in_map = False
	map_lines = None
	level_name = None
	is_pre_level_name = False
	pre_level_name = None
	i = 0
	while True:
		line = file.readline()
		is_eof = line == ''

		line = line.rstrip("\n")

		old_is_in_map = is_in_map
		is_in_map = is_map_line(line)

		if is_eof or map_lines and not old_is_in_map and is_in_map:
			map_size, map_string = create_map_string(map_lines)
			i += 1
			levels.append({
				"n": major + i / 1000,
				"name": level_name or "No Name",
				"bg_image": "bg/starry-sky.webp",
				"theme": ("stoneage1", "stoneage2", "stoneage3", "stoneage4", "stoneage5", "default", "modern1", "moss")[randint(0, 7)],
				"music": ("playful_sparrow", "film", "forest_walk", "epic_cinematic_trailer", "adventures")[randint(0, 4)] + ".mp3",
				"map_size": map_size,
				"map_string": map_string,
				"void_outer_floor": True,
				"num_enemies": 0,
				"char_health": None,
				"barrel_puzzle": {},
			})

		if is_eof:
			break

		if is_in_map:
			if not old_is_in_map:
				map_lines = []
				level_name = pre_level_name
				is_pre_level_name = False
				pre_level_name = None
			map_lines.append(line)
		else:
			if is_pre_level_name:
				if line.startswith("'") and line.endswith("'"):
					pre_level_name = pre_level_name + ": " + line[1:-1]
				continue
			if line.startswith('Level ') and line[6:].isdigit():
				is_pre_level_name = True
				pre_level_name = line
			if map_lines and line.startswith('Title: '):
				level_name = line[7:]

	file.close()

	return levels
