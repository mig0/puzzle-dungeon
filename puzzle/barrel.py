from . import *

SHOW_DEADLOCK_MAPS = False
DEBUG_FIND_SOLUTION = False
MIN_SOLUTION_DEPTH = 8
MAX_SOLUTION_DEPTH = 200
SOLUTION_DEPTH_STEP = 4

FLOOR_COST = 1
CHAR_FLOOR_COST = -1
WALL_COST = 100
OBSTACLE_COST = None

class BarrelPuzzle(Puzzle):
	def init(self):
		self.solution = None
		self.solution_depth = None
		self.show_solution_mode = False
		self.find_solution_mode = 0

	def assert_config(self):
		return not flags.is_any_maze

	def has_plate(self):
		return True

	def is_long_generation(self):
		return True

	def is_goal_to_be_solved(self):
		return True

	def on_enter_room(self):
		self.num_total_cells = self.room.size_x * self.room.size_y

	def get_room_plate_cells(self):
		return [ tuple(cell) for cell in argwhere(self.map == CELL_PLATE) if self.Globals.is_cell_in_room(cell) ]

	def get_room_barrels(self):
		return [ barrel for barrel in barrels if self.Globals.is_actor_in_room(barrel) ]

	def show_map(self, descr=None, char_cell=None, barrel_cells=None):
		orig_barrels = barrels.copy()
		barrels.clear()
		for cell in barrel_cells or self.barrel_cells:
			self.Globals.create_barrel(cell)
		orig_char_cell = char.c
		char.c = char_cell or self.char_cell
		self.Globals.debug_map(descr=descr)
		barrels.clear()
		barrels.extend(orig_barrels)
		char.c = orig_char_cell

	def show_deadlock_map(self, char_cell, barrel_cell, cell1, cell2, cell3, cell4):
		if not SHOW_DEADLOCK_MAPS:
			return
		barrel_cells = self.barrel_cells.copy()
		barrel_cells.remove(barrel_cell)
		barrel_cells.append(cell1)
		self.show_map("deadlock: %s -> %s -> %s %s %s %s" % (char_cell, barrel_cell, cell1, cell2, cell3, cell4), barrel_cell, barrel_cells)

	def is_2x2_deadlock(self, cell1, cell2, cell3, cell4):
		barrel_cells = []
		for cell in cell2, cell3, cell4:
			if cell in self.barrel_cells:
				barrel_cells.append(cell)
			elif self.is_in_room(cell) and self.map[cell] not in CELL_CHAR_MOVE_OBSTACLES:
				return False

		for barrel_cell in barrel_cells + [cell1]:
			if self.map[barrel_cell] != CELL_PLATE:
				return True
		return False

	def try_push(self, char_cell, barrel_cell):
		diff = cell_diff(char_cell, barrel_cell)
		next_barrel_cell = apply_diff(barrel_cell, diff)
		if not self.is_in_room(next_barrel_cell) or self.map[next_barrel_cell] in CELL_CHAR_MOVE_OBSTACLES or next_barrel_cell in self.barrel_cells:
			return None

		# eliminate deadlocks
		next_f_barrel_cell = apply_diff(next_barrel_cell, diff)

		next_l_barrel_cell = apply_diff(next_barrel_cell, (-1, 0) if diff in ((0, -1), (0, +1)) else (0, -1))
		next_lf_barrel_cell = apply_diff(next_l_barrel_cell, diff)
		if self.is_2x2_deadlock(next_barrel_cell, next_l_barrel_cell, next_lf_barrel_cell, next_f_barrel_cell):
			self.show_deadlock_map(char_cell, barrel_cell, next_barrel_cell, next_l_barrel_cell, next_lf_barrel_cell, next_f_barrel_cell)
			return None

		next_r_barrel_cell = apply_diff(next_barrel_cell, (+1, 0) if diff in ((0, -1), (0, +1)) else (0, +1))
		next_rf_barrel_cell = apply_diff(next_r_barrel_cell, diff)
		if self.is_2x2_deadlock(next_barrel_cell, next_r_barrel_cell, next_rf_barrel_cell, next_f_barrel_cell):
			self.show_deadlock_map(char_cell, barrel_cell, next_barrel_cell, next_r_barrel_cell, next_rf_barrel_cell, next_f_barrel_cell)
			return None

		return next_barrel_cell

	def can_push(self, char_cell, barrel_cell):
		return self.try_push(char_cell, barrel_cell) is not None

	def push(self, char_cell, barrel_cell):
		next_barrel_cell = self.try_push(char_cell, barrel_cell)
		self.barrel_cells.remove(barrel_cell)
		self.barrel_cells.append(next_barrel_cell)
		self.barrel_cells.sort()
		self.char_cell = barrel_cell
		return next_barrel_cell

	def get_barrel_plate_distance(self, char_cell, barrel_cell, plate_cell):
		char_path = self.Globals.find_path(barrel_cell, plate_cell, self.barrel_cells)
		return len(char_path) + 1 if char_path is not None else None

	def get_barrel_distance_weight(self, char_cell, barrel_cell):
		orig_barrel_cells = self.barrel_cells.copy()
		orig_char_cell = self.char_cell

		barrel_cell = self.push(char_cell, barrel_cell)

		min_num_pushes = self.num_total_cells
		for plate_cell in self.plate_cells:
			num_pushes = self.get_barrel_plate_distance(self.char_cell, barrel_cell, plate_cell) or self.num_total_cells
			if num_pushes < min_num_pushes:
				min_num_pushes = num_pushes

		self.barrel_cells = orig_barrel_cells
		self.char_cell = orig_char_cell

		return min_num_pushes

	def find_solution(self, init=True, solution_depth=None):
		if init:
			self.solution_depth = solution_depth or MIN_SOLUTION_DEPTH
			self.solution = []
			self.char_cell = char.c
			self.plate_cells = [tuple(cell) for cell in argwhere(self.map == CELL_PLATE) ]
			self.plate_cells.sort()
			self.barrel_cells = [ barrel.c for barrel in self.get_room_barrels() ]
			self.barrel_cells.sort()
			self.has_extra_barrels = len(self.plate_cells) < len(self.barrel_cells)
			self.has_extra_plates  = len(self.plate_cells) > len(self.barrel_cells)
			self.visited_positions = []

		if self.plate_cells == self.barrel_cells \
			or self.has_extra_barrels and all(cell in self.barrel_cells for cell in self.plate_cells) \
			or self.has_extra_plates  and all(cell in self.plate_cells for cell in self.barrel_cells):
			return True

		if len(self.solution) >= self.solution_depth:
			return False

		accessible_cells = self.Globals.get_accessible_cells(self.char_cell, self.barrel_cells)
		accessible_cells.sort()

		position_id = [ *accessible_cells, None, *self.barrel_cells ]
		if position_id in self.visited_positions:
			return False
		self.visited_positions.append(position_id)

		accessible_cells_near_barrels = [ (cell, barrel_cell) for cell in accessible_cells for barrel_cell in self.barrel_cells if cell_distance(cell, barrel_cell) == 1 and self.can_push(cell, barrel_cell) ]

		accessible_cells_near_barrels.sort(key=lambda cell_pair: self.get_barrel_distance_weight(*cell_pair))

		for cell, barrel_cell in accessible_cells_near_barrels:
			if DEBUG_FIND_SOLUTION:
				print("%s%s -> %s" % (" " * len(self.solution), cell, barrel_cell))
			old_barrel_cells = self.barrel_cells.copy()
			old_char_cell = self.char_cell

			char_path = self.Globals.find_path(self.char_cell, cell, self.barrel_cells)
			self.push(cell, barrel_cell)

			self.solution.append(char_path + [barrel_cell])
			if self.find_solution(init=False):
				return True
			self.solution.pop()

			self.barrel_cells = old_barrel_cells
			self.char_cell = old_char_cell

		return False

	def on_load_map(self, special_cell_values, extra_values):
		self.Globals.convert_outer_floors(CELL_VOID if "bg_image" in self.level else None)
		self.on_generate_map()

	def on_generate_map(self):
		self.Globals.convert_outer_walls(CELL_VOID if "bg_image" in self.level else None)

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
			self.Globals.debug(2, "barrel #%d - failed to find free neighbor for barrel %s (%d left)" % (idx, barrel.c, num_moves))
			return False

		for neighbor in neighbors:
			cx, cy = neighbor

			# if the cell is not empty (WALL), make it empty (FLOOR with additions)
			was_wall1_replaced = False
			if self.map[cx, cy] == CELL_WALL:
				self.Globals.convert_to_floor_if_needed(cx, cy)
				was_wall1_replaced = True
			barrel_cx = barrel.cx
			barrel_cy = barrel.cy
			new_char_cx = cx + (cx - barrel_cx)
			new_char_cy = cy + (cy - barrel_cy)
			self.Globals.debug(2, "barrel #%d - neighbor %s, next cell (%d, %d)" % (idx, neighbor, new_char_cx, new_char_cy))
			self.Globals.debug_map(2, full=True, clean=True, dual=True)
			was_wall2_replaced = False
			if self.map[new_char_cx, new_char_cy] == CELL_WALL:
				self.Globals.convert_to_floor_if_needed(new_char_cx, new_char_cy)
				was_wall2_replaced = True

			# if the char position is not None, first create random free path to the selected adjacent cell
			old_char_c = char.c
			if char.c is None:
				char.c = (cx, cy)
			if self.Globals.generate_random_free_path(neighbor):
				# pull the barrel to the char
				barrel.c = char.c
				char.c = (new_char_cx, new_char_cy)

				visited_cell_pairs.append((neighbor, char.c))

				if num_moves <= 1:
					return True

				if self.pull_barrel_randomly(barrel, visited_cell_pairs, num_moves - 1):
					return True
				else:
					self.Globals.debug(2, "barrel #%d - failed to pull barrel (%d moves left)" % (idx, num_moves - 1))
			else:
				self.Globals.debug(2, "barrel #%d - failed to generate random free path to neighbor %s" % (idx, neighbor))

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
		for cell in self.room.cells:
			self.map[cell] = CELL_WALL

		# 2) place room plates randomly or in good positions, as the number of barrels
		# 3) place room barrels into the place cells, one barrel per one plate
		for _ in range(self.num_barrels):
			cell = self.get_random_wall_cell_in_area()
			self.map[cell] = CELL_PLATE
			self.Globals.create_barrel(cell)

		# 4) for each area barrel do:
		for barrel in barrels:
			self.Globals.debug(2, "barrel #%d - starting (%d, %d)" % (barrels.index(barrel), barrel.cx, barrel.cy))
			visited_cell_pairs = [(barrel.c, char.c)]
			# 5) make random moves for the barrel until possible
			num_moves = randint(10, 80)
			self.pull_barrel_randomly(barrel, visited_cell_pairs, num_moves)
			self.Globals.debug(2, "barrel #%d - finished (%d, %d)" % (barrels.index(barrel), barrel.cx, barrel.cy))

		# 11) remember the char position, optionally try to move it as far left-top as possible
		if char.c is None:
			print("Failed to generate random solvable barrel room")
			if DEBUG_LEVEL:
				return
			else:
				quit()

		self.Globals.place_char_in_topleft_accessible_cell()
		self.Globals.set_char_cell(char.c)

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

		self.map[char_cell] = self.Globals.get_random_floor_cell_type()
		self.Globals.debug(2, "generate %s %s %s" % (str(char_cell), barrel_cells, plate_cells))
		self.Globals.debug_map(2)

		num_tries = 4000
		while num_tries > 0 and unplaced_barrel_plate_cell_pairs:
			path_cells, barrel_path_cells, barrel_cell, plate_cell = self.find_best_char_barrel_path(char_cell, unplaced_barrel_plate_cell_pairs, placed_barrel_cells)
			if not path_cells:
				break
			self.Globals.debug(2, "%s %s %s %s" % (path_cells, barrel_path_cells, str(barrel_cell), str(plate_cell)))

			unplaced_barrel_plate_cell_pairs.remove((barrel_cell, plate_cell))

			# remove walls on the char path
			for cell in path_cells:
				if self.map[cell] in CELL_WALL_TYPES:
					self.map[cell] = self.Globals.get_random_floor_cell_type()

			# remove walls on the barrel path until the first direction change
			char_cell = path_cells[-1]
			char_dir = cell_diff(char_cell, barrel_cell)
			for cell in barrel_path_cells:
				if self.map[barrel_cell] in CELL_WALL_TYPES:
					self.map[barrel_cell] = self.Globals.get_random_floor_cell_type()
				if cell_diff(barrel_cell, cell) != char_dir:
					break
				char_cell = barrel_cell
				barrel_cell = cell

			if barrel_cell != plate_cell:
				unplaced_barrel_plate_cell_pairs.append((barrel_cell, plate_cell))
			else:
				placed_barrel_cells.append(barrel_cell)

			self.Globals.debug(2, "%s %s" % (str(char_cell), str(barrel_cell)))
			self.Globals.debug_map(2)

			num_tries -= 1

		return not unplaced_barrel_plate_cell_pairs

	def generate_ng_random_solvable_room(self):
		num_tries = 2000

		while num_tries > 0:
			barrel_cells = []
			plate_cells = []

			# 1) initialize entire room to WALL
			for cell in self.room.cells:
				self.map[cell] = CELL_WALL

			# 2) place room plates randomly or in good positions, as the number of barrels
			for _ in range(self.num_barrels):
				cell = self.get_random_wall_cell_in_area()
				self.map[cell] = CELL_PLATE
				plate_cells.append(cell)

			# 3) place room barrels into the place cells, one barrel per one plate
			for _ in range(self.num_barrels):
				cell = self.get_random_wall_cell_in_area()
				self.map[cell] = self.Globals.get_random_floor_cell_type()
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
					self.Globals.create_barrel(cell)
				self.Globals.set_char_cell(char_cell)
				self.Globals.debug_map(2)
				return

			num_tries -= 1

		self.Globals.debug(0, "Can't generate barrel level, making it solved")
		for cell in self.get_room_cells(CELL_PLATE):
			self.Globals.create_barrel(cell)

	def generate_room(self):
		self.num_barrels = self.parse_config_num("num_barrels", DEFAULT_NUM_BARRELS)
		self.set_area_from_config(default_size=DEFAULT_BARREL_PUZZLE_SIZE, align_to_center=True)

		if self.config.get("use_ng"):
			self.generate_ng_random_solvable_room()
		else:
			self.generate_random_solvable_room()

	def is_solved(self):
		plate_cells = self.get_room_plate_cells()
		barrel_cells = [ barrel.c for barrel in self.get_room_barrels() ]
		if len(plate_cells) >= len(barrel_cells):
			is_solved = len([cell for cell in barrel_cells if cell in plate_cells]) == len(barrel_cells)
		else:
			is_solved = len([cell for cell in plate_cells if cell in barrel_cells]) == len(plate_cells)
		return is_solved

	def on_draw(self, mode):
		if self.find_solution_mode:
			solution_depth = self.solution_depth + SOLUTION_DEPTH_STEP if self.solution_depth else MIN_SOLUTION_DEPTH
			if solution_depth > MAX_SOLUTION_DEPTH:
				set_status_message("Failed to find solution", self, 0)
				self.find_solution_mode = 0
				return
			if self.find_solution_mode == 1:
				set_status_message("Finding solution with depth %d…" % solution_depth, self, 0)
			if self.find_solution_mode <= 2:
				self.find_solution_mode += 1
				return
			is_found = self.find_solution(True, solution_depth)
			if is_found:
				set_status_message("Found solution with %d pushes, press again to view" % len(self.solution), self, 0)
				self.solution = [cell for cells in self.solution for cell in cells]
				self.find_solution_mode = 0
			else:
				self.find_solution_mode = 1

	def on_press_key(self, keyboard):
		if keyboard.kp_enter:
			set_status_message(None, self)
			if self.show_solution_mode:
				self.show_solution_mode = False
				return
			if self.solution is not None:
				set_status_message(None, self, 0)
				self.solution_time = 0
				self.show_solution_mode = True
				return
			self.solution_depth = None
			self.find_solution_mode = 1
		else:
			if self.show_solution_mode:
				set_status_message(None, self)
				self.show_solution_mode = False
				self.solution = None

	def on_update(self, level_time):
		if self.show_solution_mode:
			if level_time > self.solution_time:
				if self.solution:
					new_cell = self.solution[0]
					dx, dy = cell_diff(char.c, new_cell)
					self.Globals.move_char(dx, dy)
					if char.c == new_cell:
						set_status_message("Number of moves left until solved: %d" % len(self.solution), self)
						self.solution.pop(0)
					self.solution_time = level_time + BARREL_PUZZLE_SOLUTION_MOVE_DELAY
				else:
					set_status_message(None, self)
					self.show_solution_mode = False
					self.solution = None
					self.solution_depth = None
