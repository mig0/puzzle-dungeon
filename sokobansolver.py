from constants import *
from celltools import *
from common import get_time_str
from debug import *
from grid import grid
from time import time
import bisect

MIN_SOLUTION_DEPTH = 5
MAX_SOLUTION_DEPTH = 500
SOLUTION_DEPTH_STEP = 5
MAX_FIND_SOLUTION_TIME = 25 * 60 * 60

SOLUTION_TYPE_BY_SHIFTS = 1
SOLUTION_TYPE_BY_MOVES = 2

SOLUTION_ALG_DFS   = "DFS"
SOLUTION_ALG_BFS   = "BFS"
SOLUTION_ALG_GREED = "Greedy"
SOLUTION_ALG_ASTAR = "A*"

solver = None

class SuperPosition:
	def __init__(self, barrel_cells, all_proto_segments):
		self.barrel_cells = barrel_cells
		self.all_proto_segments = all_proto_segments
		self._solution_cost = None  # lazy calculation
		self.is_solved = grid.is_solved_for_barrels(barrel_cells)
		self.positions = {}  # char_cell -> Position

	def get_or_reparent_or_create_position(self, char_cell, parent, own_nums, segments):
		position = self.positions.get(char_cell)
		if position is None:
			position = Position(self, char_cell, parent, own_nums, segments)
			self.positions[char_cell] = position
		else:
			debug([position.depth], DBG_SOLV2, position)
			new_total_nums = apply_diff(parent.total_nums, own_nums) if parent else (0, 0)
			if position.cmp(new_total_nums) > 0:
				position.reparent(parent, own_nums, segments)
				debug([position.depth], DBG_SOLV2, "Position already seen, but new path is better")
			else:
				debug([position.depth], DBG_SOLV2, "Position already seen, and no improvement")

		return position

	@property
	def solution_cost(self):
		if self._solution_cost is None:
			self._solution_cost = solver.get_min_solution_depth(self.barrel_cells) or 0
		return self._solution_cost

class Position:
	def __init__(self, super, char_cell, parent, own_nums, segments):
		self.super = super
		self.char_cell = char_cell
		self.parent = parent
		if parent:
			parent.add_child(self)
			self.own_nums = own_nums
			self.segments = segments
			self.calc_nums()
		else:
			self.own_nums = (0, 0)
			self.segments = []
			self.depth = 0
			self.total_nums = (0, 0)
			self._solution_cost = None
			self.is_dirty = False
		self._segments_str = None
		self.children = []
		self.is_expanded = False
		self.is_fully_processed = False
		solver.num_created_positions += 1
		debug([self.depth], DBG_SOLV2, "Created %s" % self)

	@property
	def nums_str(self):
		return "%d/%d" % (self.total_nums[0], self.total_nums[1])

	@property
	def is_solved(self):
		return self.depth and self.super.is_solved

	def cmp(self, pos2):
		total_nums2 = pos2 if type(pos2) == tuple else pos2.total_nums
		(m1, s1), (m2, s2), stype = self.total_nums, total_nums2, solver.solution_type
		return cmp((m1, s1), (m2, s2)) if stype == SOLUTION_TYPE_BY_MOVES else cmp((s1, m1), (s2, m2))

	def add_child(self, child):
		assert child, "Bug in Position, child is None"
		assert self != child, "Bug in Position, child is self"
		assert child not in self.children, "Bug in Position, adding child twice"
		self.children.append(child)

	def remove_from_parent(self):
		if self.parent:
			self.parent.children.remove(self)
			self.parent = None

	def reparent(self, parent, own_nums, segments):
		assert parent, "Bug in Position, parent is None"
		assert self != parent, "Bug in Position, parent is self"
		self.remove_from_parent()
		self.parent = parent
		self.parent.add_child(self)
		self.own_nums = own_nums
		self.segments = segments
		self.mark_dirty_down()

	def calc_nums(self):
		self.depth = self.parent.depth + 1
		self.total_nums = apply_diff(self.parent.total_nums, self.own_nums)
		self._solution_cost = None
		self.is_dirty = False
		self.is_fully_processed = False

	def mark_dirty_down(self):
		self.is_dirty = True
		self.is_fully_processed = False
		for child in self.children:
			child.mark_dirty_down()

	def cut_down(self):
		self.is_fully_processed = True
		for child in self.children:
			child.cut_down()

	@property
	def segments_str(self):
		if self._segments_str is None:
			segment_strs = []
			for path_cells, char_cell, barrel_cell in self.segments:
				segment_strs.append("+%d %s -> %s" % (len(path_cells), char_cell, barrel_cell))
			self._segments_str = ' '.join(segment_strs) or 'root'
		return self._segments_str

	@property
	def solution_cost(self):
		if self._solution_cost is None:
			m, s = self.total_nums
			own_cost = m + s * (3 if solver.solution_type == SOLUTION_TYPE_BY_SHIFTS else 0)
			self._solution_cost = own_cost // (self.depth + 1) + self.super.solution_cost * 8
		return self._solution_cost

	def to_solution_pairs(self):
		solution_pairs = self.parent.to_solution_pairs() if self.parent else []
		for path_cells, char_cell, barrel_cell in self.segments:
			solution_pairs.append([path_cells, DIR_NAMES[cell_diff(char_cell, barrel_cell, grid.reverse_barrel_mode, True)]])
		return solution_pairs

	def __str__(self):
		return "{◰[%d] %s ☻%s ■%s}" % \
			(self.depth, self.nums_str, self.char_cell, ' '.join(map(str, self.super.barrel_cells)))

class SokobanSolver():
	def __init__(self):
		self.solution_alg = None
		self.return_first = False
		self.disable_budget = False
		self.disable_prepare = False
		self.reset_solution_data()

	def reset_solution_data(self):
		global solver
		solver = None
		self.visited_super_positions = {}  # super_position_id -> SuperPosition
		self.solution_depth = MAX_SOLUTION_DEPTH
		self.solution_type = SOLUTION_TYPE_BY_SHIFTS
		self.initial_position = None
		self.solved_position = None
		self.start_solution_time = None
		self.end_solution_time = 99999999999
		self.budget_solution_time = None
		self.num_created_positions = 0
		self.unprocessed_positions = None
		self.num_processed_positions = 0
		self.sort_positions = None
		grid.reset()

	def get_min_solution_depth(self, barrel_cells):
		solution_depth = 0
		for barrel_cell in barrel_cells:
			num_shifts = grid.min_barrel_plate_shifts[min(grid.min_barrel_plate_shifts.keys(), key=lambda cell:
				grid.min_barrel_plate_shifts[cell] if cell == barrel_cell else grid.num_bits
			)] if grid.min_barrel_plate_shifts else grid.num_bits
			solution_depth += num_shifts

		return solution_depth

	def estimate_solution_depth(self):
		if (solution_depth := self.get_min_solution_depth(self.barrel_cells)) is None:
			return MIN_SOLUTION_DEPTH

		solution_depth = max(solution_depth, MIN_SOLUTION_DEPTH)

		if self.solution_alg != SOLUTION_ALG_DFS:
			return solution_depth
		return ((solution_depth - MIN_SOLUTION_DEPTH - 1) // SOLUTION_DEPTH_STEP + 1) * SOLUTION_DEPTH_STEP + MIN_SOLUTION_DEPTH

	def find_or_create_super_position(self, char_cell, barrel_cells):
		if grid.is_zsb:
			super_position_id = grid.barrel_idxs
		else:
			grid.get_accessible_bits(char_cell)
			super_position_id = (grid.get_min_last_accessible_idx(), *grid.barrel_idxs)

		if super_position_id in self.visited_super_positions:
			return self.visited_super_positions[super_position_id]

		if grid.is_zsb:
			accessible_cells_near_barrels = grid.get_all_valid_zsb_char_barrel_moves()
		else:
			accessible_cells_near_barrels = grid.get_all_valid_char_barrel_shifts()

		accessible_cells_near_barrels.sort(key=lambda two_cells: grid.min_char_barrel_plate_shifts.get(two_cells, grid.num_bits) or grid.num_bits)
		all_proto_segments = tuple([(None, char_cell, barrel_cell)] for char_cell, barrel_cell in accessible_cells_near_barrels)
		if grid.is_zsb:
			for proto_segments in all_proto_segments:
				_, char_cell, barrel_cell = proto_segments[0]
				if grid.reverse_barrel_mode:
					new_char_cell, new_barrel_cell = apply_diff(char_cell, cell_diff(barrel_cell, char_cell)), char_cell
				else:
					new_char_cell, new_barrel_cell = barrel_cell, apply_diff(barrel_cell, cell_diff(char_cell, barrel_cell))
				proto_segments.append(([], new_char_cell, new_barrel_cell))

		super_position = SuperPosition(barrel_cells, all_proto_segments)
		self.visited_super_positions[super_position_id] = super_position
		return super_position

	def create_child_position_or_reparent_if_better(self, position, segments):
		num_moves, num_shifts = 0, 0
		grid.set_barrels(position.super.barrel_cells)
		for path_cells, char_cell, barrel_cell in segments:
			new_char_cell, _ = grid.shift(char_cell, barrel_cell)
			num_moves += len(path_cells) + 1
			num_shifts += 1
		own_nums = num_moves, num_shifts

		if self.solved_position and self.solved_position.cmp(apply_diff(position.total_nums, own_nums)) <= 0:
			debug([position.depth], DBG_SOLV2, "Not creating child that does not improve found solution")
			return None

		super_position = self.find_or_create_super_position(new_char_cell, grid.barrel_cells)

		child = super_position.get_or_reparent_or_create_position(new_char_cell, position, own_nums, segments)

		return child

	def expand_position(self, position):
		if position.is_expanded:
			return

		debug([position.depth], DBG_SOLV, "%s" % position.segments_str)
		for proto_segments in position.super.all_proto_segments:
			(_, char_cell, barrel_cell), *rest_segments = proto_segments
			debug([position.depth], DBG_SOLV2, "Expanding %s -> %s" % (char_cell, barrel_cell))
			char_path = grid.find_path(position.char_cell, char_cell, position.super.barrel_cells)
			assert char_path is not None, "Bug in find_solution algorithm: no char path"
			segments = [(char_path, char_cell, barrel_cell), *rest_segments]

			self.create_child_position_or_reparent_if_better(position, segments)

		position.is_expanded = True

	def process_position(self, position):
		if position.is_dirty:
			position.calc_nums()

		if position.is_fully_processed:
			return True

		depth = position.depth

		if not self.disable_budget and time() > self.budget_solution_time:
			debug([depth], DBG_SOLV, "Returning control after budget time of 1s")
			return None

		self.num_processed_positions += 1

		if time() > self.end_solution_time:
			debug([depth], DBG_SOLV, "Solution time limit %ds reached" % MAX_FIND_SOLUTION_TIME)
			position.cut_down()
			return True

		if self.solved_position and position.cmp(self.solved_position) >= 0:
			debug([depth], DBG_SOLV, "Position does not improve the found solution")
			position.cut_down()
			return True

		if position.is_solved:
			self.solved_position = position
			debug([depth], DBG_SOLV, "Found solution %s in %.1fs" % (position.nums_str, time() - self.start_solution_time))
			position.cut_down()
			return None if self.return_first else True

		self.expand_position(position)

		position.is_fully_processed = all(child.is_fully_processed for child in position.children)

		return position.is_fully_processed

	def find_solution_using_dfs(self, position=None):
		if not position:
			position = self.initial_position

		depth = position.depth

		if depth >= self.solution_depth:
			debug([depth], DBG_SOLV, "Solution depth limit %d reached" % self.solution_depth)
			return False

		if (is_fully_processed := self.process_position(position)) is not False:
			return is_fully_processed

		is_fully_processed = True
		for child in position.children:
			if (is_fully_processed0 := self.find_solution_using_dfs(child)) is None:
				return None
			is_fully_processed &= is_fully_processed0

		if is_fully_processed:
			position.is_fully_processed = True

		return is_fully_processed

	def find_solution_using_dfs_with_lifo(self):
		unprocessed_positions = self.unprocessed_positions
		depth_limit_positions = []

		while unprocessed_positions:
			position = unprocessed_positions[-1]

			if position.depth >= self.solution_depth:
				unprocessed_positions.pop()
				depth_limit_positions.append(position)
				debug([position.depth], DBG_SOLV, "Solution depth limit %d reached" % self.solution_depth)
				continue

			is_fully_processed = self.process_position(position)
			if is_fully_processed is None:
				unprocessed_positions.extend(depth_limit_positions)
				return None
			unprocessed_positions.pop()
			if is_fully_processed:
				continue
			for child in reversed(position.children):
				if not child in unprocessed_positions:
					unprocessed_positions.append(child)

		self.unprocessed_positions = depth_limit_positions

		return not depth_limit_positions

	def find_solution_using_bfs(self):
		unprocessed_positions = self.unprocessed_positions
		depth_limit_positions = []

		while unprocessed_positions:
			position = unprocessed_positions[0]

			if position.depth >= self.solution_depth:
				unprocessed_positions.pop(0)
				depth_limit_positions.append(position)
				debug([position.depth], DBG_SOLV, "Solution depth limit %d reached" % self.solution_depth)
				continue

			is_fully_processed = self.process_position(position)
			if is_fully_processed is None:
				unprocessed_positions.extend(depth_limit_positions)
				return None
			unprocessed_positions.pop(0)
			if is_fully_processed:
				continue
			for child in position.children:
				if not child in unprocessed_positions:
					unprocessed_positions.append(child)

		self.unprocessed_positions = depth_limit_positions

		return not depth_limit_positions

	def find_solution_using_pq(self):
		unprocessed_positions = self.unprocessed_positions

		while unprocessed_positions:
			position = unprocessed_positions[0]
			is_fully_processed = self.process_position(position)
			if is_fully_processed is None:
				return None
			unprocessed_positions.pop(0)
			if is_fully_processed:
				continue
			for child in position.children:
				if not child in unprocessed_positions:
					bisect.insort(unprocessed_positions, child, key=self.sort_positions)
		return True

	def get_found_solution_items(self, reason):
		# store the solution nums for users
		solution_items = None
		self.last_solution_time_str = None
		self.last_solution_nums_str = None
		self.last_solution_str = None
		is_solved = self.solved_position is not None
		if is_solved:
			self.last_solution_time_str = get_time_str(time() - self.start_solution_time)
			self.last_solution_nums_str = self.solved_position.nums_str
			self.last_solution_str = ''
			char_cell = self.char_cell
			for char_path, shift_direction in self.solved_position.to_solution_pairs():
				for cell in char_path:
					self.last_solution_str += DIR_NAMES[cell_diff(char_cell, cell)]
					char_cell = cell
				self.last_solution_str += shift_direction.upper()
				char_cell = apply_diff(char_cell, DIRS_BY_NAME[shift_direction])

		debug(DBG_SOLV, "Finding solution %s, returning %s solution" % (reason, self.last_solution_nums_str or "no"))
		self.reset_solution_data()
		return list(self.last_solution_str) if is_solved else None

	def get_find_solution_status_str(self):
		time_str = get_time_str(time() - self.start_solution_time)
		status_str = "Finding %s optimal solution" % ("move" if self.solution_type == SOLUTION_TYPE_BY_MOVES else "push")
		status_str += "; %s" % time_str
		if self.solution_alg in (SOLUTION_ALG_DFS, SOLUTION_ALG_BFS):
			status_str += "; depth %d" % self.solution_depth
		status_str += "; positions: %d" % self.num_processed_positions
		if self.solution_alg in (SOLUTION_ALG_BFS, SOLUTION_ALG_GREED, SOLUTION_ALG_ASTAR):
			status_str += " + %d" % len(self.unprocessed_positions)
		if self.solved_position:
			status_str += "; found %s" % self.solved_position.nums_str
		debug(DBG_SOLV, status_str + "; sp: %d p: %d" % (len(self.visited_super_positions), self.num_created_positions))
		return status_str

	def find_solution_func(self, stop=False):
		if not self.disable_budget:
			self.budget_solution_time = time() + 1

		if not self.start_solution_time:
			# preparing to find solution
			self.start_solution_time = time()
			self.end_solution_time = time() + MAX_FIND_SOLUTION_TIME
			grid.prepare_sokoban_solution(self.char_cell, self.disable_prepare)
			grid.set_barrels(self.barrel_cells)
			super_position = self.find_or_create_super_position(self.char_cell, self.barrel_cells)
			self.initial_position = Position(super_position, self.char_cell, None, None, None)
			if self.solution_alg in (SOLUTION_ALG_DFS, SOLUTION_ALG_BFS):
				self.solution_depth = self.estimate_solution_depth()
			self.unprocessed_positions = [self.initial_position]
			if self.solution_alg == SOLUTION_ALG_GREED:
				self.sort_positions = lambda position: position.total_nums
			if self.solution_alg == SOLUTION_ALG_ASTAR:
				self.sort_positions = lambda position: position.solution_cost
			return None, self.get_find_solution_status_str()

		if stop or self.solution_depth > MAX_SOLUTION_DEPTH or time() > self.end_solution_time:
			return self.get_found_solution_items("terminated"), None

		debug([0], DBG_SOLV, "Using %s%s" % (self.solution_alg, " up to depth %d" % self.solution_depth if self.solution_depth < MAX_SOLUTION_DEPTH else ""))

		is_finished = (
			self.find_solution_using_dfs() if self.solution_alg == SOLUTION_ALG_DFS else
			self.find_solution_using_bfs() if self.solution_alg == SOLUTION_ALG_BFS else
			self.find_solution_using_pq()
		)

		if is_finished or self.return_first and self.solved_position:
			return self.get_found_solution_items("finished"), None

		# solution in progress
		if is_finished is False:
			if self.solution_alg == SOLUTION_ALG_BFS:
				self.solution_depth += 1
			elif self.solution_alg == SOLUTION_ALG_DFS:
				self.solution_depth += SOLUTION_DEPTH_STEP
		return None, self.get_find_solution_status_str()

	# provide a bundle method for functional tests
	def solve(self, solution_type=SOLUTION_TYPE_BY_SHIFTS, disable_budget=True):
		global solver
		assert solver, "SokobanSolution.solve requires configure"
		old_solution_type = self.solution_type
		old_disable_budget = self.disable_budget
		self.solution_type = solution_type
		self.disable_budget = disable_budget
		while True:
			solution_items, cont = self.find_solution_func()
			if not cont:
				break
		self.solution_type = old_solution_type
		self.disable_budget = old_disable_budget
		return solution_items

	def configure(self, map, reverse_barrel_mode, char_cell, barrel_cells):
		grid.configure(map, reverse_barrel_mode=reverse_barrel_mode, cut_outer_floors=True)
		grid.set_barrels(barrel_cells)
		grid.check_zsb()
		if self.solution_alg is None:
			self.solution_alg = SOLUTION_ALG_ASTAR if grid.is_zsb or self.return_first else SOLUTION_ALG_BFS
		self.char_cell = char_cell
		self.barrel_cells = barrel_cells
		global solver
		solver = self

def create_sokoban_solver(map, reverse_barrel_mode=False, solution_alg=None, return_first=False, show_map=False, show_dead=False):
	char_cell = None
	barrel_cells = []
	for cy in range(len(map[0])):
		for cx in range(len(map)):
			cell = (cx, cy)
			is_plate = False
			if map[cell] == ACTOR_CHARS["char"]:
				char_cell = cell
			elif map[cell] == ACTOR_ON_PLATE_CHARS["char"]:
				char_cell = cell
				is_plate = True
			elif map[cell] == ACTOR_CHARS["barrel"]:
				barrel_cells.append(cell)
			elif map[cell] == ACTOR_ON_PLATE_CHARS["barrel"]:
				barrel_cells.append(cell)
				is_plate = True
			else:
				continue
			map[cell] = CELL_PLATE if is_plate else CELL_FLOOR

	solver = SokobanSolver()
	solver.solution_alg = solution_alg
	solver.return_first = return_first
	solver.configure(map, reverse_barrel_mode, char_cell, tuple(barrel_cells))
	if show_dead:
		grid.prepare_sokoban_solution(char_cell)
	if show_map:
		descr = None if show_map is True else show_map
		grid.show_map(descr, char=char_cell, barrels=barrel_cells, show_dead=show_dead)
	return solver

