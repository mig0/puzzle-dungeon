from constants import *
from celltools import *
from common import get_time_str
from debug import *
from grid import grid, search_bits, _ONE
from time import time
from hungarian import Hungarian, INF
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
SOLUTION_ALG_UCS   = "Uniform"
SOLUTION_ALG_GREED = "Greedy"
SOLUTION_ALG_ASTAR = "A*"

DBG_PRUN = "prun"

solver = None

def cost_to_key(cost):
	return cost if solver.solution_type == SOLUTION_TYPE_BY_MOVES else (cost[1], cost[0])

def cmp_costs(cost1, cost2):
	(m1, s1), (m2, s2) = cost1, cost2
	return cmp((m1, s1), (m2, s2)) if solver.solution_type == SOLUTION_TYPE_BY_MOVES else cmp((s1, m1), (s2, m2))

class SuperPosition:
	def __init__(self, barrel_idxs, all_proto_segments):
		self.barrel_idxs = barrel_idxs
		self.all_proto_segments = all_proto_segments
		self._solution_cost = None  # lazy calculation
		self.is_solved = grid.is_solved_for_barrels(barrel_idxs)
		self.positions = {}  # char_idx -> Position

	def get_or_reparent_or_create_position(self, char_idx, parent, own_nums, segments):
		position = self.positions.get(char_idx)
		if position is None:
			position = Position(self, char_idx, parent, own_nums, segments)
			self.positions[char_idx] = position
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
			self._solution_cost = solver.get_min_solution_cost(self.barrel_idxs)
		return self._solution_cost

class Position:
	def __init__(self, super, char_idx, parent, own_nums, segments):
		self.super = super
		self.char_idx = char_idx
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
		self._segments_str = None
		self.children = []
		self.is_expanded = False
		self.is_fully_processed = False
		self.best_key = None  # used in heap
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
		self.recalc_nums_down()

	def calc_nums(self):
		self.depth = self.parent.depth + 1
		self.total_nums = apply_diff(self.parent.total_nums, self.own_nums)
		self._solution_cost = None
		self.is_fully_processed = False

	def recalc_nums_down(self):
		descendant_positions = [self]
		while descendant_positions:
			position = descendant_positions.pop()
			position.calc_nums()
			if position.best_key is not None:
				solver.pq_push(position)
			descendant_positions.extend(position.children)

	def cut_down(self):
		self.is_fully_processed = True
		for child in self.children:
			child.cut_down()

	@property
	def segments_str(self):
		if self._segments_str is None:
			segment_strs = []
			for distance, char_idx, barrel_idx in self.segments:
				segment_strs.append("+%d %s -> %s" % (distance, char_idx, barrel_idx))
			self._segments_str = ' '.join(segment_strs) or 'root'
		return self._segments_str

	@property
	def solution_cost(self):
		if self._solution_cost is None:
			self._solution_cost = apply_diff(self.total_nums, self.super.solution_cost, factor=solver.past_vus_cost_factor)
		return self._solution_cost

	def to_solution_pairs(self):
		solution_pairs = self.parent.to_solution_pairs() if self.parent else []
		if self.parent:
			grid.set_barrels(self.parent.super.barrel_idxs)
			prev_char_cell = grid.to_cell(self.parent.char_idx)
			for char_path_len, char_idx, barrel_idx in self.segments:
				char_cell, barrel_cell = grid.to_cells((char_idx, barrel_idx))
				path_cells = grid.find_path(prev_char_cell, char_cell, self.parent.super.barrel_idxs)
				if path_cells is None:
					grid.show_map(descr=f"{prev_char_cell} -> {char_cell}", char=char_idx, cell_colors={prev_char_cell: 1, barrel_cell: 31})
				assert path_cells is not None, "Bug: Failed to reconstruct char path in solution"
				assert len(path_cells) == char_path_len, f"Bug: Char path {path_cells} is not as expected (len {char_path_len})"
				solution_pairs.append([path_cells, DIR_NAMES[cell_diff(char_cell, barrel_cell, grid.reverse_barrel_mode, True)]])
				if len(self.segments) == 1:  # optimize for common case
					break
				new_char_cell, new_barrel_cell = grid.shift(char_cell, barrel_cell)
				prev_char_cell = new_char_cell
		return solution_pairs

	def __str__(self):
		return "{◰[%d] %s ☻%s ■%s}" % \
			(self.depth, self.nums_str, self.char_idx, ' '.join(map(str, self.super.barrel_idxs)))

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
		self.limit_time = MAX_FIND_SOLUTION_TIME
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
		if debug.has(DBG_PRUN):
			self.num_non_created_costy_positions = 0
			self.num_non_created_dead_positions = 0
			self.num_costy_than_solved_positions = 0
			self.num_found_solved_positions = 0
			self.num_costy_solved_bound_positions = 0
		self.past_vus_cost_factor = 1  # 1 is for A*
		self.sort_positions = None
		self._pq_counter = None
		grid.reset()

	def pq_push(self, position):
		if self.sort_positions is None:
			return

		key = cost_to_key(self.sort_positions(position))

		# verify that there is no better key in heap already
		if key == position.best_key:
			return
		assert position.best_key is None or position.best_key > key

		# tie-break by counter for stable ordering
		entry = (key, next(self._pq_counter), position)
		heapq.heappush(self.unprocessed_positions, entry)

		position.best_key = key

	def pq_pop(self):
		# pop until we get a non-stale tuple or heap is empty
		while self.unprocessed_positions:
			key, _, position = heapq.heappop(self.unprocessed_positions)

			# discard stale entry if position key improved after push to heap
			assert position.best_key is None or position.best_key <= key
			if position.best_key != key:
				continue

			assert not position.is_fully_processed
			return key, position

		return None, None

	def is_barrel_matching_found(self, barrel_idxs):
		if not self.is_barrel_mismatch_possible:
			return True

		plate_matches = {plate_idx: None for plate_idx in grid.plate_idxs}
		def dfs(barrel_idx, seen_plates):
			for plate_idx in self.accessible_barrel_plate_idxs.get(barrel_idx, ()):
				if plate_idx in seen_plates:
					continue
				seen_plates.add(plate_idx)
				if plate_matches[plate_idx] is None or dfs(plate_matches[plate_idx], seen_plates):
					plate_matches[plate_idx] = barrel_idx
					return True
			return False

		for barrel_idx in barrel_idxs:
			if not dfs(barrel_idx, set()):
				debug(DBG_SOLV3, "No matching for barrel %d found - deadlock" % barrel_idx)
				return False

		return True

	# greedy lower-bound cost (moves, shifts) with backtracking for the given barrels
	# return None only if is_barrel_matching_found(barrel_idxs) is False
	def old_get_min_solution_cost(self, barrel_idxs):
		if not self.is_barrel_matching_found(barrel_idxs):
			return None

		plate_idxs = grid.plate_idxs

		# collect cost matrix indexed by barrel_idx and then plate_idx
		costs = {}
		for barrel_idx in barrel_idxs:
			row = {}
			for plate_idx in plate_idxs:
				cost = self.min_plate_barrel_costs.get(plate_idx, {}).get(barrel_idx)
				if cost is not None:
					row[plate_idx] = cost
			costs[barrel_idx] = row

		# --- greedy attempt (fast) ---
		remaining_barrels = set(barrel_idxs)
		remaining_plates = set(plate_idxs)
		total_cost = (0, 0)

		while remaining_barrels:
			best = None
			for barrel_idx in remaining_barrels:
				for plate_idx in remaining_plates:
					cost = costs[barrel_idx].get(plate_idx)
					if cost is None:
						continue
					if best is None or cmp_costs(cost, best[0]) < 0:
						best = (cost, barrel_idx, plate_idx)

			if best is None:
				# greedy failed: fall back to full search
				break

			best_cost, barrel_idx, plate_idx = best
			total_cost = apply_diff(total_cost, best_cost)
			remaining_barrels.remove(barrel_idx)
			remaining_plates.remove(plate_idx)

		if not remaining_barrels:
			return total_cost

		# --- fallback: full DFS over ALL barrels (allow reassigning greedy choices) ---
		# Use greedy result as an initial upper bound if it produced any assignment
		upper_bound = None
		# If greedy produced a (partial) total_cost but incomplete, we can attempt
		# to produce a complete greedy-based upper bound by completing greedily from scratch:
		try_upper = True
		if try_upper:
			tb_barrels = set(barrel_idxs)
			tb_plates  = set(plate_idxs)
			tb_cost = (0, 0)
			ok = True
			while tb_barrels:
				bst = None
				for b in tb_barrels:
					for p in tb_plates:
						c = costs[b].get(p)
						if c is None:
							continue
						if bst is None or cmp_costs(c, bst[0]) < 0:
							bst = (c, b, p)
				if bst is None:
					ok = False
					break
				cbst, bb, pp = bst
				tb_cost = apply_diff(tb_cost, cbst)
				tb_barrels.remove(bb)
				tb_plates.remove(pp)
			if ok:
				upper_bound = tb_cost

		# choose ordering of barrels for search: MRV (fewest candidate plates first)
		barrel_idxs = sorted(barrel_idxs, key=lambda b: len(costs[b]) if b in costs else 0)
		best_cost = upper_bound  # None or (moves,shifts)

		# Pre-sort candidate plates for each barrel by increasing cost (keyed)
		sorted_barrel_plates = {}
		for barrel_idx in barrel_idxs:
			cps = [(costs[barrel_idx][plate_idx], plate_idx) for plate_idx in plate_idxs if plate_idx in costs[barrel_idx]]
			cps.sort(key=lambda cp: cost_to_key(cp[0]))
			sorted_barrel_plates[barrel_idx] = [plate_idx for _, plate_idx in cps]

		# Depth-first search over full set of barrels; prune by best_cost
		max_depth = len(barrel_idxs)

		def dfs(i, used_plates, cur_cost):
			nonlocal best_cost
			# terminal: assigned all barrels
			if i == max_depth:
				if best_cost is None or cmp_costs(cur_cost, best_cost) < 0:
					best_cost = cur_cost
				return

			barrel_idx = barrel_idxs[i]
			if not sorted_barrel_plates.get(barrel_idx):
				from colorize import COLOR_BYELLOW
				grid.show_map(cell_colors={grid.to_cell(barrel_idx): COLOR_BYELLOW}, char=char_idx)
				assert False, "Barrel has no candidates at all, but match must exist"

			for plate_idx in sorted_barrel_plates[barrel_idx]:
				if plate_idx in used_plates:
					continue
				new_cost = apply_diff(cur_cost, costs[barrel_idx][plate_idx])

				# prune if already not better than best_cost
				if best_cost is not None and cmp_costs(new_cost, best_cost) >= 0:
					continue

				used_plates.add(plate_idx)
				dfs(i + 1, used_plates, new_cost)
				used_plates.remove(plate_idx)

		dfs(0, set(), (0, 0))
		assert best_cost is not None, "Bug: No match after is_barrel_matching_found"

		return best_cost

	def get_min_solution_cost(self, barrel_idxs):
		if not self.is_barrel_matching_found(barrel_idxs):
			return None

		n = len(barrel_idxs)
		assert n == self.hungarian.n
		costs = self.hungarian.costs

		# prepare scalar packed-cost matrix
		for j in range(n):
			plate_idx = grid.plate_idxs[j]
			plate_costs = self.min_plate_barrel_costs.get(plate_idx, {})
			for i in range(n):
				barrel_idx = barrel_idxs[i]
				cost = plate_costs.get(barrel_idx)

				if cost is None:
					# unreachable -> give huge cost
					costs[i][j] = INF
				else:
					key = cost_to_key(cost)
					costs[i][j] = key[0] * grid.num_bits + key[1]

		packed_cost = self.hungarian.assign()

		return cost_to_key((packed_cost // grid.num_bits, packed_cost % grid.num_bits))

	def estimate_solution_depth(self):
		cost = self.get_min_solution_cost(self.barrel_idxs)
		if cost is None:
			debug(DBG_SOLV3, "get_min_solution_cost returned None on estimate_solution_depth")
			return MIN_SOLUTION_DEPTH

		solution_depth = max(cost[1], MIN_SOLUTION_DEPTH)

		if self.solution_alg != SOLUTION_ALG_DFS:
			return solution_depth
		return ((solution_depth - MIN_SOLUTION_DEPTH - 1) // SOLUTION_DEPTH_STEP + 1) * SOLUTION_DEPTH_STEP + MIN_SOLUTION_DEPTH

	def find_or_create_super_position(self, char_idx):
		barrel_idxs = grid.barrel_idxs
		if grid.is_zsb:
			super_position_id = barrel_idxs
		else:
			grid.get_accessible_bits(char_idx)
			super_position_id = (grid.get_min_last_accessible_idx(), *barrel_idxs)

		if super_position_id in self.visited_super_positions:
			return self.visited_super_positions[super_position_id]

		if grid.is_zsb:
			accessible_cells_near_barrels = grid.get_all_valid_zsb_char_barrel_moves()
		else:
			accessible_cells_near_barrels = grid.get_all_valid_char_barrel_shifts(valid_pairs=self.valid_shift_pairs)

		accessible_cells_near_barrels.sort(key=lambda two_cells: cost_to_key(self.min_char_barrel_costs[grid.to_idxs(two_cells)]))
		all_proto_segments = tuple([(None, grid.cell_idxs[char_cell], grid.cell_idxs[barrel_cell])] for char_cell, barrel_cell in accessible_cells_near_barrels)
		if grid.is_zsb:
			for proto_segments in all_proto_segments:
				_, char_idx, barrel_idx = proto_segments[0]
				char_cell, barrel_cell = grid.to_cells((char_idx, barrel_idx))
				if grid.reverse_barrel_mode:
					new_cells = apply_diff(char_cell, cell_diff(barrel_cell, char_cell)), char_cell
				else:
					new_cells = barrel_cell, apply_diff(barrel_cell, cell_diff(char_cell, barrel_cell))
				new_char_idx, new_barrel_idx = grid.to_idxs(new_cells)
				proto_segments.append((0, new_char_idx, new_barrel_idx))

		super_position = SuperPosition(barrel_idxs, all_proto_segments)
		self.visited_super_positions[super_position_id] = super_position

		super_position.is_dead = not self.is_barrel_matching_found(barrel_idxs)

		return super_position

	def create_child_position_or_reparent_if_better(self, position, segments):
		num_moves, num_shifts = 0, 0
		grid.set_barrels(position.super.barrel_idxs)
		for distance, char_idx, barrel_idx in segments:
			new_char_cell, _ = grid.shift(grid.idx_cells[char_idx], grid.idx_cells[barrel_idx])
			num_moves += distance + 1
			num_shifts += 1
		own_nums = num_moves, num_shifts

		if self.solved_position and self.solved_position.cmp(apply_diff(position.total_nums, own_nums)) <= 0:
			if debug.has(DBG_PRUN):
				self.num_non_created_costy_positions += 1
			debug([position.depth], DBG_SOLV3, "Not creating child that does not improve found solution")
			return None

		new_char_idx = grid.cell_idxs[new_char_cell]
		super_position = self.find_or_create_super_position(new_char_idx)

		if super_position.is_dead:
			if debug.has(DBG_PRUN):
				self.num_non_created_dead_positions += 1
			debug([position.depth], DBG_SOLV3, "Not creating child in deadlocked super-position")
			return None

		child = super_position.get_or_reparent_or_create_position(new_char_idx, position, own_nums, segments)

		return child

	def expand_position(self, position):
		if position.is_expanded:
			return

		debug([position.depth], DBG_SOLV2, "%s" % position.segments_str)
		for proto_segments in position.super.all_proto_segments:
			(_, char_idx, barrel_idx), *rest_segments = proto_segments
			debug([position.depth], DBG_SOLV3, "Expanding %s -> %s" % (char_idx, barrel_idx))
			distance = grid.get_accessible_distance(position.char_idx, char_idx, position.super.barrel_idxs)
			assert distance is not None, "Bug in find_solution algorithm: no char path"
			segments = [(distance, char_idx, barrel_idx), *rest_segments]

			self.create_child_position_or_reparent_if_better(position, segments)

		position.is_expanded = True

	def process_position(self, position):
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
			if debug.has(DBG_PRUN):
				self.num_costy_than_solved_positions += 1
			debug([depth], DBG_SOLV2, "Position does not improve the found solution")
			position.cut_down()
			return True

		if position.is_solved:
			self.solved_position = position
			if debug.has(DBG_PRUN):
				self.num_found_solved_positions += 1
			debug([depth], DBG_SOLV2, "Found solution %s in %.1fs" % (position.nums_str, time() - self.start_solution_time))
			position.cut_down()
			return None if self.return_first else True

		if self.solved_position:
			min_cost = self.get_min_solution_cost(position.super.barrel_idxs)
			if self.solved_position.cmp(apply_diff(position.total_nums, min_cost)) <= 0:
				if debug.has(DBG_PRUN):
					self.num_costy_solved_bound_positions += 1
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

		if depth > self.solution_depth:
			debug([depth], DBG_SOLV2, "Solution depth limit %d exceeded" % self.solution_depth)
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

			if position.depth > self.solution_depth:
				unprocessed_positions.pop()
				depth_limit_positions.append(position)
				debug([position.depth], DBG_SOLV2, "Solution depth limit %d exceeded" % self.solution_depth)
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
		curr_level_positions = self.unprocessed_positions
		curr_queued = set(curr_level_positions)
		depth_limit_positions = []

		while curr_level_positions:
			next_level_positions = []
			next_queued = set()

			for position in curr_level_positions:
				if position.depth > self.solution_depth:
					depth_limit_positions.append(position)
					debug([position.depth], DBG_SOLV2, "Solution depth limit %d exceeded" % self.solution_depth)
					continue

				is_fully_processed = self.process_position(position)
				if is_fully_processed is None:
					self.unprocessed_positions = curr_level_positions[curr_level_positions.index(position):] + next_level_positions + depth_limit_positions
					return None
				if is_fully_processed:
					continue

				for child in position.children:
					if child in curr_queued or child in next_queued:
						continue
					next_level_positions.append(child)
					next_queued.add(child)

			# move to next level
			curr_level_positions = next_level_positions
			curr_queued = next_queued

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

	def check_solvability(self):
		# these are static constrants, should never appear during find-solution
		self.char_idx = grid.cell_idxs.get(self.char_cell)
		self.barrel_idxs = grid.to_idxs_or_none(self.barrel_cells)
		if self.char_idx is None:
			debug(DBG_SOLV, "Char is not on floor - unsolvable")
			return False
		if None in self.barrel_idxs:
			debug(DBG_SOLV, "Some barrels are not on floor - unsolvable")
			return False
		if grid.num_plates < len(self.barrel_idxs):
			debug(DBG_SOLV, "Number of plates smaller that barrels - unsolvable")
			return False
		barrel_bits = grid.to_bits(self.barrel_idxs)
		fixed_solved_barrel_bits = barrel_bits & grid.plate_bits & grid.dead_barrel_bits
		if fixed_solved_barrel_bits != grid.no_bits:
			barrel_bits &= ~fixed_solved_barrel_bits
			self.barrel_idxs = grid.to_idxs(barrel_bits)
		if barrel_bits & grid.dead_barrel_bits != grid.no_bits:
			debug(DBG_SOLV, "Some barrels are on dead barrel cells - unsolvable")
			return False
		self.hungarian = Hungarian(grid.num_plates)
		return True

	def prepare_solution(self, char=None):
		self.min_char_barrel_costs = min_char_costs = {}
		self.min_barrel_costs = min_costs = {}
		self.min_plate_char_barrel_costs = {}
		self.min_plate_barrel_costs = {}
		self.valid_shift_pairs = None

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
			min_costs[plate_idx] = (0, 0)
			min_plate_costs[plate_idx] = (0, 0)
			unprocessed = []
			for char_idx in grid.all_passable_neigh_idxs[plate_idx]:
				min_char_costs[(char_idx, plate_idx)] = (0, 0)
				min_plate_char_costs[(char_idx, plate_idx)] = (0, 0)
				unprocessed.append((char_idx, plate_idx, 0))

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
						new_barrel_idx = new_idxs[1]

						was_improved = False
						if new_idxs not in min_char_costs or cmp_costs(min_char_costs[new_idxs], cost) > 0:
							min_char_costs[new_idxs] = cost
							if new_barrel_idx not in min_costs or cmp_costs(min_costs[new_barrel_idx], cost) > 0:
								min_costs[new_barrel_idx] = cost
							was_improved = True
						if new_idxs not in min_plate_char_costs or cmp_costs(min_plate_char_costs[new_idxs], cost) > 0:
							min_plate_char_costs[new_idxs] = cost
							if new_barrel_idx not in min_plate_costs or cmp_costs(min_plate_costs[new_barrel_idx], cost) > 0:
								min_plate_costs[new_barrel_idx] = cost
							was_improved = True
						if was_improved:
							next_unprocessed.append(new_idxs + (new_dist,))

				unprocessed = next_unprocessed

		self.valid_shift_pairs = set(min_char_costs.keys())

		grid.barrel_bits = grid.no_bits.copy()

		grid.dead_barrel_bits = ~grid.to_bits(min_costs.keys())
		if debug.has(DBG_SOLV3):
			grid.show_map("Map with dead-barrel cells", show_dead=True)

		# build optimistic barrel -> reachable plates adjacency
		self.accessible_barrel_plate_idxs = {}
		self.is_barrel_mismatch_possible = False
		for barrel_idx in search_bits(~grid.dead_barrel_bits, _ONE):
			accessible_plate_idxs = [plate_idx for plate_idx in grid.plate_idxs if barrel_idx in self.min_plate_barrel_costs.get(plate_idx, {})]
			self.accessible_barrel_plate_idxs[barrel_idx] = accessible_plate_idxs
			self.is_barrel_mismatch_possible |= len(accessible_plate_idxs) < grid.num_plates

		if debug.has("precosts"):
			def idx_costs_to_str(d):
				return ', '.join(['%d: %d/%d' % (idx, *cost) for idx, cost in d.items()])
			debug("min_barrel_costs")
			debug([2], idx_costs_to_str(dict(sorted(self.min_barrel_costs.items()))))
			plate_idx, min_plate_costs = sorted(self.min_plate_barrel_costs.items())[0]
			debug("min_plate_barrel_costs for the 1-st plate idx=%d" % plate_idx)
			debug([2], idx_costs_to_str(dict(sorted(min_plate_costs.items()))))

			if debug.has("precosts+"):
				debug("Precalculated data:")
				debug([2], {
					"min_barrel_costs": self.min_barrel_costs,
					"min_char_barrel_costs": self.min_char_barrel_costs,
					"min_plate_barrel_costs": self.min_plate_barrel_costs,
					"min_plate_char_barrel_costs": self.min_plate_char_barrel_costs,
				})

	def get_found_solution_items(self, reason):
		# store the solution nums for users
		solution_items = None
		self.last_solution_time_str = get_time_str(time() - self.start_solution_time)
		self.last_solution_nums_str = None
		self.last_solution_str = None
		is_solved = self.solved_position is not None
		if is_solved:
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
		if self.solution_alg in (SOLUTION_ALG_BFS, SOLUTION_ALG_UCS, SOLUTION_ALG_GREED, SOLUTION_ALG_ASTAR):
			status_str += " + %d" % len(self.unprocessed_positions)
		if self.solved_position:
			status_str += "; found %s" % self.solved_position.nums_str
		if debug.has(DBG_PRUN):
			status_str += "; ncc %d ncd %d sol %d cts %d csb %d" % (self.num_non_created_costy_positions, self.num_non_created_dead_positions, self.num_found_solved_positions, self.num_costy_than_solved_positions, self.num_costy_solved_bound_positions)
		debug(DBG_SOLV, status_str + "; sp: %d p: %d" % (len(self.visited_super_positions), self.num_created_positions))
		return status_str

	def find_solution_func(self, stop=False):
		if not self.disable_budget:
			self.budget_solution_time = time() + 1

		if not self.start_solution_time:
			# preparing to find solution
			self.start_solution_time = time()
			self.end_solution_time = time() + self.limit_time

			self.prepare_solution(self.char_cell)
			if not self.check_solvability():
				return self.get_found_solution_items("unsolvable"), None

			debug(DBG_SOLV2, "Solving for barrels: %s" % (self.barrel_idxs,))
			grid.set_barrels(self.barrel_idxs)
			super_position = self.find_or_create_super_position(self.char_idx)
			self.initial_position = Position(super_position, self.char_idx, None, None, None)

			if self.solution_alg in (SOLUTION_ALG_DFS, SOLUTION_ALG_BFS):
				self.solution_depth = self.estimate_solution_depth()
			if self.solution_alg == SOLUTION_ALG_UCS:
				self.sort_positions = lambda position: position.total_nums
			if self.solution_alg == SOLUTION_ALG_GREED:
				self.past_vus_cost_factor = (0.82, 1.22)
				self.sort_positions = lambda position: position.solution_cost
			if self.solution_alg == SOLUTION_ALG_ASTAR:
				self.sort_positions = lambda position: position.solution_cost
			if self.solution_alg in (SOLUTION_ALG_UCS, SOLUTION_ALG_GREED, SOLUTION_ALG_ASTAR):
				self.unprocessed_positions = []
				self._pq_counter = itertools.count()
				self.pq_push(self.initial_position)
			else:
				self.unprocessed_positions = [self.initial_position]
			return None, self.get_find_solution_status_str()

		if stop or self.solution_depth > MAX_SOLUTION_DEPTH or time() > self.end_solution_time:
			return self.get_found_solution_items("terminated"), None

		debug(DBG_SOLV2, "Using %s%s" % (self.solution_alg, " up to depth %d" % self.solution_depth if self.solution_depth < MAX_SOLUTION_DEPTH else ""))

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
			self.solution_alg = SOLUTION_ALG_GREED if grid.is_zsb or self.return_first else SOLUTION_ALG_BFS
		self.char_cell = char_cell
		self.barrel_cells = barrel_cells
		global solver
		solver = self

def create_sokoban_solver(map, reverse_barrel_mode=False, solution_alg=None, return_first=False, show_map=False, show_dead=False, limit_time=None):
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
	if limit_time:
		solver.limit_time = limit_time
	solver.solution_alg = solution_alg
	solver.return_first = return_first
	solver.configure(map, reverse_barrel_mode, char_cell, tuple(barrel_cells))
	if show_dead:
		solver.prepare_solution(char_cell)
	if show_map:
		descr = None if show_map is True else show_map
		grid.show_map(descr, char=char_cell, barrels=barrel_cells, show_dead=show_dead)
	return solver

