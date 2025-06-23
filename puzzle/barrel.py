from . import *

SHOW_DEADLOCK_MAPS = False
DEBUG_FIND_SOLUTION = False
MIN_SOLUTION_DEPTH = 8
MAX_SOLUTION_DEPTH = 200
SOLUTION_DEPTH_STEP = 4
MAX_PREPARE_SOLUTION_TIME = 8
MAX_FIND_SOLUTION_TIME = 25 * 60 * 60

FLOOR_COST = 1
CHAR_FLOOR_COST = -1
WALL_COST = 100
OBSTACLE_COST = None

class BarrelPuzzle(Puzzle):
	def init(self):
		self.disable_prepare_solution = False

	def assert_config(self):
		return not flags.is_any_maze

	def has_plate(self):
		return True

	def is_long_generation(self):
		return True

	def is_goal_to_be_solved(self):
		return True

	def reset_solution_data(self):
		self.min_char_barrel_plate_pushes = None
		self.min_barrel_plate_pushes = None
		self.solution = None
		self.solution_depth = None
		self.end_solution_time = 99999999999

	def on_enter_room(self):
		# prepare some invariant data
		self.num_total_cells = room.size_x * room.size_y
		self.plate_cells = [ tuple(cell) for cell in argwhere(self.map == CELL_PLATE) if is_cell_in_room(cell) ]
		self.plate_cells.sort()
		self.stock_barrel_cells = [ barrel.c for barrel in self.get_room_barrels() ]
		self.stock_barrel_cells.sort()
		self.has_extra_barrels = len(self.plate_cells) < len(barrels)
		self.has_extra_plates  = len(self.plate_cells) > len(barrels)

		self.reset_solution_data()

	def get_room_barrels(self):
		return [ barrel for barrel in barrels if is_actor_in_room(barrel) ]

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
		new_barrel_cell = apply_diff(barrel_cell, diff)

		if not self.is_in_room(new_barrel_cell) or self.map[new_barrel_cell] in CELL_CHAR_MOVE_OBSTACLES or new_barrel_cell in self.barrel_cells:
			return None

		if self.min_char_barrel_plate_pushes is not None and new_barrel_cell not in self.plate_cells and (char_cell, barrel_cell) not in self.min_char_barrel_plate_pushes:
			return None

		# eliminate deadlocks
		new_barrel_f_cell = apply_diff(new_barrel_cell, diff)

		new_barrel_l_cell = apply_diff(new_barrel_cell, (-1, 0) if diff in ((0, -1), (0, +1)) else (0, -1))
		new_barrel_lf_cell = apply_diff(new_barrel_l_cell, diff)
		if self.is_2x2_deadlock(new_barrel_cell, new_barrel_l_cell, new_barrel_lf_cell, new_barrel_f_cell):
			self.show_deadlock_map(char_cell, barrel_cell, new_barrel_cell, new_barrel_l_cell, new_barrel_lf_cell, new_barrel_f_cell)
			return None

		new_barrel_r_cell = apply_diff(new_barrel_cell, (+1, 0) if diff in ((0, -1), (0, +1)) else (0, +1))
		new_barrel_rf_cell = apply_diff(new_barrel_r_cell, diff)
		if self.is_2x2_deadlock(new_barrel_cell, new_barrel_r_cell, new_barrel_rf_cell, new_barrel_f_cell):
			self.show_deadlock_map(char_cell, barrel_cell, new_barrel_cell, new_barrel_r_cell, new_barrel_rf_cell, new_barrel_f_cell)
			return None

		return new_barrel_cell

	def can_push(self, char_cell, barrel_cell):
		return self.try_push(char_cell, barrel_cell) is not None

	def push(self, char_cell, barrel_cell):
		new_barrel_cell = self.try_push(char_cell, barrel_cell)
		self.barrel_cells.remove(barrel_cell)
		self.barrel_cells.append(new_barrel_cell)
		self.barrel_cells.sort()
		self.char_cell = barrel_cell
		return new_barrel_cell

	def try_pull(self, char_cell, barrel_cell):
		diff = cell_diff(barrel_cell, char_cell)
		new_char_cell = apply_diff(char_cell, diff)
		if not self.is_in_room(new_char_cell) or self.map[new_char_cell] in CELL_CHAR_MOVE_OBSTACLES or new_char_cell in self.barrel_cells:
			return None

		return new_char_cell

	def can_pull(self, char_cell, barrel_cell):
		return self.try_pull(char_cell, barrel_cell) is not None

	def pull(self, char_cell, barrel_cell):
		new_char_cell = self.try_pull(char_cell, barrel_cell)
		self.barrel_cells.remove(barrel_cell)
		self.barrel_cells.append(char_cell)
		self.barrel_cells.sort()
		self.char_cell = new_char_cell
		return new_char_cell

	def get_barrel_plate_distance(self, char_cell, barrel_cell, plate_cell):
		char_path = self.Globals.find_path(barrel_cell, plate_cell, self.barrel_cells)
		return len(char_path) + 1 if char_path is not None else None

	def get_barrel_distance_weight(self, char_cell, barrel_cell):
		if (char_cell, barrel_cell) in self.min_char_barrel_plate_pushes:
			return self.min_char_barrel_plate_pushes[char_cell, barrel_cell]

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

	def estimate_solution_depth(self):
		if not self.min_char_barrel_plate_pushes:
			return None

		solution_depth = 0
		for barrel_cell in self.stock_barrel_cells:
			num_pushes = self.min_barrel_plate_pushes[min(self.min_barrel_plate_pushes.keys(), key=lambda cell:
				self.min_barrel_plate_pushes[cell] if cell == barrel_cell else self.num_total_cells
			)]
			solution_depth += num_pushes

		return ((solution_depth - 1) // SOLUTION_DEPTH_STEP + 1) * SOLUTION_DEPTH_STEP

	def prepare_to_find_solution(self):
		self.min_char_barrel_plate_pushes = {}
		self.min_barrel_plate_pushes = {}
		if self.disable_prepare_solution:
			return

		all_char_barrel_plate_pushes = {}
		all_barrel_plate_pushes = {}

		for plate_cell in self.plate_cells:
			char_barrel_plate_pushes, barrel_plate_pushes = self.find_solvable_cells_for_plate_cells([plate_cell])
			for pair in char_barrel_plate_pushes:
				if pair not in all_char_barrel_plate_pushes:
					all_char_barrel_plate_pushes[pair] = []
				all_char_barrel_plate_pushes[pair].append(char_barrel_plate_pushes[pair])
			for cell in barrel_plate_pushes:
				if cell not in all_barrel_plate_pushes:
					all_barrel_plate_pushes[cell] = []
				all_barrel_plate_pushes[cell].append(barrel_plate_pushes[cell])

		for pair in all_char_barrel_plate_pushes:
			self.min_char_barrel_plate_pushes[pair] = min(all_char_barrel_plate_pushes[pair])
		for cell in all_barrel_plate_pushes:
			self.min_barrel_plate_pushes[cell] = min(all_barrel_plate_pushes[cell])
#		print(self.min_barrel_plate_pushes)
#		print(self.min_char_barrel_plate_pushes)

	def find_solvable_cells_for_plate_cells(self, plate_cells):
		start_time = time()
		min_char_barrel_plate_pushes = {}
		min_barrel_plate_pushes = {}
		visited_positions = []

		# start from plates and make all available pulls using BFS
		states = { 0: [] }

		last_barrel_cells = plate_cells.copy()
		self.barrel_cells = last_barrel_cells.copy()
		for barrel_cell in last_barrel_cells:
			for char_cell in self.Globals.get_accessible_neighbors(barrel_cell, self.barrel_cells):
				if self.can_pull(char_cell, barrel_cell):
					new_char_cell = self.pull(char_cell, barrel_cell)
					new_barrel_cell = char_cell
					states[0].append((new_char_cell, new_barrel_cell, self.barrel_cells, None))
					self.barrel_cells = last_barrel_cells.copy()
					min_char_barrel_plate_pushes[new_char_cell, new_barrel_cell] = 1
					min_barrel_plate_pushes[new_barrel_cell] = 1

		stop = False
		for depth in range(1, MAX_SOLUTION_DEPTH + 1):
			if stop:
				break
			# for each (char_cell, barrel_cell) from depth-1 do all possible next pulls and save as new states
			states[depth] = []
			min_pushes_updated = False
			for state in states[depth - 1]:
				if time() - start_time > MAX_PREPARE_SOLUTION_TIME:
					stop = True
					break
				last_char_cell, last_barrel_cell, last_barrel_cells, prev_state = state
				if (last_char_cell, last_barrel_cells) in visited_positions:
					break
				visited_positions.append((last_char_cell, last_barrel_cells))
				self.barrel_cells = last_barrel_cells.copy()

				if self.barrel_cells == self.stock_barrel_cells and self.Globals.find_path(last_char_cell, self.stock_char_cell, self.barrel_cells):
#					print("Found solution by pulls")
					self.solution = []
					orig_char_cell = self.stock_char_cell
					while True:
						char_path = self.Globals.find_path(orig_char_cell, last_char_cell, self.barrel_cells)
#						print(char_path + [last_barrel_cell])
						self.solution.append(char_path + [last_barrel_cell])
						if prev_state is None:
							break
						orig_char_cell = last_barrel_cell
						last_char_cell, last_barrel_cell, self.barrel_cells, prev_state = prev_state
					stop = True
					break

				for barrel_cell in last_barrel_cells:
					for char_cell in self.Globals.get_accessible_neighbors(barrel_cell, self.barrel_cells):
						if self.Globals.find_path(last_char_cell, char_cell, self.barrel_cells) is None:
							continue
						new_char_cell = self.try_pull(char_cell, barrel_cell)
						if new_char_cell is not None:
							new_barrel_cell = char_cell
							self.pull(char_cell, barrel_cell)
							states[depth].append((new_char_cell, new_barrel_cell, self.barrel_cells, state))
							self.barrel_cells = last_barrel_cells.copy()
							if (new_char_cell, new_barrel_cell) not in min_char_barrel_plate_pushes:
								min_char_barrel_plate_pushes[new_char_cell, new_barrel_cell] = depth + 1
								min_pushes_updated = True
								if new_barrel_cell not in min_barrel_plate_pushes:
									min_barrel_plate_pushes[new_barrel_cell] = depth + 1
			if not min_pushes_updated:
				stop = True
				break

#		print("find_solvable_cells_for_plate_cells finished in %.1fs for %d plates %s" % (time() - start_time, len(plate_cells), str(plate_cells)))
#		print("  Unique barrel cells: %d, pairs: %d" % (len(min_barrel_plate_pushes), len(min_char_barrel_plate_pushes)))
#		print("  %s" % str(min_barrel_plate_pushes))
#		print("  %s" % str(min_char_barrel_plate_pushes))

		return min_char_barrel_plate_pushes, min_barrel_plate_pushes

	def find_reverse_solution(self):
		if self.disable_prepare_solution:
			return

		if self.has_extra_plates:
			print("Don't know what to do when there are more plates than barrels, trying to find solution when last plates are unused")
			for _ in range(len(self.plate_cells) - len(barrels)):
				self.plate_cells.pop()

		self.min_char_barrel_plate_pushes, self.min_barrel_plate_pushes = self.find_solvable_cells_for_plate_cells(self.plate_cells)

	def find_solution(self, init=True):
		if init:
			self.solution = []
			self.char_cell = self.stock_char_cell
			self.barrel_cells = self.stock_barrel_cells.copy()
			self.barrel_cells.sort()
			self.visited_positions = []
			self.end_solution_time = time() + MAX_FIND_SOLUTION_TIME

		if self.is_solved_for_barrel_cells(self.barrel_cells):
			return True

		if len(self.solution) >= self.solution_depth:
			return False

		if time() > self.end_solution_time:
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

		if init:
			self.solution = None
		return False

	def on_set_theme(self):
		self.red_floor_image = load_theme_cell_image('floor')
		self.red_floor_image.fill(MAIN_COLOR_RGB_VALUES[0], special_flags=pygame.BLEND_RGB_MULT)

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
			self.Globals.create_barrel(cell)

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
					self.Globals.create_barrel(cell)
				self.Globals.set_char_cell(char_cell)
				self.Globals.debug_map(2)
				return

			num_tries -= 1

		debug(0, "Can't generate barrel level, making it solved")
		for cell in self.get_room_cells(CELL_PLATE):
			self.Globals.create_barrel(cell)

	def generate_room(self):
		self.num_barrels = self.parse_config_num("num_barrels", DEFAULT_NUM_BARRELS)
		self.set_area_from_config(default_size=DEFAULT_BARREL_PUZZLE_SIZE, align_to_center=True)

		if self.config.get("use_ng"):
			self.generate_ng_random_solvable_room()
		else:
			self.generate_random_solvable_room()

	def is_solved_for_barrel_cells(self, barrel_cells):
		return \
			len([cell for cell in barrel_cells if cell in self.plate_cells]) == len(barrel_cells) \
			if self.has_extra_plates else \
			len([cell for cell in self.plate_cells if cell in barrel_cells]) == len(self.plate_cells)

	def is_solved(self):
		return self.is_solved_for_barrel_cells([ barrel.c for barrel in self.get_room_barrels() ])

	def get_cell_image_to_draw(self, cell, cell_type):
		if cell_type in CELL_FLOOR_TYPES and self.min_barrel_plate_pushes is not None and cell not in self.min_barrel_plate_pushes:
			return self.red_floor_image

	def on_press_key(self, keyboard):
		if keyboard.d:
			self.disable_prepare_solution = not self.disable_prepare_solution
			set_status_message("Prepare solution is %s" % ("disabled" if self.disable_prepare_solution else "enabled"), self, None, 4)

	def find_solution_func(self):
		self.stock_char_cell = char.c
		if self.min_barrel_plate_pushes is None:
			# preparing to find solution
			self.prepare_to_find_solution()
			self.solution_depth = self.estimate_solution_depth() or MIN_SOLUTION_DEPTH
			return None, "Finding solution with depth %d…" % self.solution_depth

		if self.solution_depth > MAX_SOLUTION_DEPTH or time() > self.end_solution_time:
			# solution not found
			self.reset_solution_data()
			return None, None

		if self.find_solution(True):
			# solution found
			solution_items = self.solution.copy()
			self.reset_solution_data()
			return solution_items, None
		else:
			# solution in progress
			self.solution_depth += SOLUTION_DEPTH_STEP
			return None, "Finding solution with depth %d…" % self.solution_depth

	def prepare_solution(self):
		self.solution_depth = None
		return ("Preparing to find solution", self.find_solution_func)

