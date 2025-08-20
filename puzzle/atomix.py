from . import *

# scramble directions, depending on neighbor presense
scramble_presense_dirs = {
	0x0: 'lrud',
	0x1: ' r  ',
	0x2: 'l   ',
	0x3: '    ',
	0x4: '   d',
	0x5: ' r d',
	0x6: 'l  d',
	0x7: '   d',
	0x8: '  u ',
	0x9: ' ru ',
	0xa: 'l u ',
	0xb: '  u ',
	0xc: '    ',
	0xd: ' r  ',
	0xe: 'l   ',
	0xf: '    ',
}

dir_diffs = {
	'l': (-1, 0),
	'r': (+1, 0),
	'u': (0, -1),
	'd': (0, +1),
}

diff_factors = {
	'l': 1,
	'r': 2,
	'u': 4,
	'd': 8,
}

bonus_molecules = {
	6: (
		[[1, 1], [2, 2], [3, 3]],
		[[1, 2], [3, 4], [5, 6]],
		[[1, 1, 1], [2, 2, 2]],
                [[1, 1, 1], [2, 3, 4]],
		[[1, 2, 3], [4, 4, 4]],
		[[1, 2, 3], [4, 5, 6]],
	),
	9: (
		[[1, 1, 1], [2, 2, 2], [3, 3, 3]],
		[[1, 1, 1], [2, 2, 2], [3, 4, 5]],
		[[1, 1, 1], [2, 3, 4], [5, 5, 5]],
		[[1, 1, 1], [2, 3, 4], [5, 6, 7]],
		[[1, 2, 3], [4, 4, 4], [5, 5, 5]],
		[[1, 2, 3], [4, 4, 4], [5, 6, 7]],
		[[1, 2, 3], [4, 5, 6], [7, 7, 7]],
		[[1, 2, 3], [4, 5, 6], [7, 8, 9]],
	),
	15: (
		[[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12, 13, 14, 15]],
		[[1, 1, 1], [2, 2, 2], [3, 3, 3], [4, 4, 4], [5, 5, 5]],
	),
	16: [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]],
}

bonus_sizes = {
	6: (3, 3),
	9: (4, 4),
	15: (5, 5),
	16: (
		(5, 5),
		(5, 6),
		(6, 5),
		(6, 6),
		(7, 5),
		(7, 7),
	),
}

gnome_molecules = {
	"acetic acid": [
		[''      , 'H↓'    , 'O⇊'    , ''      , ''      ],
		['H→'    , 'C←↑→↓' , 'C←→⇈'  , 'O←→'   , 'H←'    ],
		[''      , 'H↑'    , ''      , ''      , ''      ],
	],
	"acetone": [
		[''      , 'H↓'    , ''      , 'H↓'    , ''      ],
		['H→'    , 'C←↑→↓' , 'C←→⇊'  , 'C←↑→↓' , 'H←'    ],
		[''      , 'H↑'    , 'O⇈'    , 'H↑'    , ''      ],
	],
	"butanol": [
		[''      , 'H↓'    , 'H↓'    , 'H↓'    , 'H↓'    , ''      ],
		['H→'    , 'C←↑→↓' , 'C←↑→↓' , 'C←↑→↓' , 'C←↑→↓' , 'H←'    ],
		[''      , 'H↑'    , 'H↑'    , 'H↑'    , 'O↑↓'   , ''      ],
		[''      , ''      , ''      , ''      , 'H↑'    , ''      ],
	],
	"cyclobutane": [
		[''      , 'H↓'    , 'H↓'    , ''      ],
		['H→'    , 'C←↑→↓' , 'C←↑→↓' , 'H←'    ],
		['H→'    , 'C←↑→↓' , 'C←↑→↓' , 'H←'    ],
		[''      , 'H↑'    , 'H↑'    , ''      ],
	],
	"dimethyl ether": [
		[''      , 'H↓'    , ''      , 'H↓'    , ''      ],
		['H→'    , 'C←↑→↓' , 'O←→'   , 'C←↑→↓' , 'H←'    ],
		[''      , 'H↑'    , ''      , 'H↑'    , ''      ],
	],
	"ethanal": [
		[''      , 'H↓'    , 'H↓'    , ''      ],
		['H→'    , 'C←↑→↓' , 'C←↑⇉'  , 'O⇇'    ],
		[''      , 'H↑'    , ''      , ''      ],
	],
	"ethane": [
		['H↘'    , 'H↓'    , 'H↙'    ],
		[''      , 'C↑↓↖↗' , ''      ],
		[''      , 'C↑↓↘↙' , ''      ],
		['H↗'    , 'H↑'    , 'H↖'    ],
	],
	"ethanol": [
		[''      , 'H↓'    , 'H↓'    , ''      , ''      ],
		['H→'    , 'C←↑→↓' , 'C←↑→↓' , 'O←→'   , 'H←'    ],
		[''      , 'H↑'    , 'H↑'    , ''      , ''      ],
	],
	"ethylene": [
		['H↘'    , ''      , ''      , 'H↙'    ],
		[''      , 'C↖↙⇉'  , 'C↗↘⇇'  , ''      ],
		['H↗'    , ''      , ''      , 'H↖'    ],
	],
	"glycerin": [
		[''      , 'H↓'    , ''      , ''      ],
		['H→'    , 'C←↑→↓' , 'O←→'   , 'H←'    ],
		['H→'    , 'C←↑→↓' , 'O←→'   , 'H←'    ],
		['H→'    , 'C←↑→↓' , 'O←→'   , 'H←'    ],
		[''      , 'H↑'    , ''      , ''      ],
	],
	"lactic acid": [
		['H↘'    , ''      , ''      , 'O⇊'    , ''      , ''      ],
		[''      , 'O↖↘'   , ''      , 'C→↙⇈'  , 'O←→'   , 'H←'    ],
		['H↘'    , ''      , 'C↖↗↘↙' , ''      , ''      , ''      ],
		[''      , 'C↖↗↘↙' , ''      , 'H↖'    , ''      , ''      ],
		['H↗'    , ''      , 'H↖'    , ''      , ''      , ''      ],
	],
	"methanal": [
		['H↓'    , ''      ],
		['C↑↓⇉'  , 'O⇇'    ],
		['H↑'    , ''      ],
	],
	"methane": [
		[''      , 'H↓'    , ''      ],
		['H→'    , 'C←↑→↓' , 'H←'    ],
		[''      , 'H↑'    , ''      ],
	],
	"methanol": [
		[''      , 'H↓'    , ''      , ''      ],
		['H→'    , 'C←↑→↓' , 'O←→'   , 'H←'    ],
		[''      , 'H↑'    , ''      , ''      ],
	],
	"propanal": [
		[''      , 'H↓'    , 'H↓'    , ''      , ''      ],
		['H→'    , 'C←↑→↓' , 'C←↑→↓' , 'C←→↓⇊' , 'H←'    ],
		[''      , 'H↑'    , 'H↑'    , 'O⇈'    , ''      ],
	],
	"propylene": [
		[''      , 'H↓'    , 'H↓'    , ''      , 'H↙'    ],
		['H→'    , 'C←↑→↓' , 'C←↑⇉'  , 'C↗↘⇇'  , ''      ],
		[''      , 'H↑'    , ''      , ''      , 'H↖'    ],
	],
	"pyran": [
		[''      , 'H↓'    , 'H↓'    , ''      , ''      ],
		[''      , 'C↑↙⇉'  , 'C↑↘⇇'  , ''      , 'H↙'    ],
		['O↗↘'   , ''      , ''      , 'C↖↗↘↙' , ''      ],
		[''      , 'C↓↖⇉'  , 'C↓↗⇇'  , ''      , 'H↖'    ],
		[''      , 'H↑'    , 'H↑'    , ''      , ''      ],
	],
	"trans butylen": [
		[''      , ''      , ''      , 'H↘'    , ''      , 'H↙'    ],
		[''      , 'H↘'    , ''      , ''      , 'C↖↗↘↙' , ''      ],
		['H↘'    , ''      , 'C↖↙⇉'  , 'C↗↘⇇'  , ''      , 'H↖'    ],
		[''      , 'C↖↗↘↙' , ''      , ''      , 'H↖'    , ''      ],
		['H↗'    , ''      , 'H↖'    , ''      , ''      , ''      ],
	],
	"water": [
		['H→'    , 'O←→'   , 'H←'    ],
	],
}

chlorine_molecules = {
	"chlorine heptoxide": [
		[''      , 'O↓'      , ''    , 'O↓'    , ''      ],
		['O→'    , '₵→⇊⇇⇈'   , 'O→←' , '₵←⇊⇉⇈' , 'O←'    ],
		[''      , 'O↑'      , ''    , 'O↑'    , ''      ],
	],
}

real_molecules = { **gnome_molecules, **chlorine_molecules }

atom_colors = {
	'H': (200, 200, 255),
	'O': (255, 100, 100),
	'C': (128, 128, 128),
	'₵': (100, 255, 100),
	'N': (100, 100, 255),
	'S': (255, 255, 200),
	'P': (255, 255, 100),
}

def shuffle_new(array):
	array = list(array)
	shuffle(array)
	return array

class AtomixPuzzle(Puzzle):
	def init(self):
		self.goal_molecules = [''] * flags.NUM_ROOMS
		self.atom_indexes_per_room = [{} for i in range(flags.NUM_ROOMS)]
		self.draw_solved_mode = False
		self.last_draw_solved_mode = False
		self.is_loaded = False

	def assert_config(self):
		return not flags.is_any_maze

	def has_border(self):
		return False

	def is_goal_to_be_solved(self):
		return True

	def has_start(self):
		return True

	def has_finish(self):
		return not flags.MULTI_ROOMS and not self.is_loaded

	def has_sand(self):
		return True

	@property
	def goal_molecule(self):
		return self.goal_molecules[room.idx]

	@goal_molecule.setter
	def goal_molecule(self, molecule):
		self.goal_molecules[room.idx] = molecule

		atom_ids = self.get_goal_molecule_atom_ids()
		uniq_atom_ids = []
		atom_base_ids = {}
		atom_base_counters = {}
		for atom_id in atom_ids:
			atom_base = self.get_atom_base(atom_id)
			if atom_base not in atom_base_ids:
				atom_base_ids[atom_base] = []
				atom_base_counters[atom_base] = 0
			if atom_id not in atom_base_ids[atom_base]:
				uniq_atom_ids.append(atom_id)
				atom_base_ids[atom_base].append(atom_id)
		atom_indexes = {}
		for atom_id in uniq_atom_ids:
			atom_base = self.get_atom_base(atom_id)
			atom_base_counters[atom_base] += 1
			atom_indexes[atom_id] = None if len(atom_base_ids[atom_base]) == 1 else atom_base_counters[atom_base]
		self.atom_indexes_per_room[room.idx] = atom_indexes

	@property
	def atom_indexes(self):
		return self.atom_indexes_per_room[room.idx]

	@atom_indexes.setter
	def atom_indexes(self, indexes):
		self.atom_indexes_per_room[room.idx] = indexes

	def get_goal_molecule_atom_ids(self):
		return [atom_id for row in self.goal_molecule for atom_id in row if atom_id != '']

	def get_atom_base(self, atom_id):
		return atom_id[0] if type(atom_id) == str else str(atom_id)
	
	def get_atom_str(self, atom_id):
		index = self.atom_indexes[atom_id]
		index_str = "" if index is None else chr(index + (0xb8 if index == 1 else 0xb0 if index <= 3 else 0x2070))
		return self.get_atom_base(atom_id) + index_str
	
	def get_current_lift_molecule(self):
		room_lifts = get_actors_in_room(lifts)

		x_min = y_min = 1000
		x_max = y_max = -1
		for lift in room_lifts:
			if lift.cx < x_min: x_min = lift.cx
			if lift.cy < y_min: y_min = lift.cy
			if lift.cx > x_max: x_max = lift.cx
			if lift.cy > y_max: y_max = lift.cy

		size_x = x_max - x_min + 1
		size_y = y_max - y_min + 1

		lift_molecule = [[''] * size_x for _ in range(size_y)]

		for lift in room_lifts:
			lift_molecule[lift.cy - y_min][lift.cx - x_min] = lift.atom_id

		return lift_molecule

	def is_solved(self):
		curr_lift_molecule = self.get_current_lift_molecule()
		return curr_lift_molecule == self.goal_molecule

	def store_level(self, stored_level):
		stored_level["is_loaded"] = self.is_loaded
		stored_level["goal_molecules"] = self.goal_molecules
		stored_level["lifts"] = [*lifts]
		for lift in stored_level["lifts"]:
			lift.orig_cell = lift.c

	def restore_level(self, stored_level):
		self.is_loaded = stored_level["is_loaded"]
		for molecule in stored_level["goal_molecules"]:
			self.goal_molecule = molecule
			self.Globals.advance_room()
		# replace stock lifts with our versions holding designated atom image
		lifts.clear()
		lifts.extend(stored_level["lifts"])
		for lift in lifts:
			lift.c = lift.orig_cell

	def on_enter_room(self):
		set_status_message("Press KP Enter to see the goal molecule", self, 0, 12)

	def scramble(self):
		# move all lifts until possible without repetition
		room_lifts = get_actors_in_room(lifts)
		was_scrambled = False

		visited_lift_molecules = [self.goal_molecule]
		for i in range(50):
			for lift in shuffle_new(room_lifts):
				for i in range(randint(1, 10)):
					neigh_presense = 0
					for dir in 'lrdu':
						neigh = apply_diff(lift.c, dir_diffs[dir])
						if not is_cell_in_room(neigh) or self.map[neigh] != CELL_VOID or is_cell_in_actors(neigh, lifts):
							neigh_presense += diff_factors[dir]
					scramble_dirs = [dir for dir in scramble_presense_dirs[neigh_presense] if dir != ' ']
					for scramble_dir in scramble_dirs:
						neigh = apply_diff(lift.c, dir_diffs[scramble_dir])
						target = get_lift_target_at_neigh(lift, neigh)
						if not target:
							continue
						orig_cell = lift.c
						lift.c = target
						lift_molecule = self.get_current_lift_molecule()
						if lift_molecule in visited_lift_molecules:
							lift.c = orig_cell
						else:
							visited_lift_molecules.append(lift_molecule)
							was_scrambled = True
							break
					else:
						break

		return was_scrambled

	def create_atom(self, cell, atom_id, goal_cell):
		non_bonus_mode = type(atom_id) == str
		atom_base = atom_id[0] if non_bonus_mode else ''
		num_uniq_atom_ids = len(set(self.get_goal_molecule_atom_ids()))

		if non_bonus_mode or num_uniq_atom_ids <= len(EXTENDED_COLOR_RGB_VALUES):
			lift_image = load_theme_cell_image('sphere-gray')
			lift_image.fill(atom_colors.get(atom_base) or EXTENDED_COLOR_RGB_VALUES[atom_id - 1], special_flags=pygame.BLEND_RGB_MULT)
		else:
			lift_image = load_theme_cell_image('lift-empty')
		text_surface = create_text_cell_image(self.get_atom_str(atom_id), color='#FFFFC0', gcolor="#808040", owidth=1, ocolor="#404030")
		lift_image.blit(text_surface, (0, 0))

		lift = create_lift(cell, MOVE_A, lift_image)
		lift.atom_id = atom_id
		lift.goal_cell = goal_cell

	def generate_room(self):
		# determine the configured goal molecule
		bonus_mode = self.config.get("bonus_mode")
		if bonus_mode:
			if type(bonus_mode) == tuple:
				bonus_mode = bonus_mode[randint(0, len(bonus_mode) - 1)]
			molecules = bonus_molecules.get(bonus_mode)
		elif "molecule" in self.config and self.config["molecule"] in real_molecules:
			molecules = real_molecules[self.config["molecule"]]
		else:
			molecules = tuple(real_molecules.values())

		if molecules is None:
			self.die("Unknown bonus_mode %s" % bonus_mode)

		goal_molecule = molecules[randint(0, len(molecules) - 1)] if type(molecules) == tuple else molecules
		self.goal_molecule = goal_molecule

		if "size" not in self.config:
			sizes = bonus_sizes.get(bonus_mode) if bonus_mode else (len(goal_molecule[0]) + 1, len(goal_molecule))
			if sizes is None:
				self.die("Unknown size for bonus_mode %s" % bonus_mode)
			size = sizes[randint(0, len(sizes) - 1)] if type(sizes[0]) == tuple else sizes
			self.config["size"] = size

		self.set_area_from_config(align_to_center=True)

		# replace floor with void and fill unused space with walls
		for cell in room.cells:
			self.map[cell] = CELL_VOID if self.is_in_area(cell) else CELL_FLOOR if flags.MULTI_ROOMS else CELL_WALL

		if not flags.MULTI_ROOMS:
			self.Globals.convert_outer_walls(CELL_FLOOR if flags.MULTI_ROOMS else CELL_VOID)

		# create lifts
		for y in range(len(goal_molecule)):
			row = goal_molecule[y]
			for x in range(len(row)):
				atom_id = row[x]
				if atom_id == '':
					continue
				goal_cell = (self.area.x1 + x, self.area.y1 + y)
				self.create_atom(goal_cell, atom_id, goal_cell)

		if not bonus_mode:
			self.map[self.area.x2, self.area.y2] = CELL_SAND

		# scramble lifts
		if self.scramble() and self.is_solved():
			self.generate_room()
			return

		if not flags.MULTI_ROOMS and self.area.y1 > PLAY_Y1:
			self.map[PLAY_X1, PLAY_Y1] = CELL_START
			for x in range(PLAY_X1 + 1, PLAY_X2):
				self.map[x, PLAY_Y1] = CELL_FLOOR
			self.map[PLAY_X2, PLAY_Y1] = CELL_FINISH

	def on_load_map(self, special_cell_values, extra_values):
		self.is_loaded = True

		goal_size_x, goal_size_y = map(int, extra_values.pop(0).split(' '))
		goal_molecule = [[''] * goal_size_x for _ in range(goal_size_y)]

		atom_id_goal_cells = {}
		for goal_atom_value in extra_values:
			goal_cell_x_str, goal_cell_y_str, atom_id = goal_atom_value.split(' ')
			goal_cell_x, goal_cell_y = int(goal_cell_x_str), int(goal_cell_y_str)
			goal_molecule[goal_cell_y][goal_cell_x] = atom_id
			if atom_id not in atom_id_goal_cells:
				atom_id_goal_cells[atom_id] = []
			atom_id_goal_cells[atom_id].append((goal_cell_x, goal_cell_y))

		self.goal_molecule = goal_molecule

		for cell, atom_id in special_cell_values.items():
			# get random goal cell of all corresponding goal cells for atom_id
			goal_cell = atom_id_goal_cells[atom_id].pop()
			goal_cell = (goal_cell[0] + (MAP_SIZE_X - goal_size_x) // 2, goal_cell[1] + (MAP_SIZE_Y - goal_size_y) // 2)
			self.create_atom(cell, atom_id, goal_cell)
			self.map[cell] = CELL_VOID

	def modify_cell_types_to_draw(self, cell, cell_types):
		if self.draw_solved_mode and "map_file" in self.level:
			cell_types.clear()

	def on_press_key(self, keyboard):
		self.draw_solved_mode = keyboard.kp_enter and not self.draw_solved_mode

	def on_update(self, level_time):
		if not active_inplace_animation_actors:
			if self.draw_solved_mode != self.last_draw_solved_mode:
				room_lifts = get_actors_in_room(lifts)
				for lift in room_lifts:
					lift.cell_to_draw = lift.goal_cell if self.draw_solved_mode else None
				self.last_draw_solved_mode = self.draw_solved_mode

	def is_char_phased(self):
		return is_cell_in_actors(char.c, lifts)

