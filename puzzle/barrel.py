from . import *
from sokobansolver import *

FLOOR_COST = 1
CHAR_FLOOR_COST = -1
WALL_COST = 100
OBSTACLE_COST = None

class BarrelPuzzle(Puzzle):
	def init(self):
		self.solver = SokobanSolver()

	def assert_config(self):
		return not flags.is_any_maze

	def has_border(self):
		return True

	def has_plate(self):
		return True

	def is_long_generation(self):
		return True

	def is_goal_to_be_solved(self):
		return True

	def store_level(self, stored_level):
		stored_level["area"] = self.area

	def restore_level(self, stored_level):
		self.area = stored_level["area"]

	def max_valid_zsb_barrel_shuffle(self, barrel_cells, num_moves):
		orig_barrel_cells = barrel_cells
		barrel_cells = barrel_cells.copy()
		max_barrel_cells = orig_barrel_cells
		max_total_distance = 0
		for _ in range(num_moves):
			barrel_cell, target_cell = choice(grid.get_all_valid_zsb_barrel_moves(barrel_cells))
			barrel_cells[barrel_cells.index(barrel_cell)] = target_cell
			total_distance = sum(cell_distance(cell1, cell2) for cell1, cell2 in zip(barrel_cells, orig_barrel_cells))
			if total_distance > max_total_distance:
				max_barrel_cells = barrel_cells.copy()
				max_total_distance = total_distance
		return max_barrel_cells

	def generate_random_zsb_room(self):
		grid.configure(game.map, self.area, flags.is_reverse_barrel)
		if not grid.is_valid_zsb_area_size():
			self.die("Invalid area size %s for Zero Space type-B puzzle" % str(self.area.size))
		self.set_area_border_walls(0)

		zsb_size = grid.get_zsb_size()
		num_barrels = zsb_size[0] * zsb_size[1] - 1
		all_anchor_cells = grid.get_all_zsb_anchor_cells()
		debug(2, "Generating Zero Space type-B puzzle %s with %d barrels" % (grid.get_zsb_size_str(), num_barrels))

		# 1) initialize zsb walls
		for cell in grid.get_zsb_wall_cells():
			self.map[cell] = CELL_WALL

		# 2) create random barrels and plates until both are connected and correspond to each other
		while True:
			barrel_cells = sample(all_anchor_cells, k=num_barrels)
			if not grid.is_zsb_graph_connected(barrel_cells):
				continue
			plate_cells = self.max_valid_zsb_barrel_shuffle(barrel_cells, self.area.num_cells * 2)
			break

		# 3) initialize room barrels
		for cell in barrel_cells:
			create_barrel(cell)

		# 4) initialize room plates
		for cell in plate_cells:
			self.map[cell] = CELL_PLATE

		# 5) initialize char (optional)
		game.set_char_cell(self.area.cell11)

	def check_special_setups(self):
		grid.configure(game.map)
		grid.set_barrels(self.get_room_barrel_cells())
		grid.check_zsb()
		reverse_str = " reverse" if flags.is_reverse_barrel else ""
		if grid.is_zsb:
			msg = "This is Zero Space type-B %s%s puzzle!" % (grid.get_zsb_size_str(), reverse_str)
			self.solver.solution_alg = SOLUTION_ALG_ASTAR
		else:
			msg = "This is Sokoban%s puzzle" % reverse_str
			self.solver.solution_alg = SOLUTION_ALG_BFS
		set_status_message(msg, self)

	def on_enter_room(self):
		if flags.is_reverse_barrel:
			barrel_cells = self.get_room_plate_cells()
			plate_cells = self.get_room_barrel_cells()
			for cell in plate_cells:
				if not cell in barrel_cells:
					self.map[cell] = CELL_PLATE
					barrels.remove(get_actor_on_cell(cell, barrels))
			for cell in barrel_cells:
				if not cell in plate_cells:
					self.map[cell] = self.Globals.get_random_floor_cell_type()
					create_barrel(cell)

		# prepare some invariant data
		self.num_total_cells = room.size_x * room.size_y
		self.plate_cells = self.get_room_plate_cells()
		self.has_extra_barrels = len(self.plate_cells) < len(barrels)
		self.has_extra_plates  = len(self.plate_cells) > len(barrels)

		self.num_moves = 0
		self.num_shifts = 0

		self.solver.reset_solution_data()
		self.check_special_setups()

	def get_room_plate_cells(self):
		return self.get_room_cells(CELL_PLATE)

	def get_room_barrels(self):
		return [ barrel for barrel in barrels if is_actor_in_room(barrel) ]

	def get_room_barrel_cells(self):
		return sort_cells([ barrel.c for barrel in self.get_room_barrels() ])

	def on_set_theme(self):
		self.red_floor_image = load_theme_cell_image('floor')
		self.red_floor_image.fill(MAIN_COLOR_RGB_VALUES[0], special_flags=pygame.BLEND_RGB_MULT)
		self.barrel_spinner = load_theme_cell_image("barrel")

	def on_load_map(self, special_cell_values, extra_values):
		self.area = room
		self.Globals.convert_outer_floors(CELL_VOID if game.level.bg_image else None)
		self.on_generate_map()

	def on_generate_map(self):
		self.Globals.convert_outer_walls(CELL_VOID if game.level.bg_image else None, True)

	def pull_barrel_randomly(self, barrel, visited_cell_pairs, num_moves):
		idx = barrels.index(barrel)
		weighted_neighbors = []
		# sort 4 barrel directions to place char to the "adjacent to barrel" cell for a pull (prefer empty cells)
		for c in self.Globals.get_actor_neighbors(barrel, self.area.x_range, self.area.y_range):
			if (c, char.c) in visited_cell_pairs:
				continue
			cx, cy = c
			if is_cell_in_actors(c, barrels):
				continue
			new_cx = cx + cx - barrel.cx
			new_cy = cy + cy - barrel.cy
			if new_cx not in self.area.x_range or new_cy not in self.area.y_range:
				continue
			if is_cell_in_actors((new_cx, new_cy), barrels):
				continue
			weight = randint(0, 30)
			if self.map[cx, cy] not in CELL_WALL_TYPES:
				weight += 20
			if self.map[cx, cy] == CELL_PLATE:
				weight += 4
			if self.map[new_cx, new_cy] not in CELL_WALL_TYPES:
				weight += 10
			if self.map[new_cx, new_cy] == CELL_PLATE:
				weight += 2
			weighted_neighbors.append((weight, c))

		neighbors = [n[1] for n in sorted(weighted_neighbors, reverse=True)]

		if not neighbors:
			# can't find free neighbor for barrel, stop
			debug(2, "barrel #%d - failed to find free neighbor for barrel %s (%d left)" % (idx, barrel.c, num_moves))
			return False

		for neighbor in neighbors:
			cx, cy = neighbor

			# if the cell is not empty (WALL), make it empty (FLOOR with additions)
			was_wall1_replaced = False
			if self.map[neighbor] == CELL_WALL:
				self.convert_to_floor(neighbor)
				was_wall1_replaced = True
			barrel_cx = barrel.cx
			barrel_cy = barrel.cy
			new_char_cx = cx + (cx - barrel_cx)
			new_char_cy = cy + (cy - barrel_cy)
			debug(2, "barrel #%d - neighbor %s, next cell (%d, %d)" % (idx, neighbor, new_char_cx, new_char_cy))
			self.Globals.debug_map(2, full=True, clean=True, dual=True)
			was_wall2_replaced = False
			if self.map[new_char_cx, new_char_cy] == CELL_WALL:
				self.convert_to_floor((new_char_cx, new_char_cy))
				was_wall2_replaced = True

			# if the char position is not None, first create random free path to the selected adjacent cell
			old_char_c = char.c
			if char.c is None:
				char.c = (cx, cy)
			if self.Globals.generate_random_free_path(char.c, neighbor):
				# pull the barrel to the char
				barrel.c = char.c
				char.c = (new_char_cx, new_char_cy)

				visited_cell_pairs.append((neighbor, char.c))

				if num_moves <= 1:
					return True

				if self.pull_barrel_randomly(barrel, visited_cell_pairs, num_moves - 1):
					return True
				else:
					debug(2, "barrel #%d - failed to pull barrel (%d moves left)" % (idx, num_moves - 1))
			else:
				debug(2, "barrel #%d - failed to generate random free path to neighbor %s" % (idx, neighbor))

			# can't create free path for char or can't pull barrel, restore the original state
			char.c = old_char_c
			barrel.c = (barrel_cx, barrel_cy)
			if was_wall1_replaced:
				self.map[cx, cy] = CELL_WALL
			if was_wall2_replaced:
				self.map[new_char_cx, new_char_cy] = CELL_WALL

		return False

	def generate_random_solvable_room(self):
		# 0) initialize char position to None
		char.c = None

		# 1) initialize entire room to WALL
		for cell in room.cells:
			self.map[cell] = CELL_WALL

		# 2) place room plates randomly or in good positions, as the number of barrels
		# 3) place room barrels into the place cells, one barrel per one plate
		for _ in range(self.num_barrels):
			cell = self.get_random_wall_cell_in_area()
			self.map[cell] = CELL_PLATE
			create_barrel(cell)

		# 4) for each area barrel do:
		for barrel in barrels:
			debug(2, "barrel #%d - starting (%d, %d)" % (barrels.index(barrel), barrel.cx, barrel.cy))
			visited_cell_pairs = [(barrel.c, char.c)]
			# 5) make random moves for the barrel until possible
			num_moves = randint(10, 80)
			self.pull_barrel_randomly(barrel, visited_cell_pairs, num_moves)
			debug(2, "barrel #%d - finished (%d, %d)" % (barrels.index(barrel), barrel.cx, barrel.cy))

		# 11) remember the char position, optionally try to move it as far left-top as possible
		if char.c is None:
			self.die("Failed to generate random solvable room")

		self.Globals.place_char_in_topleft_accessible_cell()
		game.set_char_cell(char.c)

	def cost_for_path(self, cell, parent_cell, visited_cells, start_cell, target_cell, obstacles, is_char):
		if not self.is_in_area(cell):
			return OBSTACLE_COST
		if cell in obstacles:
			return OBSTACLE_COST

		if self.map[cell] in CELL_WALL_TYPES:
			cost = WALL_COST
		else:
			cost = CHAR_FLOOR_COST if is_char else FLOOR_COST

		if not is_char:
			def get_cost(cell):
				return self.cost_for_path(cell, None, visited_cells, start_cell, target_cell, obstacles, True)

			# If the barrel path changed direction, then the char path should be added too.
			# There are always 2 possibilities for the char to walk around the barrel.
			if grand_parent_cell := (visited_cells.get(parent_cell) or [None])[0]:
				diff1 = cell_diff(cell, parent_cell)
				diff2 = cell_diff(parent_cell, grand_parent_cell)
				if diff1 != diff2:
					cell1 = apply_diff(grand_parent_cell, diff1)
					cell2 = apply_diff(parent_cell, diff1)
					cell3 = apply_diff(cell, diff2)
					cell4 = apply_diff(cell, diff2, factor=-1)
					cell5 = apply_diff(cell4, diff1)
					cell6 = apply_diff(cell5, diff1)

					cell1_cost = get_cost(cell1)
					cell2_cost = get_cost(cell2)
					cell3_cost = get_cost(cell3)
					cell4_cost = get_cost(cell4)
					cell5_cost = get_cost(cell5)
					cell6_cost = get_cost(cell6)

					if cell1_cost == OBSTACLE_COST or cell2_cost == OBSTACLE_COST:
						cost1 = OBSTACLE_COST
					else:
						cost1 = cell1_cost + cell2_cost
					if cell3_cost == OBSTACLE_COST or cell4_cost == OBSTACLE_COST or cell5_cost == OBSTACLE_COST or cell6_cost == OBSTACLE_COST or cell2_cost == OBSTACLE_COST:
						cost2 = OBSTACLE_COST
					else:
						cost2 = cell3_cost + cell4_cost + cell5_cost + cell6_cost + cell2_cost
					if cost1 == OBSTACLE_COST and cost2 == OBSTACLE_COST:
						return OBSTACLE_COST
					cost += cost1 if cost2 == OBSTACLE_COST or cost1 != OBSTACLE_COST and cost1 < cost2 else cost2

			else:
				prev_parent_cell = apply_diff(cell, cell_diff(cell, parent_cell), factor=2)
				cost1 = get_cost(prev_parent_cell)
				if cost1 == OBSTACLE_COST:
					return OBSTACLE_COST
				cost += cost1

		return cost

	def cost_for_barrel_path(self, cell, parent_cell, visited_cells, start_cell, target_cell, obstacles):
		return self.cost_for_path(cell, parent_cell, visited_cells, start_cell, target_cell, obstacles, False)

	def cost_for_char_path(self, cell, parent_cell, visited_cells, start_cell, target_cell, obstacles):
		return self.cost_for_path(cell, parent_cell, visited_cells, start_cell, target_cell, obstacles, True)

	def find_best_char_barrel_path(self, char_cell, barrel_plate_cell_pairs, placed_barrel_cells):
		best_path_cost = None
		best_path_values = (None, None, None, None)
		for barrel_cell, plate_cell in barrel_plate_cell_pairs:
			if barrel_cell == plate_cell:
				print("BUG. Barrel %s to be moved is already on its plate" % str(barrel_cell))
				continue
			other_barrel_cells = [_barrel_cell for _barrel_cell, _ in barrel_plate_cell_pairs if _barrel_cell != barrel_cell] + placed_barrel_cells
			# generate best barrel path to its plate
			barrel_path_cells = self.Globals.find_best_path(barrel_cell, plate_cell, obstacles=other_barrel_cells, allow_obstacles=True, cost_func=self.cost_for_barrel_path)
			if barrel_path_cells is None:
				continue
			new_char_cell = apply_diff(barrel_cell, cell_diff(barrel_cell, barrel_path_cells[0]), True)
			# generate best char path to the start of the best barrel path
			path_cost = [0]  # only remains 0 if the char should not be moved
			barrel_cells = other_barrel_cells + [barrel_cell]
			path_cells = self.Globals.find_best_path(char_cell, new_char_cell, obstacles=barrel_cells, allow_obstacles=True, cost_func=self.cost_for_char_path, set_path_cost=path_cost)
			if path_cells is not None and (best_path_cost is None or path_cost[0] < best_path_cost):
				best_path_cost = path_cost[0]
				best_path_values = (path_cells, barrel_path_cells, barrel_cell, plate_cell)

		return best_path_values

	def generate_char_and_barrel_paths_to_plates(self, char_cell, barrel_cells, plate_cells):
		unplaced_barrel_plate_cell_pairs = list(zip(barrel_cells, plate_cells))
		placed_barrel_cells = []

		self.convert_to_floor(char_cell)
		debug(2, "generate %s %s %s" % (str(char_cell), barrel_cells, plate_cells))
		self.Globals.debug_map(2)

		num_tries = 4000
		while num_tries > 0 and unplaced_barrel_plate_cell_pairs:
			path_cells, barrel_path_cells, barrel_cell, plate_cell = self.find_best_char_barrel_path(char_cell, unplaced_barrel_plate_cell_pairs, placed_barrel_cells)
			if not path_cells:
				break
			debug(2, "%s %s %s %s" % (path_cells, barrel_path_cells, str(barrel_cell), str(plate_cell)))

			unplaced_barrel_plate_cell_pairs.remove((barrel_cell, plate_cell))

			# remove walls on the char path
			for cell in path_cells:
				if self.map[cell] in CELL_WALL_TYPES:
					self.convert_to_floor(cell)

			# remove walls on the barrel path until the first direction change
			char_cell = path_cells[-1]
			char_dir = cell_diff(char_cell, barrel_cell)
			for cell in barrel_path_cells:
				if self.map[barrel_cell] in CELL_WALL_TYPES:
					self.convert_to_floor(barrel_cell)
				if cell_diff(barrel_cell, cell) != char_dir:
					break
				char_cell = barrel_cell
				barrel_cell = cell

			if barrel_cell != plate_cell:
				unplaced_barrel_plate_cell_pairs.append((barrel_cell, plate_cell))
			else:
				placed_barrel_cells.append(barrel_cell)

			debug(2, "%s %s" % (str(char_cell), str(barrel_cell)))
			self.Globals.debug_map(2)

			num_tries -= 1

		return not unplaced_barrel_plate_cell_pairs

	def generate_ng_random_solvable_room(self):
		num_tries = 2000

		while num_tries > 0:
			barrel_cells = []
			plate_cells = []

			# 1) initialize entire room to WALL
			for cell in room.cells:
				self.map[cell] = CELL_WALL

			# 2) place room plates randomly or in good positions, as the number of barrels
			for _ in range(self.num_barrels):
				cell = self.get_random_wall_cell_in_area()
				self.map[cell] = CELL_PLATE
				plate_cells.append(cell)

			# 3) place room barrels into the place cells, one barrel per one plate
			for _ in range(self.num_barrels):
				cell = self.get_random_wall_cell_in_area()
				self.convert_to_floor(cell)
				barrel_cells.append(cell)

			# 4) place char randomly
			char_cell = self.get_random_wall_cell_in_area()

			# 5) remove some cells from being used in generation
			excluded_cells = set()
			for _ in range(randint(-2, 4)):
				excluded_cells.add(self.get_random_wall_cell_in_area(excluded_cells))

			# 6) generate routes from each barrel and its plate by removing walls
			if self.generate_char_and_barrel_paths_to_plates(char_cell, barrel_cells, plate_cells):
				# optionally optimize level

				for cell in barrel_cells:
					create_barrel(cell)
				game.set_char_cell(char_cell)
				self.Globals.debug_map(2)
				return

			num_tries -= 1

		warn("Can't generate barrel level, making it solved")
		for cell in self.get_room_plate_cells():
			create_barrel(cell)

	def generate_room(self):
		self.num_barrels = self.parse_config_num("num_barrels", DEFAULT_NUM_BARRELS)
		self.set_area_from_config(default_size=DEFAULT_BARREL_PUZZLE_SIZE, align_to_center=True)

		if self.config.get("zsb"):
			self.generate_random_zsb_room()
		elif self.config.get("use_ng"):
			self.generate_ng_random_solvable_room()
		else:
			self.generate_random_solvable_room()

	def is_solved_for_barrel_cells(self, barrel_cells):
		return \
			len([cell for cell in barrel_cells if cell in self.plate_cells]) == len(barrel_cells) \
			if self.has_extra_plates else \
			len([cell for cell in self.plate_cells if cell in barrel_cells]) == len(self.plate_cells)

	def is_solved(self):
		return game.in_level and self.num_shifts and self.is_solved_for_barrel_cells([ barrel.c for barrel in self.get_room_barrels() ])

	def get_cell_image_to_draw(self, cell, cell_type):
		if cell_type == CELL_FLOOR and grid.is_dead_barrel(cell):
			return self.red_floor_image

	def on_press_key(self, keyboard):
		if keyboard.ralt and not solution.is_find_mode():
			if keyboard.a:
				self.solver.solution_alg = SOLUTION_ALG_ASTAR
			if keyboard.b:
				self.solver.solution_alg = SOLUTION_ALG_BFS
			if keyboard.d:
				self.solver.solution_alg = SOLUTION_ALG_DFS
			if keyboard.p:
				self.solver.solution_alg = SOLUTION_ALG_PQ
			if keyboard.minus:
				self.solver.disable_prepare = not self.solver.disable_prepare
			if keyboard.k_0:
				self.solver.disable_budget = not self.solver.disable_budget
			msg = "Going to use solution algorithm %s; budget of 1s is %s; prepare is %s" % (self.solver.solution_alg,
				("disabled" if self.solver.disable_budget else "enabled"),
				("disabled" if self.solver.disable_prepare else "enabled"),
			)
			set_status_message(msg, self, None, 4)
			return
		if keyboard.e and keyboard.alt:
			game.level.reverse_barrel_mode = not game.level.reverse_barrel_mode
			game.set_requested_new_level(None, True)
		if keyboard.kp_enter:
			if solution.is_active() and ((self.solver.solution_type == SOLUTION_TYPE_BY_MOVES) ^ keyboard.shift):
				solution.reset()
			if not solution.is_active() and not solution.is_find_mode():
				self.solver.solution_type = SOLUTION_TYPE_BY_MOVES if keyboard.shift else SOLUTION_TYPE_BY_SHIFTS

	def on_enter_cell(self):
		game.remember_obj_state(self)
		self.num_moves += 1
		self.num_shifts += game.last_char_move.is_barrel_shift

	def on_draw(self):
		game.screen.draw.text("%d/%d" % (self.num_moves, self.num_shifts), center=(CELL_W * 1.5, CELL_H * 0.5), color="#00FFAA", gcolor="#00AA66", owidth=1.6, ocolor="#3A4440", alpha=1, fontsize=27)

	def get_state(self):
		return (self.num_moves, self.num_shifts)

	def restore_state(self, state):
		(self.num_moves, self.num_shifts) = state

	def find_solution_func(self):
		solution_items, msg = self.solver.find_solution_func(solution.stop_find)
		return solution_items, (msg, self.barrel_spinner) if msg else None

	def prepare_solution(self):
		self.solver.configure(game.map, flags.is_reverse_barrel, char.c, tuple(self.get_room_barrel_cells()))
		return ("Preparing to find solution", self.find_solution_func)

