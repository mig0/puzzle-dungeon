from constants import *
from celltools import *
from common import get_time_str
from debug import *
from grid import grid, search_bits, _ONE
from time import time
import heapq
import itertools

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

INF = 10 ** 9

solver = None

def cost_to_key(cost):
	return cost if solver.solution_type == SOLUTION_TYPE_BY_MOVES else (cost[1], cost[0])

def cmp_costs(cost1, cost2):
	(m1, s1), (m2, s2) = cost1, cost2
	return cmp((m1, s1), (m2, s2)) if solver.solution_type == SOLUTION_TYPE_BY_MOVES else cmp((s1, m1), (s2, m2))

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
			debug([position.depth], DBG_SOLV3, position)
			new_total_nums = apply_diff(parent.total_nums, own_nums) if parent else (0, 0)
			if position.cmp(new_total_nums) > 0:
				position.reparent(parent, own_nums, segments)
				debug([position.depth], DBG_SOLV3, "Position already seen, but new path is better")
			else:
				debug([position.depth], DBG_SOLV3, "Position already seen, and no improvement")

		return position

	@property
	def solution_cost(self):
		if self._solution_cost is None:
			self._solution_cost = solver.get_min_solution_cost(self.barrel_cells)
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
		solver.last_created_position = self
		if self.depth > solver.max_created_depth:
			solver.max_created_depth = self.depth
		debug([self.depth], DBG_SOLV3, "Created %s" % self)

	@property
	def nums_str(self):
		return "%d/%d" % (self.total_nums[0], self.total_nums[1])

	@property
	def is_solved(self):
		return self.depth and self.super.is_solved

	def cmp(self, pos_or_cost):
		return cmp_costs(self.total_nums, pos_or_cost if type(pos_or_cost) == tuple else pos_or_cost.total_nums)

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
		solver.pq_push(self)

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
			self._solution_cost = apply_diff(self.total_nums, self.super.solution_cost, factor=1)
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
		self.last_created_position = None
		self.max_created_depth = 0
		self.unprocessed_positions = None
		self.num_processed_positions = 0
		self.sort_positions = None
		self._pq_counter = None
		self._best_position_keys = {}  # position -> key used in heap
		grid.reset()

	def pq_push(self, position):
		if self.sort_positions is None:
			return

		key = cost_to_key(self.sort_positions(position))
		prev_key = self._best_position_keys.get(position)
		if prev_key is not None and prev_key <= key:
			return

		# tie-break by counter, stable ordering
		entry = (key, next(self._pq_counter), position)
		heapq.heappush(self.unprocessed_positions, entry)
		self._best_position_keys[position] = key

	def pq_pop(self):
		# pop until we get a non-stale tuple or heap is empty
		while self.unprocessed_positions:
			key, _, position = heapq.heappop(self.unprocessed_positions)
			best_key = self._best_position_keys.get(position)
			if best_key is None or best_key != key:
				# skip stale entry
				continue
			# remove entry now - will reinsert if it gets updated
			del self._best_position_keys[position]
			return key, position
		return None, None


	# greedy lower-bound cost (moves, shifts) for the given barrels
	def get_min_solution_cost(self, barrels):
		barrel_idxs = grid.to_idxs(barrels)
		plate_idxs = grid.plate_idxs

		# build cost matrix: cost[b][p] = min_plate_barrel_costs[p].get(b, (INF, INF))
		barrel_plate_costs = {}
		for barrel_idx in barrel_idxs:
			barrel_plate_costs[barrel_idx] = {}
			for plate_idx in plate_idxs:
				plate_min_barrel_costs = self.min_plate_barrel_costs.get(plate_idx, {})
				barrel_plate_costs[barrel_idx][plate_idx] = plate_min_barrel_costs.get(barrel_idx)

		# greedy matching: for each barrel pick plate with best cost
		total_cost = (0, 0)
		assigned_plates = set()

		remaining_barrels = set(barrel_idxs)
		while remaining_barrels:
			best = None
			for barrel_idx in remaining_barrels:
				for plate_idx in plate_idxs:
					if plate_idx in assigned_plates:
						continue
					cost = barrel_plate_costs[barrel_idx][plate_idx]
					if cost is None:
						continue
					if best is None or cmp_costs(cost, best[0]) < 0:
						best = (cost, barrel_idx, plate_idx)
			if best is None:
				# unreachable barrel (dead), return huge
				return (INF, INF)
			best_cost, barrel_idx, plate_idx = best
			total_cost = apply_diff(total_cost, best_cost)
			assigned_plates.add(plate_idx)
			remaining_barrels.remove(barrel_idx)

		return total_cost

	def get_min_solution_depth(self, barrel_cells):
		return sum(self.min_barrel_plate_shifts.get(barrel_cell, grid.num_bits) for barrel_cell in barrel_cells)

	def estimate_solution_depth(self):
		_, solution_depth = self.get_min_solution_cost(self.barrel_cells)
		if solution_depth is None or solution_depth == INF:
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

		accessible_cells_near_barrels.sort(key=lambda two_cells: self.min_char_barrel_plate_shifts.get(two_cells, grid.num_bits) or grid.num_bits)
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
			debug([position.depth], DBG_SOLV3, "Not creating child that does not improve found solution")
			return None

		super_position = self.find_or_create_super_position(new_char_cell, grid.barrel_cells)

		child = super_position.get_or_reparent_or_create_position(new_char_cell, position, own_nums, segments)

		return child

	def expand_position(self, position):
		if position.is_expanded:
			return

		debug([position.depth], DBG_SOLV2, "%s" % position.segments_str)
		for proto_segments in position.super.all_proto_segments:
			(_, char_cell, barrel_cell), *rest_segments = proto_segments
			debug([position.depth], DBG_SOLV3, "Expanding %s -> %s" % (char_cell, barrel_cell))
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
			debug([depth], DBG_SOLV2, "Returning control after budget time of 1s")
			return None

		self.num_processed_positions += 1

		if time() > self.end_solution_time:
			debug([depth], DBG_SOLV2, "Solution time limit %ds reached" % MAX_FIND_SOLUTION_TIME)
			position.cut_down()
			return True

		if self.solved_position and position.cmp(self.solved_position) >= 0:
			debug([depth], DBG_SOLV2, "Position does not improve the found solution")
			position.cut_down()
			return True

		if position.is_solved:
			self.solved_position = position
			debug([depth], DBG_SOLV2, "Found solution %s in %.1fs" % (position.nums_str, time() - self.start_solution_time))
			position.cut_down()
			return None if self.return_first else True

		if self.solved_position:
			min_cost = self.get_min_solution_cost(position.super.barrel_cells)
			if self.solved_position.cmp(apply_diff(position.total_nums, min_cost)) <= 0:
				debug([depth], DBG_SOLV2, "Pruning position by solution lower bound")
				position.cut_down()
				return True

		self.expand_position(position)

		position.is_fully_processed = all(child.is_fully_processed for child in position.children)

		return position.is_fully_processed

	def find_solution_using_dfs(self, position=None):
		if not position:
			position = self.initial_position

		depth = position.depth

		if depth >= self.solution_depth:
			debug([depth], DBG_SOLV2, "Solution depth limit %d reached" % self.solution_depth)
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
				debug([position.depth], DBG_SOLV2, "Solution depth limit %d reached" % self.solution_depth)
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
				debug([position.depth], DBG_SOLV2, "Solution depth limit %d reached" % self.solution_depth)
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
		while True:
			key, position = self.pq_pop()
			if position is None:
				# heap is empty, finished
				return True
			is_fully_processed = self.process_position(position)
			if is_fully_processed is None:
				self.pq_push(position)
				return None
			if is_fully_processed:
				continue
			# push all children (their keys are computed inside pq_push)
			for child in position.children:
				self.pq_push(child)

	def prepare_solution(self, char=None):
		self.min_char_barrel_plate_shifts = min_char_shifts = {}
		self.min_barrel_plate_shifts = min_shifts = {}
		self.min_plate_char_barrel_costs = {}
		self.min_plate_barrel_costs = {}

		if grid.plate_bits == grid.no_bits:
			grid.dead_barrel_bits = grid.all_bits
			return
		grid.dead_barrel_bits = grid.no_bits
		# disable means to proceed with the solution without calculating minimal-costs and dead-barrels
		if self.disable_prepare:
			return

		char_idx = grid.to_idx_or_none(char) if char else None
		grid.barrel_bits = grid.no_bits
		char_accessible_bits = grid.get_accessible_bits(char_idx) if char_idx else grid.all_bits

		# run BFS separately for each plate to compute distances from that plate
		for plate_idx in search_bits(grid.plate_bits, _ONE):
			if not char_accessible_bits[plate_idx]:
				continue
			plate_cell = grid.to_cell(plate_idx)
			self.min_plate_barrel_costs[plate_idx] = min_plate_costs = {}
			self.min_plate_char_barrel_costs[plate_idx] = min_plate_char_costs = {}

			depth = 0
			min_shifts[plate_cell] = 0
			min_plate_costs[plate_idx] = (0, 0)
			unprocessed = [(char_idx, plate_idx, 0) for char_idx in grid.all_passable_neigh_idxs[plate_idx]]

			while unprocessed:
				depth += 1
				next_unprocessed = []

				for last_char_idx, barrel_idx, last_dist in unprocessed:
					grid.barrel_bits = grid.to_bit(barrel_idx)
					accessible_bits = grid.get_accessible_bits(last_char_idx)

					for char_idx in grid.all_passable_neigh_idxs[barrel_idx]:
						if not accessible_bits[char_idx]:
							continue

						new_cells = grid.try_opposite_shift(grid.idx_cells[char_idx], grid.idx_cells[barrel_idx])
						if not new_cells:
							continue

						new_idxs = grid.to_idxs(new_cells)
						own_dist = grid.get_accessible_distance(char_idx, last_char_idx)
						new_dist = last_dist + own_dist + 1
						cost = (new_dist, depth)

						was_improved = False
						if new_cells not in min_char_shifts or min_char_shifts[new_cells] > depth:
							min_char_shifts[new_cells] = depth
							new_char_cell, new_barrel_cell = new_cells
							if new_barrel_cell not in min_shifts or min_shifts[new_barrel_cell] > depth:
								min_shifts[new_barrel_cell] = depth
							was_improved = True
						if new_idxs not in min_plate_char_costs or cmp_costs(min_plate_char_costs[new_idxs], cost) > 0:
							min_plate_char_costs[new_idxs] = cost
							new_char_idx, new_barrel_idx = new_idxs
							if new_barrel_idx not in min_plate_costs or cmp_costs(min_plate_costs[new_barrel_idx], cost) > 0:
								min_plate_costs[new_barrel_idx] = cost
							was_improved = True
						if was_improved:
							next_unprocessed.append(new_idxs + (new_dist,))

				unprocessed = next_unprocessed

		if debug.has("precosts"):
			plate_idx, min_plate_costs = sorted(self.min_plate_barrel_costs.items())[0]
			debug("min_plate_barrel_costs for the 1-st plate idx=%d" % plate_idx)
			debug([2], str(dict(sorted(min_plate_costs.items()))))

		grid.barrel_bits = grid.no_bits.copy()

		grid.dead_barrel_bits = ~grid.to_bits(min_shifts.keys())
		if debug.has(DBG_SOLV3):
			grid.show_map("Map with dead-barrel cells", show_dead=True)

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
		max_depth = self.max_created_depth
		if self.solution_alg == SOLUTION_ALG_DFS:
			status_str += "; limit %d" % self.solution_depth
		elif self.solution_alg == SOLUTION_ALG_BFS:
			status_str += "; depth %s" % max_depth
		else:
			status_str += "; %s deepest %d" % (self.solution_alg[0:2], max_depth)
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
			self.prepare_solution(self.char_cell)
			grid.set_barrels(self.barrel_cells)
			super_position = self.find_or_create_super_position(self.char_cell, self.barrel_cells)
			self.initial_position = Position(super_position, self.char_cell, None, None, None)

			if self.solution_alg in (SOLUTION_ALG_DFS, SOLUTION_ALG_BFS):
				self.solution_depth = self.estimate_solution_depth()
			if self.solution_alg == SOLUTION_ALG_GREED:
				self.sort_positions = lambda position: position.total_nums
			if self.solution_alg == SOLUTION_ALG_ASTAR:
				self.sort_positions = lambda position: position.solution_cost
			if self.solution_alg in (SOLUTION_ALG_GREED, SOLUTION_ALG_ASTAR):
				self.unprocessed_positions = []
				self._best_position_keys = {}
				self._pq_counter = itertools.count()
				self.pq_push(self.initial_position)
			else:
				self.unprocessed_positions = [self.initial_position]
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
		solver.prepare_solution(char_cell)
	if show_map:
		descr = None if show_map is True else show_map
		grid.show_map(descr, char=char_cell, barrels=barrel_cells, show_dead=show_dead)
	return solver

