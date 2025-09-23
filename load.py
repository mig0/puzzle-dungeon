import io
from constants import *

def parse_map_file_signature(file):
	words = file.readline().split(" ")
	if len(words) <= 1:
		return "Invalid signature line, no expected space", None, None, None
	if words[0] != '#' or words[1] != 'Dungeon':
		return "Invalid signature line, no expected '# Dungeon'", None, None, None
	if len(words) <= 4:
		return "Invalid signature line, no expected puzzle-type and size", None, None, None
	puzzle_type = words[2]
#	if not puzzle_type.endswith("Puzzle"):
#		return "Invalid signature line, invalid puzzle-type %s" % puzzle_type, None, None, None
	size_str = words[-1].rstrip("\n")
	sizes = size_str.split("x")
	if len(sizes) != 2 or not sizes[0].isdigit() or not sizes[1].isdigit():
		return "Invalid signature line, invalid size '%s'" % size_str, None, None, None
	size_x = int(sizes[0])
	size_y = int(sizes[1])
	return None, puzzle_type, size_x, size_y

def load_map(filename_or_stringio, special_cell_types={}):
	from game import game
	from sizetools import MAP_SIZE_X, MAP_SIZE_Y
	from objects import enemies, barrels, carts, lifts, mirrors, portal_destinations, drop_key1, drop_key2, create_cart, create_lift, create_enemy, create_barrel, create_mirror

	is_stringio = type(filename_or_stringio) == io.StringIO
	filename = "<from-string>" if is_stringio else filename_or_stringio

	orig_map = game.map.copy()

	def print_error(error):
		print("%sFile %s: %s\n%sIgnoring bad map file" % (ERROR_PREFIX, filename, error, CNTRL_PREFIX))
		if is_stringio:
			print(filename_or_stringio.getvalue())
		enemies.clear()
		barrels.clear()
		carts.clear()
		lifts.clear()
		mirrors.clear()
		portal_destinations.clear()
		game.set_char_cell(None, 0)
		game.map = orig_map.copy()

	if is_stringio:
		file = filename_or_stringio
		debug(4, "Loading map:\n" + str(filename_or_stringio.getvalue()))
	else:
		try:
			file = open(filename, "r", encoding="utf-8")
		except:
			print_error("Failed to open")
			return

	# parse first signature line
	error, puzzle_type, size_x, size_y = parse_map_file_signature(file)
	if error:
		print_error(error)
		return
	if size_x != MAP_SIZE_X or size_y != MAP_SIZE_Y:
		print_error("Invalid size %dx%d instead of %dx%d" % (size_x, size_y, MAP_SIZE_X, MAP_SIZE_Y))
		return

	game.set_char_cell(None, 0)

	# parse map lines
	line_n = 2
	special_cell_infos = []
	portal_cells = []
	for y in range(0, size_y):
		line = file.readline()
		if line == '':
			print_error("Failed to read map line #%d" % line_n)
			return
		line = line.rstrip("\n")
		for x in range(0, size_x):
			if len(line) <= x:
				print_error("Failed to read char #%d in map line #%d" % (x + 1, line_n))
				return
			ch = line[x]
			cell = (x, y)
			mirror_host = None
			if ch == CELL_START:
				game.set_char_cell(cell, 0)
			if ch in CART_MOVE_TYPES_BY_CHAR:
				cart = create_cart(cell, CART_MOVE_TYPES_BY_CHAR[ch])
				if ch in MIRROR_CHARS:
					mirror_host = cart
				ch = CELL_FLOOR
			if ch in LIFT_MOVE_TYPES_BY_CHAR:
				lift = create_lift(cell, LIFT_MOVE_TYPES_BY_CHAR[ch])
				if ch in MIRROR_CHARS:
					mirror_host = lift
				ch = CELL_VOID
			if ch in ACTOR_AND_PLATE_BY_CHAR:
				actor_name, is_plate = ACTOR_AND_PLATE_BY_CHAR[ch]
				ch = CELL_PLATE if is_plate else CELL_FLOOR
				if actor_name == "key1":
					drop_key1.instantiate(cell)
				if actor_name == "key2":
					drop_key2.instantiate(cell)
				if actor_name == "enemy":
					create_enemy(cell)
				if actor_name == "barrel":
					create_barrel(cell)
				if actor_name == "mirror":
					mirror_host = create_barrel(cell)
				if actor_name == "char":
					game.set_char_cell(cell, 0)
				if actor_name == "npc":
					special_cell_infos.append((cell, None))
			if ch == CELL_PORTAL:
				portal_cells.append(cell)
			if mirror_host:
				create_mirror(mirror_host)
			if value_type := special_cell_types.get(ch):
				special_cell_infos.append((cell, value_type))
			game.map[x, y] = ch
		line_n += 1

	def print_metadata_cell_line_error(name, cell, error):
		print_error(error + " for %s %s in map line #%d" % (name, str(cell), line_n))

	# parse portal cell metadata lines if any
	for cell in portal_cells:
		line = file.readline()
		def print_portal_error(error):
			print_metadata_cell_line_error("portal", cell, error)
		if line == '':
			print_portal_error("Failed to read line")
			return
		values = line.split()
		if not values:
			continue
		if len(values) > 2:
			print_portal_error("Must be up to 2 ints")
			return
		if len(values) == 1:
			if not values[0].isdigit() or not 0 <= int(values[0]) < len(portal_cells):
				print_portal_error("Invalid dest portal idx")
				return
			dest_cell = portal_cells[int(values[0])]
		else:
			if not values[0].isdigit() or not values[1].isdigit():
				print_portal_error("Dest cell is not 2 ints")
				return
			dest_cell = (int(values[0]), int(values[1]))
		if dest_cell == cell:
			print_portal_error("Dest cell can't be the same")
			return
		if not 0 <= dest_cell[0] < size_x or not 0 <= dest_cell[1] < size_y:
			print_portal_error("Dest cell is out of map")
			return
		portal_destinations[cell] = dest_cell
		line_n += 1

	# parse mirror cell metadata lines if any
	for mirror in mirrors:
		line = file.readline()
		def print_mirror_error(error):
			print_metadata_cell_line_error("mirror", mirror.c, error)
		if line == '':
			print_mirror_error("Failed to read line")
			return
		values = line.split()
		if not len(values) == 2:
			print_mirror_error("Invalid metadata %s, must have 2 fields" % values)
			return
		if not values[0]:
			print_mirror_error("Invalid empty orientation")
			return
		if not values[0][0] in MIRROR_ORIENTATION_CHARS:
			print_mirror_error("Invalid orientation (%s)" % values[0][0])
			return
		mirror.orientation = values[0][0]
		mirror.fixed_orientation = False if values[0][1:] == "*" else True
		if not values[1]:
			print_mirror_error("Invalid empty activeness")
			return
		if not values[1][0].isdigit():
			print_mirror_error("Invalid activeness (%s), must be integer" % values[1][0])
			return
		mirror.activeness = int(values[1][0])
		if not 0 <= mirror.activeness <= 3:
			print_mirror_error("Invalid activeness (%d), must be [0..3]" % mirror.activeness)
			return
		mirror.fixed_activeness = False if values[1][1:] == "*" else True
		line_n += 1

	# parse special cell metadata lines if any
	special_cell_values = {}
	for cell, value_type in special_cell_infos:
		def print_special_error(error):
			print_metadata_cell_line_error("special cell", cell, error)
		if value_type is None:
			special_cell_values[cell] = None
			continue
		line = file.readline()
		if line == '':
			print_special_error("Failed to read line")
			return
		value_str = line.rstrip("\n")
		def parse_int(value_str):
			return None if value_str == '-' else int(value_str)
		try:
			if value_type == 'str':
				value = value_str
			elif value_type == 'strs':
				value = value_str.split()
			elif value_type == 'int':
				value = parse_int(value_str)
			elif value_type == 'ints':
				value = tuple(map(parse_int, value_str.split()))
			else:
				raise ValueError("Unsupported value type %s" % value_type)
		except Exception as e:
			print_special_error("Error: \"%s\"" % e)
			return
		special_cell_values[cell] = value
		line_n += 1

	extra_values = []
	while True:
		line = file.readline()
		if line == '':
			break
		extra_values.append(line.rstrip("\n"))

	file.close()

	return (special_cell_values, extra_values)

