import os
import io
import sys
import random
import pygame
import pgzero
import builtins
from pgzero.constants import keys
from numpy import ndarray
from copy import deepcopy
from random import randint, choice, shuffle
from unicodedata import bidirectional
from constants import *
from teestream import *
from leveltools import *
from sizetools import *
from cellactor import *
from objects import *
from common import *
from debug import *
from image import *
from theme import *
from draw import *
from room import *
from game import game
from drop import draw_status_drops
from flags import flags
from puzzle import create_puzzle, Puzzle
from solution import solution, set_solution_funcs
from joystick import scan_joysticks_and_state, emulate_joysticks_press_key, get_joysticks_arrow_keys
from clipboard import clipboard
from translate import _, set_lang
from mainscreen import main_screen_level_config, create_main_screen
from statusmessage import reset_status_messages, set_status_message, draw_status_message

# set data dir and default encoding for the whole program
pgzero.loaders.set_root(DATA_DIR)
sys.stdout.reconfigure(encoding='utf-8')

def load_map(filename_or_stringio, special_cell_types={}):
	global map

	is_stringio = type(filename_or_stringio) == io.StringIO
	filename = "<from-string>" if is_stringio else filename_or_stringio

	orig_map = map.copy()

	def print_error(error):
		global map
		print("%sFile %s: %s\n%sIgnoring bad map file" % (ERROR_PREFIX, filename, error, CNTRL_PREFIX))
		if is_stringio:
			print(filename_or_stringio.getvalue())
		enemies.clear()
		barrels.clear()
		carts.clear()
		lifts.clear()
		mirrors.clear()
		portal_destinations.clear()
		set_char_cell(None, 0)
		map = orig_map.copy()

	if is_stringio:
		file = filename_or_stringio
		if DEBUG_LEVEL >= 2:
			print(filename_or_stringio.getvalue())
	else:
		try:
			file = open(filename, "r", encoding="utf-8")
		except:
			print_error("Failed to open")
			return

	# parse first signature line
	words = file.readline().split(" ")
	if len(words) <= 1:
		print_error("Invalid signature line, no expected space")
		return
	if words[0] != '#' or words[1] != 'Dungeon':
		print_error("Invalid signature line, no expected '# Dungeon'")
		return
	size_str = words[-1].rstrip("\n")
	sizes = size_str.split("x")
	if len(sizes) != 2 or not sizes[0].isdigit() or not sizes[1].isdigit():
		print_error("Invalid signature line, invalid size '%s'" % size_str)
		return
	size_x = int(sizes[0])
	size_y = int(sizes[1])
	if size_x != MAP_SIZE_X or size_y != MAP_SIZE_Y:
		print_error("Invalid size %dx%d instead of %dx%d" % (size_x, size_y, MAP_SIZE_X, MAP_SIZE_Y))
		return

	set_char_cell(None, 0)

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
				set_char_cell(cell, 0)
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
					set_char_cell(cell, 0)
				if actor_name == "npc":
					special_cell_infos.append((cell, None))
			if ch == CELL_PORTAL:
				portal_cells.append(cell)
			if mirror_host:
				create_mirror(mirror_host)
			if value_type := special_cell_types.get(ch):
				special_cell_infos.append((cell, value_type))
			map[x, y] = ch
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
				value = tuple(builtins.map(parse_int, value_str.split()))
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

# get 4 neughbour cells for cell
def get_cell_neighbors(cell, x_range=None, y_range=None):
	neighbors = []
	for diff in ((-1, 0), (+1, 0), (0, -1), (0, +1)):
		neigh = apply_diff(cell, diff)
		if x_range is None or y_range is None or is_cell_in_area(neigh, x_range, y_range):
			neighbors.append(neigh)
	debug(3, "* get_cell_neighbors %s - %s" % (str(cell), neighbors))
	return neighbors

# get 4 neughbour cells for actor
def get_actor_neighbors(actor, x_range=None, y_range=None):
	return get_cell_neighbors(actor.c, x_range, y_range)

# get 8 or 9 neughbour cells for cell
def get_all_neighbors(cell, include_self=False):
	neighbors = []
	for dy in (-1, 0, +1):
		for dx in (-1, 0, +1):
			if dy == 0 and dx == 0 and not include_self:
				continue
			neighbors.append(apply_diff(cell, (dx, dy)))
	return neighbors

is_game_won = False
is_music_enabled = True
is_music_started = False
is_sound_enabled = True
is_move_animate_enabled = True
is_level_intro_enabled = True

music_orig_volume = None
music_start_time  = None
music_fadein_time = None

mode = "start"

puzzle = None

bg_image = None

game_time = 0
level_time = 0
idle_time = 0

last_regeneration_time = 0

last_time_arrow_keys_processed = None
last_processed_arrow_keys = []
pressed_arrow_keys = []

level_title = None
level_name = None
level_goal = None

map = None  # will be generated
cell_images = {}  # will be generated
revealed_map = None

switch_cell_infos = {}  # tuple(old_cell_type, new_cell_type, end_time, duration) per cell
portal_demolition_infos = {}  # tuple(new_cell_type, start_time) per cell

def get_drop_on_cell(cell):
	for drop in drops:
		if drop.has_instance(cell):
			return drop
	return None

killed_enemies = []

level_title_time = 0
level_goal_time = 0

level = None

enter_room_idx = None

def get_bg_image():
	return bg_image

def debug_map(level=0, descr=None, full_format=False, full=True, clean=True, combined=True, dual=False, endl=False, char_cell=None, cell_chars={}):
	if DEBUG_LEVEL < level:
		return
	if descr:
		print(descr)
	if full_format:
		full = True
		combined = True
		dual = False
		portal_cells = []
		print("# Dungeon %s anonymous map %dx%d" % (puzzle.__class__.__name__ if puzzle else "non-puzzle", MAP_SIZE_X, MAP_SIZE_Y))
	for cy in MAP_Y_RANGE if full else PLAY_Y_RANGE:
		if not combined:
			for cx in MAP_X_RANGE if full else PLAY_X_RANGE:
				cell = (cx, cy)
				print(CELL_FLOOR if clean and map[cell] in CELL_FLOOR_TYPES else map[cell], end="")
		if dual:
			print("    ", end="")
		if dual or combined:
			for cx in MAP_X_RANGE if full else PLAY_X_RANGE:
				cell = (cx, cy)
				cell_ch = CELL_FLOOR if clean and map[cell] in CELL_FLOOR_TYPES else map[cell]
				actor_chars = ACTOR_ON_PLATE_CHARS if cell_ch == CELL_PLATE else ACTOR_CHARS
				if cell in cell_chars:
					cell_ch = cell_chars[cell]
				if drop := get_drop_on_cell(cell):
					cell_ch = actor_chars[drop.name]
				if is_cell_in_actors(cell, enemies):
					cell_ch = actor_chars['enemy']
				if barrel := get_actor_on_cell(cell, barrels):
					cell_ch = actor_chars['mirror' if barrel.mirror else 'barrel']
				if cart := get_actor_on_cell(cell, carts):
					cell_ch = CART_CHARS[1 if cart.mirror else 0][cart.type]
				if lift := get_actor_on_cell(cell, lifts):
					cell_ch = LIFT_CHARS[1 if lift.mirror else 0][lift.type]
				if cell == char_cell or char.c is not None and char.c == cell:
					cell_ch = actor_chars['char']
				print(cell_ch, end="")
				if full_format and cell_ch == CELL_PORTAL:
					portal_cells.append(cell)
		print()
	if full_format:
		for cell in portal_cells:
			if dest_cell := portal_destinations.get(cell):
				print(portal_cells.index(dest_cell) if dest_cell in portal_cells else ' '.join(builtins.map(str, portal_destinations[cell])))
			else:
				print("")
		for extra_value in puzzle.get_map_extra_values() if puzzle else ():
			line = ' '.join(builtins.map(str, extra_value)) if hasattr(extra_value, '__iter__') else str(extra_value)
			print(line)
	if endl:
		print()

def is_cell_in_map(cell):
	return is_cell_in_area(cell, MAP_X_RANGE, MAP_Y_RANGE)

def is_outer_wall(cell):
	if map[cell] not in CELL_WALL_TYPES:
		return False

	for neigh in get_all_neighbors(cell):
		if is_cell_in_map(neigh) and map[neigh] not in CELL_WALL_TYPES:
			return False
	return True

def replace_outer_walls(*cell_types):
	for cy in MAP_Y_RANGE:
		for cx in MAP_X_RANGE:
			if map[cx, cy] == CELL_OUTER_WALL:
				map[cx, cy] = choice(cell_types)

def convert_outer_walls(cell_type=None):
	for cy in MAP_Y_RANGE:
		for cx in MAP_X_RANGE:
			if is_outer_wall((cx, cy)):
				map[cx, cy] = CELL_OUTER_WALL

	if cell_type is not None:
		replace_outer_walls(*cell_type)

def convert_outer_floors(cell_type=None):
	floor_cells_to_convert = set()
	for cy in (0, MAP_SIZE_Y - 1):
		for cx in (0, MAP_SIZE_X - 1):
			if map[cx, cy] in CELL_FLOOR_TYPES:
				floor_cells_to_convert.update(get_accessible_cells((cx, cy)))
	for cell in floor_cells_to_convert:
		map[cell] = CELL_OUTER_WALL

	if cell_type is not None:
		replace_outer_walls(cell_type)

def is_portal_destination(cell):
	return cell in {v: k for k, v in portal_destinations.items()}

def is_cell_occupied_except_char(cell, include_phased=False):
	if is_cell_in_actors(cell, enemies + barrels, include_phased=include_phased):
		return True

	return get_drop_on_cell(cell) is not None

def is_cell_occupied(cell, include_phased=False):
	return is_cell_occupied_except_char(cell, include_phased) or char.c == cell

# used for positioning enemies during level generation
def is_cell_occupied_for_enemy(cell):
	return map[cell] in CELL_ENEMY_PLACE_OBSTACLES or is_cell_occupied(cell, True) or is_portal_destination(cell)

def reveal_map_near_char():
	if not flags.is_cloud_mode:
		return

	for cell in get_all_neighbors(char.c, include_self=True):
		revealed_map[cell] = True

def get_revealed_actors(actors):
	if not flags.is_cloud_mode or level.get("actors_always_revealed", False):
		return actors

	revealed_actors = []
	for actor in actors:
		if revealed_map[actor.c]:
			revealed_actors.append(actor)
	return revealed_actors

def set_char_flip(is_right_dir=True):
	char.flip = None if is_right_dir else (True, False)

def propagate_map():
	set_map(map)  # this is objects.set_map
	puzzle.set_map(map)

def set_room_and_notify_puzzle(idx):
	set_room(idx)
	puzzle.on_set_room()

# only to be used by puzzle's restore_level
def advance_room():
	if room.idx + 1 >= flags.NUM_ROOMS:
		return False
	set_room_and_notify_puzzle(room.idx + 1)
	return True

def enter_room(idx):
	global mode, char_cells, last_time_arrow_keys_processed

	set_room_and_notify_puzzle(idx)
	reset_status_messages()

	char.reset_animation()
	char.reset_inplace_animation()

	last_time_arrow_keys_processed = None

	place_char_in_room()
	char_cells[idx] = char.c  # needed for Alt-R

	reveal_map_near_char()

	if map[char.c] == CELL_START:
		char.activate_inplace_animation(level_time, CHAR_APPEARANCE_SCALE_DURATION, scale=(0, 1), angle=(180, 720))

	cursor.reset()

	mode = "game"

	game.start_level(map)

	puzzle.on_enter_room()

	char.phased = puzzle.is_char_phased()
	set_char_flip((char.cx - room.x1) * 2 < room.size_x)

accessible_obstacles = None

def start_accessible_obstacles():
	global accessible_obstacles
	accessible_obstacles = set()

def clear_accessible_obstacles():
	global accessible_obstacles
	accessible_obstacles0 = accessible_obstacles
	accessible_obstacles = None
	return accessible_obstacles0

def is_cell_accessible(cell, obstacles=None, place=False, allow_obstacles=False, allow_enemy=False):
	is_cell_blocked = map[cell] in (() if allow_obstacles else CELL_CHAR_PLACE_OBSTACLES if place else CELL_CHAR_MOVE_OBSTACLES)
	if obstacles is not None:
		if accessible_obstacles is not None and cell in obstacles:
			accessible_obstacles.add(cell)
		return False if is_cell_blocked or cell in obstacles else True
	if is_cell_blocked:
		return False
	return not is_cell_in_actors(cell, barrels if allow_enemy else barrels + enemies)

def get_accessible_neighbors(cell, obstacles=None, allow_obstacles=False, allow_enemy=False, allow_closed_gate=False, allow_stay=False):
	neighbors = []
	if ALLOW_DIAGONAL_MOVES and False:
		directions = ((-1, -1), (0, -1), (+1, -1), (-1, 0), (+1, 0), (-1, +1), (0, +1), (+1, +1))
	else:
		directions = ((-1, 0), (+1, 0), (0, -1), (0, +1))
	for diff in directions + ((0, 0),) if allow_stay else directions:
		neigh = apply_diff(cell, diff)
		if is_cell_in_room(neigh) and (
			allow_closed_gate and map[neigh] == CELL_GATE0 or
			is_cell_accessible(neigh, obstacles, allow_obstacles=allow_obstacles, allow_enemy=allow_enemy)
		):
			neighbors.append(neigh)
	debug(3, "* get_accessible_neighbors %s - %s" % (str(cell), neighbors))
	return neighbors

def get_accessible_cells(start_cell, obstacles=None):
	accessible_cells = []
	unprocessed_cells = [start_cell]
	while unprocessed_cells:
		cell = unprocessed_cells.pop(0)
		accessible_cells.append(cell)
		neigbours = get_accessible_neighbors(cell, obstacles)
		for n in neigbours:
			if n not in accessible_cells and n not in unprocessed_cells:
				unprocessed_cells.append(n)
	return accessible_cells

def get_accessible_cell_distances(start_cell, obstacles=None, allow_obstacles=False, allow_enemy=False):
	accessible_cells = []
	accessible_cell_distances = {start_cell: 0}
	unprocessed_cells = [start_cell]
	while unprocessed_cells:
		cell = unprocessed_cells.pop(0)
		accessible_distance = accessible_cell_distances[cell]
		accessible_cells.append(cell)
		neigbours = get_accessible_neighbors(cell, obstacles, allow_obstacles, allow_enemy)
		for n in neigbours:
			if n not in accessible_cells and n not in unprocessed_cells:
				unprocessed_cells.append(n)
				accessible_cell_distances[n] = accessible_distance + 1
	return accessible_cell_distances

def get_all_accessible_cells():
	return get_accessible_cells(char.c)

def get_num_accessible_target_directions(start_cell, target_cells):
	num_accessible_directions = 0

	for neigh in get_accessible_neighbors(start_cell, allow_closed_gate=True):
		unprocessed_cells = [ neigh ]
		accessible_cells = [ start_cell, neigh ]

		while unprocessed_cells:
			cell = unprocessed_cells.pop(0)
			if cell in target_cells:
				num_accessible_directions += 1
				break
			for new_neigh in get_accessible_neighbors(cell, allow_closed_gate=True):
				if new_neigh in accessible_cells:
					continue
				accessible_cells.append(new_neigh)
				unprocessed_cells.append(new_neigh)

	return num_accessible_directions

def find_path(start_cell, target_cell, obstacles=None, allow_obstacles=False, allow_enemy=False, randomize=True):
	if start_cell == target_cell:
		return []
	accessible_cell_distances = get_accessible_cell_distances(start_cell, obstacles, allow_obstacles, allow_enemy)
	accessible_distance = accessible_cell_distances.get(target_cell)
	if accessible_distance is None:
		return None
	path_cells = [target_cell]
	while accessible_distance > 1:
		accessible_distance -= 1
		neigh_cells = get_accessible_neighbors(path_cells[0], obstacles, allow_obstacles, allow_enemy)
		if randomize:
			shuffle(neigh_cells)
		for neigh_cell in neigh_cells:
			neigh_distance = accessible_cell_distances.get(neigh_cell)
			if neigh_distance == accessible_distance:
				path_cells.insert(0, neigh_cell)
				break
	return path_cells

# like find_path, but return all paths with the shortest distance from start to target
def find_all_paths(start_cell, target_cell, obstacles=None, allow_obstacles=False):
	if start_cell == target_cell:
		return [()]
	accessible_cell_distances = get_accessible_cell_distances(start_cell, obstacles, allow_obstacles)
	accessible_distance = accessible_cell_distances.get(target_cell)
	if accessible_distance is None:
		return None
	all_path_cells = [(target_cell,)]
	while accessible_distance > 1:
		accessible_distance -= 1
		new_all_path_cells = []
		for path_cells in all_path_cells:
			neigh_cells = [cell for cell in get_accessible_neighbors(path_cells[0], obstacles, allow_obstacles)
				if accessible_cell_distances.get(cell) == accessible_distance]
			for neigh_cell in neigh_cells:
				new_all_path_cells.append((neigh_cell, *path_cells))
		all_path_cells = new_all_path_cells
	return all_path_cells

def find_best_path(start_cell, target_cell, obstacles=None, allow_obstacles=False, randomize=True,
	cost_func=None, set_path_cost=None, allow_stay=False, state_func=None
):
	if start_cell == target_cell:
		return []

	def _pack_state(cell, old_cell, old_state):
		if state_func:
			state = state_func(cell, old_cell, old_state)
			return None if state is None else (cell, state)
		else:
			return cell

	def _unpack_state(cell_state):
		return cell_state if state_func else (cell_state, None)

	if not (start_cell_state := _pack_state(start_cell, None, None)):
		return None
	target_cell_state = None

	visited_cells = {start_cell_state: [None, 0]}  # cell_state: [parent, cost]
	processed_cells = []
	unprocessed_cells = [start_cell_state]

	while unprocessed_cells:
		cell_state = unprocessed_cells.pop(0)
		cell, state = _unpack_state(cell_state)
		processed_cells.append(cell_state)

		if cell == target_cell:
			target_cell_state = cell_state
			break

		neigbours = get_accessible_neighbors(cell, obstacles, allow_obstacles, allow_stay=allow_stay)
		if randomize:
			shuffle(neigbours)
		for neigh in neigbours:
			if not (neigh_state := _pack_state(neigh, cell, state)):
				continue

			if neigh_state in processed_cells:
				continue

			if cost_func:
				cost = cost_func(neigh, cell, visited_cells, start_cell, target_cell, obstacles)
			else:
				cost = 0
			if cost is None:
				continue

			cost += visited_cells[cell_state][1]
			if neigh_state not in visited_cells:
				visited_cells[neigh_state] = [cell_state, cost]
				unprocessed_cells.append(neigh_state)
				unprocessed_cells.sort(key=lambda cell: visited_cells[neigh_state][1] + cell_distance(neigh, target_cell))
			else:
				if visited_cells[neigh_state][1] < cost:
					visited_cells[neigh_state] = [cell_state, cost]

	if not target_cell_state:
		return None

	best_path_cells = []
	cell_state = target_cell_state
	while cell_state != start_cell_state:
		cell, _ = _unpack_state(cell_state)
		best_path_cells.insert(0, cell)
		if not cell_state in visited_cells:
			print("BUG:", cell_state, visited_cells)
		cell_state = visited_cells[cell_state][0]

	if set_path_cost is not None:
		set_path_cost[0] = visited_cells[target_cell_state][1]

	return best_path_cells

def is_path_found(start_cell, target_cell, obstacles=None):
	return target_cell in get_accessible_cells(start_cell, obstacles)

def set_char_cell(cell, room_idx=None):
	global char_cells

	char_cells[room.idx if room_idx is None else room_idx] = cell

def get_farthest_accessible_cell(start_cell):
	accessible_cell_distances = get_accessible_cell_distances(start_cell)
	return max(accessible_cell_distances, key=lambda cell: accessible_cell_distances[cell])

def get_closest_accessible_cell(start_cell, target_cell):
	accessible_cells = get_accessible_cells(start_cell)
	return min(accessible_cells, key=lambda cell: cell_distance(cell, target_cell))

def get_topleft_accessible_cell(start_cell):
	return get_closest_accessible_cell(start_cell, (0, 0))

def place_char_in_closest_accessible_cell(target_cell):
	char.c = get_closest_accessible_cell(char.c, target_cell)

def place_char_in_topleft_accessible_cell():
	char.c = get_topleft_accessible_cell(char.c)

def place_char_in_first_free_spot():
	for cell in room.cells:
		if is_cell_accessible(cell, place=True):
			char.c = cell
			return

	if lifts:
		char.c = get_actors_in_room(lifts)[0].c
		return

	print("Was not able to find free spot for char, fix the level or a bug")
	if DEBUG_LEVEL:
		char.c = (0, 0)
	else:
		quit()

def place_char_in_room():
	if char_cells[room.idx]:
		char.c = char_cells[room.idx]
	else:
		place_char_in_first_free_spot()

def get_random_floor_cell_type():
	return CELL_FLOOR_TYPES_FREQUENT[randint(0, len(CELL_FLOOR_TYPES_FREQUENT) - 1)]

def convert_to_floor_if_needed(cell):
	if not cell:
		warn("Called convert_to_floor_if_needed without cell, ignoring", True)
		return
	if map[cell] in (*CELL_WALL_TYPES, CELL_VOID, CELL_INTERNAL1):
		map[cell] = get_random_floor_cell_type()

def get_random_even_point(a1, a2):
	return a1 + randint(0, int((a2 - a1) / 2)) * 2

def generate_random_maze_area(x1, y1, x2, y2):
	if x2 - x1 <= 1 or y2 - y1 <= 1:
		return

	# select random point that will divide the area into 4 sub-areas
	random_x = get_random_even_point(x1 + 1, x2 - 1)
	random_y = get_random_even_point(y1 + 1, y2 - 1)

	# create the horizontal and vertical wall via this point
	for x in range(x1, x2 + 1):
		map[x, random_y] = CELL_WALL
	for y in range(y1, y2 + 1):
		map[random_x, y] = CELL_WALL

	# select 3 random holes on the 4 just created wall walls
	skipped_wall = randint(0, 3)
	if skipped_wall != 0: map[get_random_even_point(x1, random_x - 1), random_y] = get_random_floor_cell_type()
	if skipped_wall != 1: map[random_x, get_random_even_point(y1, random_y - 1)] = get_random_floor_cell_type()
	if skipped_wall != 2: map[get_random_even_point(random_x + 1, x2), random_y] = get_random_floor_cell_type()
	if skipped_wall != 3: map[random_x, get_random_even_point(random_y + 1, y2)] = get_random_floor_cell_type()

	# recurse into 4 sub-areas
	generate_random_maze_area(x1, y1, random_x - 1, random_y - 1)
	generate_random_maze_area(random_x + 1, y1, x2, random_y - 1)
	generate_random_maze_area(x1, random_y + 1, random_x - 1, y2)
	generate_random_maze_area(random_x + 1, random_y + 1, x2, y2)

def generate_grid_maze():
	for cy in room.y_range:
		for cx in room.x_range:
			if (cx - room.x1 - 1) % 2 == 0 and (cy - room.y1 - 1) % 2 == 0:
				map[cx, cy] = CELL_WALL

def generate_spiral_maze():
	if randint(0, 1) == 0:
		pointer = (room.x1 - 1, room.y1 + 1)
		steps = ((1, 0), (0, 1), (-1, 0), (0, -1))
		len = [room.x2 - room.x1, room.y2 - room.y1]
	else:
		pointer = (room.x1 + 1, room.y1 - 1)
		steps = ((0, 1), (1, 0), (0, -1), (-1, 0))
		len = [room.y2 - room.y1, room.x2 - room.x1]

	dir = 0

	while len[dir % 2] > 0:
		step = steps[dir]
		for i in range(len[dir % 2]):
			pointer = apply_diff(pointer, step)
			map[pointer] = CELL_WALL

		if dir % 2 == 0:
			len[0] -= 2
			len[1] -= 2
		dir = (dir + 1) % 4

def generate_random_maze_room():
	generate_random_maze_area(room.x1, room.y1, room.x2, room.y2)

def generate_random_free_path(start_cell, target_cell, area=None, deviation=0, level=0):
	global map

	if randint(0, deviation) == 0:
		start_cell = get_closest_accessible_cell(start_cell, target_cell)

	if start_cell == target_cell:
		return True

	if area == None:
		area = room

	debug_path_str = "free path from %s to %s" % (str(start_cell), str(target_cell))
	debug(2, "* [%d] generating %s" % (level, debug_path_str))

	max_distance = get_max_area_distance(area)

	accessible_cells = get_accessible_cells(start_cell)
	weighted_neighbors = []
	for cell in get_cell_neighbors(start_cell, area.x_range, area.y_range):
		if cell in accessible_cells:
			continue
		if is_cell_in_actors(cell, barrels):
			continue
		weight = randint(0, max_distance)
		weight -= cell_distance(cell, target_cell)
		if map[cell] in CELL_FLOOR_TYPES:
			weight -= randint(0, max_distance)
		weighted_neighbors.append((weight, cell))

	neighbors = [n[1] for n in sorted(weighted_neighbors, reverse=True)]

	if not neighbors:
		debug(2, "* [%d] failed to generate %s" % (level, debug_path_str))
		return False

	for neigh in neighbors:
		old_cell_type = map[neigh]
		if old_cell_type not in (*CELL_WALL_TYPES, CELL_VOID):
			print("BUG!")
			return False
		convert_to_floor_if_needed(neigh)
		debug(3, "* [%d] trying to move to %s" % (level, str(neigh)))
		debug_map(3)
		is_generated = generate_random_free_path(neigh, target_cell, area, deviation, level + 1)
		if is_generated:
			debug(2, "* [%d] successfully generated %s" % (level, debug_path_str))
			if level == 0:
				debug_map(2)
			return True
		map[neigh] = old_cell_type

	return False

def get_random_floor_cell():
	while True:
		cell = randint(room.x1, room.x2), randint(room.y1, room.y2)
		if map[cell] in CELL_FLOOR_TYPES:
			return cell

def replace_random_floor_cell(cell_type, num=1, callback=None, extra=None, extra_num=None):
	for n in range(num):
		cell = get_random_floor_cell()
		map[cell] = cell_type
		extra_cells = []
		if extra_num:
			for i in range(extra_num):
				extra_cell = get_random_floor_cell()
				map[extra_cell] = cell_type
				extra_cells.append(extra_cell)
		if callback:
			if extra is not None:
				callback(cell, extra, *extra_cells)
			else:
				callback(cell, *extra_cells)

def switch_cell_type(cell, new_cell_type, duration):
	game.remember_map_cell(cell)
	switch_cell_infos[cell] = (map[cell], new_cell_type, level_time + duration, duration)
	map[cell] = new_cell_type

def demolish_portal(cell, new_cell_type=CELL_FLOOR):
	portal_demolition_infos[cell] = (new_cell_type, level_time + PORTAL_DEMOLITION_DELAY)

def toggle_gate(gate_cell):
	cell_type = map[gate_cell]
	gate_cell_types = (CELL_TRAP1, CELL_TRAP0) if cell_type in (CELL_TRAP0, CELL_TRAP1) else (CELL_GATE0, CELL_GATE1)
	if cell_type not in gate_cell_types:
		die("Called toggle_gate not on CELL_GATE or CELL_TRAP")
	if cell_type == gate_cell_types[1]:
		sound_name = 'close.wav'
		new_cell_type = gate_cell_types[0]
	else:
		sound_name = 'open.wav'
		new_cell_type = gate_cell_types[1]

	switch_cell_type(gate_cell, new_cell_type, GATE_SWITCH_DURATION)
	play_sound(sound_name)

def toggle_actor_phased(actor):
	is_phased = not actor.phased
	if is_phased:
		sound_name = 'switch-on.wav'
		opacity = [1, ACTOR_PHASED_OPACITY]
	else:
		sound_name = 'switch-off.wav'
		opacity = [ACTOR_PHASED_OPACITY, 1]

	game.remember_obj_state(actor)
	actor.phased = is_phased
	actor.activate_inplace_animation(level_time, ACTOR_PHASED_DURATION, opacity=opacity, tween="decelerate", on_finished=lambda: actor.reset_opacity())
	play_sound(sound_name)

class Globals:
	is_cell_in_area = is_cell_in_area
	get_actor_neighbors = get_actor_neighbors
	get_all_neighbors = get_all_neighbors
	get_bg_image = get_bg_image
	debug_map = debug_map
	is_cell_in_map = is_cell_in_map
	convert_outer_walls = convert_outer_walls
	convert_outer_floors = convert_outer_floors
	is_cell_occupied = is_cell_occupied
	advance_room = advance_room
	start_accessible_obstacles = start_accessible_obstacles
	clear_accessible_obstacles = clear_accessible_obstacles
	is_cell_accessible = is_cell_accessible
	get_accessible_neighbors = get_accessible_neighbors
	get_accessible_cells = get_accessible_cells
	get_accessible_cell_distances = get_accessible_cell_distances
	get_all_accessible_cells = get_all_accessible_cells
	get_num_accessible_target_directions = get_num_accessible_target_directions
	find_path = find_path
	find_all_paths = find_all_paths
	find_best_path = find_best_path
	is_path_found = is_path_found
	set_char_cell = set_char_cell
	get_farthest_accessible_cell = get_farthest_accessible_cell
	get_closest_accessible_cell = get_closest_accessible_cell
	place_char_in_topleft_accessible_cell = place_char_in_topleft_accessible_cell
	get_random_floor_cell_type = get_random_floor_cell_type
	convert_to_floor_if_needed = convert_to_floor_if_needed
	generate_random_free_path = generate_random_free_path
	get_random_floor_cell = get_random_floor_cell
	replace_random_floor_cell = replace_random_floor_cell
	switch_cell_type = switch_cell_type
	demolish_portal = demolish_portal
	toggle_gate = toggle_gate
	toggle_actor_phased = toggle_actor_phased

def generate_room(idx):
	set_room_and_notify_puzzle(idx)

	if flags.is_random_maze:
		generate_random_maze_room()

	if flags.is_spiral_maze:
		generate_spiral_maze()

	if flags.is_grid_maze:
		generate_grid_maze()

	accessible_cells = None
	finish_cell = None
	if flags.has_finish or puzzle.is_finish_cell_required():
		char.c = (room.x1, room.y1)
		set_char_cell(char.c)
		if flags.has_start:
			map[char.c] = CELL_START
		accessible_cells = get_all_accessible_cells()
		accessible_cells.pop(0)  # remove char cell
		if not accessible_cells:
			debug_map()
			die("Requested to generate finish cell with no accessible cells")
		finish_cell = accessible_cells.pop()
		map[finish_cell] = CELL_FINISH
		puzzle.set_finish_cell(accessible_cells, finish_cell)

	puzzle.generate_room()

	# generate enemies
	if char.power:
		return
	for i in range(level["num_enemies"] if "num_enemies" in level else DEFAULT_NUM_ENEMIES):
		place_char_in_room()
		num_tries = 10000
		while num_tries > 0:
			cx = randint(room.x1, room.x2)
			cy = randint(room.y1, room.y2)
			if not is_cell_occupied_for_enemy((cx, cy)):
				break
			num_tries -= 1
		if num_tries == 0:
			print("Was not able to find free spot for enemy in 10000 tries, positioning it anyway on an obstacle")
		create_enemy((cx, cy))

def generate_map():
	global map

	map = ndarray((MAP_SIZE_X, MAP_SIZE_Y), dtype='U5')
	bw = 0 if flags.MULTI_ROOMS and not puzzle.has_border() else 1
	for cy in MAP_Y_RANGE:
		for cx in MAP_X_RANGE:
			if cx == PLAY_X1 - bw or cx == PLAY_X2 + bw or cy == PLAY_Y1 - bw or cy == PLAY_Y2 + bw:
				cell_type = CELL_WALL
			else:
				if cx in flags.ROOM_BORDERS_X or cy in flags.ROOM_BORDERS_Y:
					cell_type = CELL_WALL
				else:
					cell_type = get_random_floor_cell_type()
			map[cx, cy] = cell_type

	if "map_file" in level or "map_string" in level:
		filename_or_stringio = MAPS_DIR_PREFIX + level["map_file"] if "map_file" in level else io.StringIO(level["map_string"])
		if ret := load_map(filename_or_stringio, puzzle.load_map_special_cell_types):
			if flags.MULTI_ROOMS:
				print("Ignoring multi-room level config when loading map")
			propagate_map()
			set_room_and_notify_puzzle(0)
			puzzle.on_load_map(*ret)
			return

	propagate_map()

	for idx in range(flags.NUM_ROOMS):
		generate_room(idx)

	puzzle.on_generate_map()

def set_theme(theme_name):
	global cell_images, status_image, cloud_image

	set_theme_name(theme_name)
	image1 = create_theme_image('wall')
	image2 = create_theme_image('floor')
	image3 = create_theme_image('crack')
	image4 = create_theme_image('bones')
	image5 = create_theme_image('rocks')
	image6 = create_theme_image('plate')  if puzzle.has_plate() else None
	image7 = create_theme_image('start')  if flags.has_start or puzzle.has_start() else None
	image8 = create_theme_image('finish') if flags.has_finish or puzzle.has_finish() else None
	image9 = create_theme_image('portal') if puzzle.has_portal() else None
	image10 = create_theme_image('gate0') if puzzle.has_gate() else None
	image11 = create_theme_image('gate1') if puzzle.has_gate() else None
	image12 = create_theme_image('sand')  if puzzle.has_sand() else None
	image13 = create_theme_image('lock1') if puzzle.has_locks() else None
	image14 = create_theme_image('lock2') if puzzle.has_locks() else None
	image15 = create_theme_image('odirl') if puzzle.has_odirs() else None
	image16 = create_theme_image('odirr') if puzzle.has_odirs() else None
	image17 = create_theme_image('odiru') if puzzle.has_odirs() else None
	image18 = create_theme_image('odird') if puzzle.has_odirs() else None
	image19 = create_theme_image('glass') if puzzle.has_glass() else None
	image20 = create_theme_image('trap0') if puzzle.has_trap() else None
	image21 = create_theme_image('trap1') if puzzle.has_trap() else None
	image22 = create_theme_image('beamgn') if puzzle.has_beam() else None
	image23 = create_theme_image('beamcl') if puzzle.has_beam() else None
	status_image = create_theme_image('status')
	cloud_image = create_theme_image('cloud') if flags.is_cloud_mode and not bg_image else None

	outer_wall_image = load_theme_cell_image('wall')
	outer_wall_image.fill((50, 50, 50), special_flags=pygame.BLEND_RGB_SUB)

	cell_images = {
		CELL_WALL:   image1,
		CELL_FLOOR:  image2,
		CELL_CRACK:  image3,
		CELL_BONES:  image4,
		CELL_ROCKS:  image5,
		CELL_PLATE:  image6,
		CELL_START:  image7,
		CELL_FINISH: image8,
		CELL_PORTAL: image9,
		CELL_GATE0:  image10,
		CELL_GATE1:  image11,
		CELL_SAND:   image12,
		CELL_LOCK1:  image13,
		CELL_LOCK2:  image14,
		CELL_ODIRL:  image15,
		CELL_ODIRR:  image16,
		CELL_ODIRU:  image17,
		CELL_ODIRD:  image18,
		CELL_GLASS:  image19,
		CELL_TRAP0:  image20,
		CELL_TRAP1:  image21,
		CELL_BEAMGN: image22,
		CELL_BEAMCL: image23,
		CELL_OUTER_WALL: outer_wall_image,
	}

	load_actor_theme_image(char, 'char')

	load_actor_theme_image(cursor, 'cursor')

	for enemy in enemies:
		load_actor_theme_image(enemy, 'enemy')

	for barrel in barrels:
		reload_actor_theme_image(barrel)

	for cart in carts:
		reload_actor_theme_image(cart)

	for lift in lifts:
		reload_actor_theme_image(lift)

	for mirror in mirrors:
		reload_actor_theme_image(mirror)

	for drop in drops:
		drop.set_image(get_theme_image_name(drop.name))

	puzzle.on_set_theme()

def set_music_fadein():
	global music_orig_volume, music_start_time, music_fadein_time

	music_orig_volume = music.get_volume()
	music_start_time  = level_time
	music_fadein_time = level_time + MUSIC_FADEIN_DURATION
	music.set_volume(0)

def reset_music_fadein():
	global music_orig_volume, music_start_time, music_fadein_time

	if music_orig_volume:
		music.set_volume(music_orig_volume)
	music_orig_volume = music_start_time = music_fadein_time = None

def start_music():
	global is_music_started

	if mode != "game" and mode != "end":
		print("Called start_music outside of game or end")
		return

	is_music_started = True

	if is_music_enabled:
		set_music_fadein()
		track = level["music"] if mode == "game" else "victory" if is_game_won else "defeat"
		music.play(track)

def stop_music():
	global is_music_started

	is_music_started = False

	if is_music_enabled:
		music.stop()
		reset_music_fadein()

def enable_music():
	global is_music_enabled

	if is_music_enabled:
		return

	is_music_enabled = True

	if is_music_started:
		start_music()

def disable_music():
	global is_music_enabled, is_music_started

	if not is_music_enabled:
		return

	if is_music_started:
		stop_music()
		is_music_started = True

	is_music_enabled = False

def play_sound(name):
	if not is_sound_enabled:
		return

	sound = getattr(sounds, name)
	sound.play()

def reset_level_title_and_goal_time():
	global level_title_time, level_goal_time

	level_title_time = level_time + LEVEL_TITLE_TIME
	level_goal_time = level_title_time + LEVEL_GOAL_TIME

def clear_level_title_and_goal_time():
	global level_title_time, level_goal_time

	level_title_time = 0
	level_goal_time = 0

def reset_idle_time():
	global idle_time, last_regeneration_time

	idle_time = 0
	last_regeneration_time = 0

def init_new_level(offset=1, config=None, reload_stored=False, create_puzzle_func=create_puzzle):
	global level, level_time, mode, is_game_won
	global level_title, level_name, level_goal
	global puzzle
	global bg_image
	global revealed_map
	global switch_cell_infos, portal_demolition_infos
	global char_cells, enter_room_idx
	global level_time
	global map, stored_level

	if config and offset != 0:
		die("Can't init config for a non-current level")

	if reload_stored and offset != 0:
		die("Can't reload a non-current level")

	if not is_level_unset() and is_level_out_of_range(offset):
		print("Requested level is out of range")
		return

	if puzzle:
		mode = "finish"
		puzzle.finish()
		game.stop_level()

	stop_music()
	clear_level_title_and_goal_time()
	mode = "init"

	level = config if config else set_level(offset)
	if not level:
		mode = "end"
		is_game_won = True
		start_music()
		return

	flags.parse_level(level)

	char.reset_state()
	char_cells = [None] * flags.NUM_ROOMS
	char.power  = level.get("char_power")
	char.health = level.get("char_health")
	char.attack = None if char.power else INITIAL_CHAR_ATTACK

	barrels.clear()
	enemies.clear()
	carts.clear()
	lifts.clear()
	mirrors.clear()
	killed_enemies.clear()
	portal_destinations.clear()

	solution.reset()

	puzzle = create_puzzle_func(level, Globals)

	set_map_size(level.get("map_size", DEFAULT_MAP_SIZE), puzzle.has_border())
	import_size_constants()
	import_size_constants(game)
	import_size_constants(Puzzle)
	import_size_constants(puzzle)

	draw_apply_sizes()
	flags.apply_sizes()

	game.init_console()

	bg_image = None
	if "bg_image" in level:
		bg_image = load_image(level["bg_image"], (MAP_W, MAP_H), level.get("bg_image_crop", False))

	level_title = "main-screen" if level["n"] == 0 else level.get("title", "{level-label} %s" % level["n"])
	level_name = "level-%s-name" % level["n"]
	level_name = level.get("name", level_name if _(level_name) != level_name else "")
	if "goal" in level:
		level_goal = level["goal"]
	elif puzzle.is_goal_to_be_solved():
		level_goal = "solve-%s-puzzle" % puzzle.canonic_name()
	elif puzzle.is_goal_to_kill_enemies() and not flags.has_finish:
		level_goal = "kill-enemies"
	else:
		level_goal = "reach-finish"
	if "time_limit" in level:
		level_goal = "{%s} {in-word} %d {seconds-word}" % (level_goal, level["time_limit"])

	for drop in drops:
		# should be called after set_map_size()
		drop.reset()

	if reload_stored:
		theme_name = stored_level["theme_name"]
		char_cells = stored_level["char_cells"]
		map = stored_level["map"]
		propagate_map()
		for enemy_info in stored_level["enemy_infos"]:
			create_enemy(*enemy_info)
		for barrel_cell in stored_level["barrel_cells"]:
			create_barrel(barrel_cell)
		for lift_info in stored_level["lift_infos"]:
			create_lift(*lift_info)
		for mirror_data in stored_level["mirror_datas"]:
			mirror_host = get_actor_on_cell(mirror_data[0], barrels + carts + lifts)
			create_mirror(mirror_host, mirror_data)
		for portal_cell, dst_cell in stored_level["portal_destinations"].items():
			create_portal(portal_cell, dst_cell)
		for drop in drops:
			drop.restore_state(stored_level["drop_states"][drop.name])
		set_room_and_notify_puzzle(0)
		puzzle.restore_level(stored_level)
	else:
		theme_name = level["theme"]
		if puzzle.is_long_generation():
			draw_long_level_generation()
		generate_map()

	set_theme(theme_name)

	for drop in drops:
		drop.active = drop.num_total > 0

	level_time = 0
	reset_idle_time()
	if is_level_intro_enabled:
		reset_level_title_and_goal_time()

	if flags.is_cloud_mode:
		revealed_map = ndarray((MAP_SIZE_X, MAP_SIZE_Y), dtype=bool)
		revealed_map.fill(False)

	switch_cell_infos.clear()
	portal_demolition_infos.clear()

	enter_room_idx = 0
	enter_room(enter_room_idx)

	start_music()

	stored_level = {
		"map": map.copy(),
		"char_cells": char_cells.copy(),
		"enemy_infos": tuple((enemy.c, enemy.power or enemy.health, enemy.attack, enemy.drop) for enemy in enemies),
		"barrel_cells": tuple(barrel.c for barrel in barrels),
		"lift_infos": tuple((lift.c, lift.type) for lift in lifts),
		"mirror_datas": tuple(mirror.to_data() for mirror in mirrors),
		"portal_destinations": dict(portal_destinations),
		"drop_states": dict([(drop.name, drop.get_state()) for drop in drops]),
		"theme_name": theme_name,
	}
	puzzle.store_level(stored_level)

def init_new_room():
	global enter_room_idx

	if not flags.MULTI_ROOMS or enter_room_idx == flags.NUM_ROOMS - 1:
		init_new_level()
	else:
		enter_room_idx += 1
		enter_room(enter_room_idx)

def init_main_screen():
	reset_level()
	init_new_level(0, main_screen_level_config, False, create_main_screen)

def draw_map():
	for cy in range(len(map[0])):
		for cx in range(len(map)):
			cell = (cx, cy)
			cell_type = map[cell]
			cell_types = [cell_type]
			if cell_type in CELL_FLOOR_EXTENSIONS and cell_type != CELL_FLOOR:
				cell_types.insert(0, CELL_FLOOR)
			if cell == pressed_cell:
				cell_types.append(CELL_CURSOR)
			puzzle.modify_cell_types_to_draw(cell, cell_types)
			for cell_type in cell_types:
				cell_image = None
				if flags.is_cloud_mode and not revealed_map[cell]:
					if bg_image:
						continue
					cell_image = cloud_image
				elif cell_type == CELL_CURSOR:
					cell_image = cursor._surf
				elif cell_image0 := puzzle.get_cell_image_to_draw(cell, cell_type):
					cell_image = cell_image0
				elif cell in switch_cell_infos and switch_cell_infos[cell][1] == cell_type:
					old_cell_type, _, end_time, duration = switch_cell_infos[cell]
					remaining_time = end_time - level_time
					if remaining_time < 0:
						del switch_cell_infos[cell]
						remaining_time = 0
					factor = remaining_time / duration
					if factor > 1:  # should never happen, but python is buggy
						factor = 1
					cell_type_opacities = [
						(old_cell_type, factor ** 0.5),
						(cell_type, (1 - factor) ** 0.5)
					]
					if cell_type == CELL_FLOOR:
						cell_type_opacities.reverse()
					for cell_type, opacity in cell_type_opacities:
						if cell_type == CELL_VOID:
							continue
						cell_image = cell_images[cell_type]
						cell_image.draw(cell, opacity if cell_type != CELL_FLOOR else 1)
					continue
				elif cell_type == CELL_VOID:
					continue
				elif cell_type in cell_images:
					cell_image = cell_images[cell_type]
				else:
					cell_image = create_text_cell_image(cell_type)

				if not cell_image:
					debug_map()
					die("Bug. Got null cell image at %s cell_type=%s" % (cell, cell_type))
				elif cell_image.__class__.__name__ == 'CellActor':
					cell_image.draw(cell)
				else:
					screen.blit(cell_image, cell_to_pos_00(cell))
	puzzle.on_draw_map()

def get_time_str(time):
	sec = int(time)
	min = sec / 60
	sec = sec % 60
	return "%d:%02d" % (min, sec) if min < 60 else "%d:%02d:%02d" % (min / 60, min % 60, sec)

def draw_status():
	cy = MAP_SIZE_Y
	for cx in MAP_X_RANGE:
		status_image.draw((cx, cy))

	draw_status_drops(drops)

	draw_status_message(POS_STATUS_Y)

	solution.set_status_drawn()

	if mode == "game":
		color, gcolor = ("#60C0FF", "#0080A0") if "time_limit" not in level else ("#FFC060", "#A08000") if level["time_limit"] - level_time > CRITICAL_REMAINING_LEVEL_TIME else ("#FF6060", "#A04040")
		time_str = get_time_str(level_time if "time_limit" not in level else level["time_limit"] - level_time)
		screen.draw.text(time_str, midright=(WIDTH - 20, POS_STATUS_Y), color=color, gcolor=gcolor, owidth=1.2, ocolor="#404030", alpha=1, fontsize=27)

def draw():
	if mode in ("start", "finish", "init"):
		return
	if not game.screen:
		game.screen = screen
	screen.fill("#2f3542")
	if bg_image:
		screen.blit(bg_image, (MAP_POS_X1, MAP_POS_Y1))
	visible_barrels = get_revealed_actors(barrels)
	visible_enemies = get_revealed_actors(enemies)

	draw_map()
	draw_status()
	for cart in carts:
		cart.draw()
	for lift in lifts:
		lift.draw()
	for drop in drops:
		drop.draw_instances()
	for barrel in visible_barrels:
		barrel.draw()
	for enemy in killed_enemies:
		enemy.draw()
	for enemy in visible_enemies:
		enemy.draw()
	char.draw()
	for actor in visible_enemies + [char]:
		if actor.power:
			draw_actor_hint(actor, actor.power, (0, -CELL_H * 0.5 - 14), CHAR_POWER_COLORS if actor == char else ENEMY_POWER_COLORS)
		elif actor.health is not None:
			draw_actor_hint(actor, actor.health, (-12, -CELL_H * 0.5 - 14), ACTOR_HEALTH_COLORS)
			draw_actor_hint(actor, actor.attack, (+12, -CELL_H * 0.5 - 14), ACTOR_ATTACK_COLORS)
	cursor.draw()

	puzzle.on_draw()

	game.show_console()

	if mode == "end":
		end_line = _('victory-text') if is_game_won else _('defeat-text')
		draw_central_flash()
		screen.draw.text(end_line, center=(POS_CENTER_X, POS_CENTER_Y), color='white', gcolor=("#008080" if is_game_won else "#800000"), owidth=0.8, ocolor="#202020", alpha=1, fontsize=60)

	if mode == "game" and level_title_time > 0:
		if puzzle.is_virtual():
			draw_central_flash()
		yd = -14 if level_name else 0
		screen.draw.text(_(level_title), center=(POS_CENTER_X, POS_CENTER_Y + yd), color='yellow', gcolor="#AAA060", owidth=1.2, ocolor="#404030", alpha=1, fontsize=50)
		screen.draw.text(_(level_name),  center=(POS_CENTER_X, POS_CENTER_Y + 21), color='white',  gcolor="#C08080", owidth=1.2, ocolor="#404030", alpha=1, fontsize=32)
	elif mode == "game" and level_goal_time > 0:
		goal_line = _(level_goal)
		if puzzle.is_virtual():
			draw_central_flash()
		screen.draw.text(goal_line, center=(POS_CENTER_X, POS_CENTER_Y), color='#FFFFFF', gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=1, fontsize=40)

def kill_enemy_cleanup():
	enemy = killed_enemies.pop(0)
	enemy.reset_inplace_animation()

def cancel_playing_solution():
	if solution.is_play_mode():
		solution.reset()
		set_status_message("Playing solution stopped", "stop-auto-play", 1, 3)
		return True
	return False

def unset_prepared_solution():
	if solution.is_active() and not solution.is_play_mode():
		solution.reset()
		return True
	return False

def press_cell(cell, button=None):
	was_handled = puzzle.press_cell(cell, button)
	if was_handled:
		unset_prepared_solution()
	return was_handled

def change_solution_move_delay(is_reset, is_dec, is_inc):
	if is_reset:
		solution.reset_move_delay()
		return True
	if is_dec:
		solution.dec_move_delay()
		return True
	if is_inc:
		solution.inc_move_delay()
		return True
	return False

def handle_requested_new_level():
	if game.requested_new_level:
		new_level = game.requested_new_level
		game.requested_new_level = None
		init_new_level(new_level)
		return

def handle_press_key():
	global is_move_animate_enabled, is_level_intro_enabled, is_sound_enabled

	# apply workaround for the invalid syntax keyboard.return in python
	keyboard.enter = keys.RETURN in keyboard._pressed

	keyboard.shift = keyboard.lshift or keyboard.rshift
	keyboard.ctrl  = keyboard.lctrl  or keyboard.rctrl
	keyboard.alt   = keyboard.lalt   or keyboard.ralt

	reset_idle_time()

	if mode != "game" and mode != "end" and mode != "next":
		return

	if keyboard.escape and keyboard.ctrl:
		game.toggle_console()
		return

	if solution.is_play_mode():
		if change_solution_move_delay(keyboard.insert, keyboard.pageup, keyboard.pagedown):
			return

	if keyboard.escape and not cursor.is_active():
		init_main_screen()
		return

	if keyboard.rshift:
		if keyboard.e:
			set_lang('en')
		if keyboard.r:
			set_lang('ru')
		if keyboard.h:
			set_lang('he')

		if keyboard.l:
			is_level_intro_enabled = not is_level_intro_enabled
			if is_level_intro_enabled:
				reset_level_title_and_goal_time()
			else:
				clear_level_title_and_goal_time()

		if keyboard.s:
			flags.is_stopless = not flags.is_stopless

		if keyboard.d:
			map_stringio = io.StringIO()
			with stdout_redirected_to(sys.stdout, map_stringio):
				debug_map(full_format=not keyboard.ralt, clean=not keyboard.rctrl)
			clipboard.put(map_stringio.getvalue())
			set_status_message("The current map copied to clipboard and stdout", priority=4, duration=5)

		return

	if keyboard.f1:
		set_theme("default")
	if keyboard.f2:
		set_theme("classic")
	if keyboard.f3:
		set_theme("ancient1")
	if keyboard.f4:
		set_theme("ancient2")
	if keyboard.f5:
		set_theme("modern1")
	if keyboard.f6:
		set_theme("modern2")
	if keyboard.f7:
		set_theme("minecraft")
	if keyboard.f8:
		set_theme("moss"      if not keyboard.shift else "stoneage3")
	if keyboard.f9:
		set_theme("stoneage1" if not keyboard.shift else "stoneage4")
	if keyboard.f10:
		set_theme("stoneage2" if not keyboard.shift else "stoneage5")

	if keyboard.f11:
		# Currently toggle_fullscreen() caused warning on the first time, so use set_mode()
		pygame.display.set_mode((WIDTH, HEIGHT), 0 if pygame.display.is_fullscreen() else pygame.FULLSCREEN)
	if keyboard.f12:
		pygame.mouse.set_visible(not pygame.mouse.get_visible())

	if keyboard.l:
		reset_level_title_and_goal_time()

	if keyboard.m:
		if is_music_enabled:
			disable_music()
		else:
			enable_music()

	if keyboard.s:
		is_sound_enabled = not is_sound_enabled

	if keyboard.a:
		is_move_animate_enabled = not is_move_animate_enabled

	if keyboard.q:
		quit()

	if mode == "next":
		return

	if keyboard.space and not cursor.is_active():
		if map[char.c] == CELL_PORTAL:
			teleport_char()
		else:
			press_cell(char.c)

	if keyboard.u:
		if not game.undo_move():
			play_sound('error')

	cursor_was_active = cursor.is_active()

	if keyboard.enter:
		if not cursor.is_active():
			cursor.toggle()
		else:
			if not press_cell(cursor.c):
				cursor.toggle()

	if keyboard.space or keyboard.escape:
		if not cursor.is_char_selected():
			cursor.reset()

	if DEBUG_LEVEL > 0 and cursor_was_active and not cursor.is_active():
		set_status_message(priority=0)

	if keyboard.home:
		press_cell(cursor.selected_actor.c, 1)
	if keyboard.end:
		press_cell(cursor.selected_actor.c, 3)
	if keyboard.insert:
		press_cell(cursor.selected_actor.c, 2)
	if keyboard.delete:
		press_cell(cursor.selected_actor.c, 6)
	if keyboard.pageup:
		press_cell(cursor.selected_actor.c, 4)
	if keyboard.pagedown:
		press_cell(cursor.selected_actor.c, 5)

	puzzle.on_press_key(keyboard)
	handle_requested_new_level()

	if is_level_unset():
		return

	# if any key is pressed while playing solution, stop it
	if cancel_playing_solution():
		return

	if keyboard.p:
		offset = get_prev_level_group_offset() if keyboard.lctrl else get_prev_level_offset()
		init_new_level(offset)
	if keyboard.r:
		offset = get_curr_level_group_offset() if keyboard.lctrl else 0
		init_new_level(offset, reload_stored=keyboard.lalt and not keyboard.lctrl)
	if keyboard.n:
		offset = get_next_level_group_offset() if keyboard.lctrl else get_next_level_offset()
		init_new_level(offset)

	if keyboard.w:
		win_room()

	if keyboard.o:
		priority = randint(0, 4)
		set_status_message("Hello, world! [priority=%d]" % priority, None, priority, 10)

	if keyboard.kp_enter:
		if solution.is_active():
			solution.set_play_mode()
		elif not solution.is_find_mode():
			find_solution_info = puzzle.prepare_solution()
			if find_solution_info:
				msg, find_func = find_solution_info
				solution.set_find_mode(msg)
				solution.set_find_func(find_func)

	if keyboard.s and keyboard.alt:
		print(clipboard.get())
		clipboard.put("My text")
		print(clipboard.get())

def on_key_down(key):
	handle_press_key()

def on_mouse_down(pos, button):
	if mode != "game":
		return

	if solution.is_play_mode():
		if change_solution_move_delay(button == 2, button == 4, button == 5):
			return
	if cancel_playing_solution():
		return
	if cursor.is_active():
		cursor.toggle()
	cell = pos_to_cell(pos)
	press_cell(cell, button)
	handle_requested_new_level()

def loose_game():
	global mode, is_game_won

	stop_music()
	mode = "end"
	is_game_won = False
	set_status_message("You lost. Press Alt-R to retry", priority=0)
	start_music()

def win_room():
	global mode

	play_sound("finish")
	mode = "next"
	clock.schedule(init_new_room, WIN_NEW_DELAY)

def check_victory():
	if mode != "game":
		return

	if (puzzle.is_lost()
		or "time_limit" in level and level_time > level["time_limit"]
		or char.health is not None and char.health <= 0
		or char.power is not None and char.power <= 0
		or map[char.c] == CELL_TRAP1
	):
		loose_game()
		return

	status_messages = []
	can_win = True
	goal_achieved = False

	if puzzle.is_goal_to_be_solved():
		if puzzle.is_solved():
			goal_achieved = True
			status_messages.append("Puzzle solved!")
		else:
			can_win = False
			status_messages.append("Solve puzzle!")

	if puzzle.is_goal_to_kill_enemies():
		if not sum(1 for enemy in enemies if is_actor_in_room(enemy)) and not killed_enemies:
			goal_achieved = True
			status_messages.append("All enemies killed!")
		else:
			can_win = False
			status_messages.append("Kill all enemies!")

	if level.get("disable_win"):
		can_win = False

	if flags.has_finish or puzzle.has_finish():
		if map[char.c] == CELL_FINISH and can_win:
			char.activate_inplace_animation(level_time, CHAR_APPEARANCE_SCALE_DURATION, scale=(1, 0))
			win_room()
		else:
			status_messages.append("Reach finish!")
	elif goal_achieved and can_win:
		win_room()

	if status_messages:
		set_status_message(" ".join(status_messages))

pressed_cell = None

def press_cell_cleanup():
	global pressed_cell
	pressed_cell = None

def prepare_move():
	clock.unschedule(press_cell_cleanup)
	press_cell_cleanup()

def press_cell_in_solution(cell, button=None):
	global pressed_cell
	if cursor.is_active():
		return
	if cell != char.c:
		pressed_cell = cell
		clock.schedule(press_cell_cleanup, SOLUTION_MOVE_DELAY)
	if not puzzle.press_cell(cell, button):
		play_sound('error')

teleport_char_in_progress = False

def finish_teleport_char():
	global teleport_char_in_progress
	teleport_char_in_progress = False

def teleport_char():
	global teleport_char_in_progress

	if map[char.c] != CELL_PORTAL and not teleport_char_in_progress:
		die("Called teleport_char not on CELL_PORTAL and not in progress")

	if not teleport_char_in_progress:
		teleport_char_in_progress = True
		char.activate_inplace_animation(level_time, CHAR_APPEARANCE_SCALE_DURATION, scale=(1, 0), angle=(0, 540), on_finished=teleport_char)
	else:
		char.c = portal_destinations[char.c]
		char.activate_inplace_animation(level_time, CHAR_APPEARANCE_SCALE_DURATION, scale=(0, 1), angle=(540, 0), on_finished=finish_teleport_char)

def leave_cell(old_char_cell):
	if map[old_char_cell] == CELL_SAND:
		switch_cell_type(old_char_cell, CELL_VOID, SAND_DISAPPREAR_DURATION)

	puzzle.on_leave_cell()

def prepare_enter_cell(animate_duration):
	# prepare drop disappear if any
	for drop in drops:
		if drop.has_instance(char.c):
			drop.disappear(char.c, level_time, animate_duration)

	if map[char.c] == CELL_LOCK1:
		switch_cell_type(char.c, CELL_FLOOR, LOCK_DISAPPREAR_DURATION)
		drop_key1.consume()
	elif map[char.c] == CELL_LOCK2:
		switch_cell_type(char.c, CELL_FLOOR, LOCK_DISAPPREAR_DURATION)
		drop_key2.consume()

	puzzle.on_prepare_enter_cell()
	char.phased = puzzle.is_char_phased()

def enter_cell():
	# collect drop if any
	for drop in drops:
		if (args := drop.collect(char.c)) is not None:
			game.remember_extra_obj_state(char)
			if drop.name == 'heart' and not char.power:
				char.health += BONUS_HEALTH_VALUE
			if drop.name == 'sword' and not char.power:
				char.attack += BONUS_ATTACK_VALUE
			if drop.name == 'might' and char.power:
				op, factor = args
				if op == '\u00d7': char.power *= factor   # '×'
				if op == '\u00f7': char.power //= factor  # '÷'
				if op == '+': char.power += factor
				if op == '-': char.power -= factor

	if map[char.c] == CELL_PORTAL:
		teleport_char()

	puzzle.on_enter_cell()

last_move_diff = None

def continue_move_char():
	diff_x, diff_y = last_move_diff
	last_move_diff = None
	move_char(diff_x, diff_y)

def get_move_animate_duration(old_char_cell):
	distance = cell_distance(old_char_cell, char.c)
	animate_time_factor = distance - (distance - 1) / 2
	return animate_time_factor * ARROW_KEYS_RESOLUTION

def activate_beat_animation(actor, diff, tween):
	actor.move_pos((diff[0] * ENEMY_BEAT_OFFSET, diff[1] * ENEMY_BEAT_OFFSET))
	actor.animate(ENEMY_BEAT_ANIMATION_TIME, tween)

def kill_enemy(enemy):
	play_sound("kill")
	game.remember_collection_elem(enemies, enemy)
	enemies.remove(enemy)
	# fallen drops upon enemy death
	if enemy.drop:
		enemy.drop.instantiate(enemy)
	enemy.activate_inplace_animation(level_time, ENEMY_KILL_ANIMATION_TIME, angle=(0, (-90, 90)[randint(0, 1)]), opacity=(1, 0.3), scale=(1, 0.8))
	killed_enemies.append(enemy)
	clock.schedule(kill_enemy_cleanup, ENEMY_KILL_ANIMATION_TIME + ENEMY_KILL_DELAY)

def beat_or_kill_enemy(enemy, diff):
	if enemy.power is not None or char.power is not None:
		die("Called beat_or_kill_enemy in power mode")

	enemy.health -= char.attack
	# can't move if we face enemy, cancel the move
	char.move(diff, undo=True)
	# animate beat or kill
	if enemy.health > 0:
		play_sound("beat")
		activate_beat_animation(enemy, diff, 'decelerate')
	else:
		kill_enemy(enemy)
	activate_beat_animation(char, diff, 'bounce_end')

def move_char(diff):
	global last_move_diff

	old_char_pos = char.pos
	old_char_cell = char.c

	# try to move forward, and prepare to cancel if the move is impossible
	char.move(diff)

	if flags.is_stopless:
		is_jumped = False
		while map[char.c] in CELL_FLOOR_TYPES and not is_cell_occupied_except_char(char.c) and can_move(diff):
			char.move(diff)
			is_jumped = True
		if is_move_animate_enabled and is_jumped and is_cell_occupied_except_char(char.c) and last_move_diff is None:
			# undo one step
			char.move(diff, undo=True)
			last_move_diff = diff
			char.pos = old_char_pos
			char.animate(get_move_animate_duration(old_char_cell), on_finished=continue_move_char)
			return

	should_pull = flags.allow_barrel_pull and keyboard.shift
	pull_barrel_cell = None
	if should_pull:
		if not is_cell_accessible(char.c):
			# can't pull into obstacle
			char.move(diff, undo=True)
			return
		pull_barrel_cell = apply_diff(old_char_cell, diff, subtract=True)

	# collision with enemies
	enemy = get_actor_on_cell(char.c, enemies)
	if enemy:
		game.remember_extra_obj_state(char)
		game.remember_extra_obj_state(enemy)
		if char.power is None:
			char.health -= enemy.attack
			beat_or_kill_enemy(enemy, diff)
			return
		else:
			if char.power >= enemy.power:
				char.power += enemy.power
				kill_enemy(enemy)
			else:
				char.power = 0
				# we die, cancel move
				char.move(diff, undo=True)
				return

	# collision with barrels
	barrel = get_actor_on_cell(pull_barrel_cell or char.c, barrels)
	if barrel:
		next_barrel_cell = apply_diff(barrel.c, diff)
		if not is_cell_accessible(next_barrel_cell, allow_enemy=True):
			# can't push, cancel the move
			char.move(diff, undo=True)
			return
		else:
			# if enemy is in the next barrel cell, possibly don't move; beat or kill it
			if enemy := get_actor_on_cell(next_barrel_cell, enemies):
				game.remember_extra_obj_state(enemy)
				if char.power is None:
					beat_or_kill_enemy(enemy, diff)
					activate_beat_animation(barrel, diff, 'bounce_end')
					return
				else:
					# in power mode unconditionally kill enemy using barrel
					kill_enemy(enemy)

			# can push, animate the push
			barrel.move_animated(diff, enable_animation=is_move_animate_enabled)

	# can move, process the character move: leave_cell, enter_cell
	unset_prepared_solution()

	# process lift movement if available
	if lift_target := get_lift_target(old_char_cell, diff):
		distance = cell_distance(old_char_cell, lift_target)
		for i in range(1, distance):
			char.move(diff)
		lift = get_actor_on_cell(old_char_cell, lifts)
		lift.move_animated(target=lift_target, enable_animation=is_move_animate_enabled, on_finished=activate_cursor_after_lift_movement)

	leave_cell(old_char_cell)

	# animate the move if needed
	if is_move_animate_enabled:
		animate_duration = get_move_animate_duration(old_char_cell)
		prepare_enter_cell(animate_duration)
		char.pos = old_char_pos
		char.animate(animate_duration, on_finished=enter_cell)
	else:
		prepare_enter_cell(0)
		enter_cell()

	reveal_map_near_char()

def activate_cursor_after_lift_movement():
	if not cursor.is_lift_selected():
		return
	lift = cursor.selected_actor
	if lift.type in (MOVE_L, MOVE_R, MOVE_U, MOVE_D):
		cursor.toggle()

def move_selected_lift(diff):
	lift = cursor.selected_actor
	if lift_target := get_lift_target(lift.c, diff):
		for actor in [lift, char] if char.c == lift.c else [lift]:
			actor.move_animated(target=lift_target, enable_animation=is_move_animate_enabled, on_finished=activate_cursor_after_lift_movement)

def process_move(diff):
	if cursor.is_active():
		cursor.move_animated(diff, enable_animation=is_move_animate_enabled)
	else:
		game.start_move()
		if cursor.is_lift_selected():
			move_selected_lift(diff)
		else:
			move_char(diff)

def can_move(diff):
	dest_cell = apply_diff(cursor.selected_actor.c, diff)

	if not is_cell_in_room(dest_cell):
		return False

	if cursor.is_active():
		return True

	if cursor.is_lift_selected():
		return map[dest_cell] == CELL_VOID and not is_cell_in_actors(dest_cell, lifts)

	return (
		map[dest_cell] not in CELL_CHAR_MOVE_OBSTACLES
		or map[dest_cell] == CELL_LOCK1 and drop_key1.num_collected > 0
		or map[dest_cell] == CELL_LOCK2 and drop_key2.num_collected > 0
		or map[dest_cell] == CELL_ODIRL and diff != (+1, 0)
		or map[dest_cell] == CELL_ODIRR and diff != (-1, 0)
		or map[dest_cell] == CELL_ODIRU and diff != (0, +1)
		or map[dest_cell] == CELL_ODIRD and diff != (0, -1)
		or is_cell_in_actors(dest_cell, lifts)
		or get_lift_target(char.c, diff)
	)

ARROW_KEY_CODE = {
	'r': pygame.K_RIGHT,
	'l': pygame.K_LEFT,
	'd': pygame.K_DOWN,
	'u': pygame.K_UP,
}

def update(dt):
	global level_title_time, level_goal_time
	global game_time, level_time, idle_time, last_regeneration_time
	global last_time_arrow_keys_processed, last_processed_arrow_keys, pressed_arrow_keys

	if mode == "start":
		init_main_screen()
		return

	game_time += dt
	level_time += dt
	idle_time += dt

	if music_fadein_time:
		if level_time >= music_fadein_time:
			reset_music_fadein()
		else:
			factor = (level_time - music_start_time) / (music_fadein_time - music_start_time)
			music.set_volume(music_orig_volume * (factor ** 2))

	for actor in active_inplace_animation_actors:
		actor.update_inplace_animation(level_time)

	for cell in list(portal_demolition_infos):
		new_cell_type, start_time = portal_demolition_infos[cell]
		if level_time >= start_time:
			del portal_demolition_infos[cell]
			switch_cell_type(cell, new_cell_type, PORTAL_DEMOLITION_DURATION)

	puzzle.on_update(level_time)

	if level_title_time < level_time:
		level_title_time = 0
	if level_goal_time < level_time:
		level_goal_time = 0

	if char.health is not None and (
		last_regeneration_time == 0 and idle_time >= REGENERATION_IDLE_TIME or
		last_regeneration_time != 0 and idle_time >= last_regeneration_time + REGENERATION_NEXT_TIME
	):
		char.health += REGENERATION_HEALTH
		if char.health > level["char_health"]:
			char.health = level["char_health"]
		last_regeneration_time = idle_time

	if solution.is_play_mode() and not teleport_char_in_progress:
		solution.play_move()

	if solution.is_find_mode():
		solution_items, msg = solution.call_find_func()
		if solution_items:
			solution.set(solution_items)
		elif msg:
			solution.set_find_mode(msg)
		else:
			solution.set_not_found()

	check_victory()

	if DEBUG_LEVEL > 0 and cursor.is_active():
		set_status_message(str(cursor.c), priority=0)

	if char.is_animated() or mode == "next" or game.is_console_enabled():
		return

	scan_joysticks_and_state()

	if emulate_joysticks_press_key(keyboard):
		handle_press_key()
		return

	keys = pygame.key.get_pressed()
	joistick_arrow_keys = get_joysticks_arrow_keys()

	if last_time_arrow_keys_processed is None:
		last_time_arrow_keys_processed = game_time
		last_processed_arrow_keys = []
		pressed_arrow_keys = []

	for key in ('r', 'l', 'd', 'u'):
		is_key_pressed = keys[ARROW_KEY_CODE[key]] or key in joistick_arrow_keys
		if is_key_pressed and key not in pressed_arrow_keys:
			pressed_arrow_keys.append(key)
			reset_idle_time()
		if not is_key_pressed and key in pressed_arrow_keys and key in last_processed_arrow_keys:
			pressed_arrow_keys.remove(key)

	if game_time - last_time_arrow_keys_processed < ARROW_KEYS_RESOLUTION:
		return

	last_time_arrow_keys_processed = game_time
	last_processed_arrow_keys = []
	last_processed_arrow_diff = (0, 0)

	new_char_flip_direction = None
	def set_arrow_key_to_process(key, diff):
		global last_processed_arrow_keys
		nonlocal last_processed_arrow_diff
		nonlocal new_char_flip_direction
		if not ALLOW_DIAGONAL_MOVES and last_processed_arrow_keys:
			return
		pressed_arrow_keys.remove(key)
		next_diff = apply_diff(last_processed_arrow_diff, diff)
		if cursor.is_char_selected() and key in (DIRECTION_R, DIRECTION_L):
			new_char_flip_direction = key
		if can_move(next_diff) and not keyboard.rctrl:
			last_processed_arrow_keys.append(key)
			last_processed_arrow_diff = next_diff

	for key in list(pressed_arrow_keys):
		if key == 'r' and key not in last_processed_arrow_keys and 'l' not in last_processed_arrow_keys:
			set_arrow_key_to_process(key, (+1, +0))
		if key == 'l' and key not in last_processed_arrow_keys and 'r' not in last_processed_arrow_keys:
			set_arrow_key_to_process(key, (-1, +0))
		if key == 'd' and key not in last_processed_arrow_keys and 'u' not in last_processed_arrow_keys:
			set_arrow_key_to_process(key, (+0, +1))
		if key == 'u' and key not in last_processed_arrow_keys and 'd' not in last_processed_arrow_keys:
			set_arrow_key_to_process(key, (+0, -1))

	diff_x = 0
	diff_y = 0

	if 'r' in last_processed_arrow_keys:
		diff_x += 1
	if 'l' in last_processed_arrow_keys:
		diff_x -= 1
	if 'd' in last_processed_arrow_keys:
		diff_y += 1
	if 'u' in last_processed_arrow_keys:
		diff_y -= 1

	if new_char_flip_direction is not None:
		set_char_flip((new_char_flip_direction == DIRECTION_L) ^ (not flags.allow_barrel_pull or not keyboard.lshift))

	if diff_x or diff_y:
		process_move((diff_x, diff_y),)

set_solution_funcs(find_path, move_char, press_cell_in_solution, prepare_move)
