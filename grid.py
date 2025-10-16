import numpy
from bitarray import bitarray

from constants import *
from celltools import apply_diff, cell_diff, sort_cells
from common import isinstance_by_name, die
from debug import *

_ONE = bitarray('1')
_ZEROBITS = bitarray('')
SORTED_DIRS = sort_cells(DIRS)

class Grid:
	"""
	High-performance map & path abstraction for puzzles.
	- Terminology used in Grid class:
		The 2d map consists of cells, starting from (0, 0).
		Passable cells - floor and other non-obstacle cells,
			only passable cells are indexed for path purposes.
	- Core concepts:
		bits (bitarray), bit (bitarray with only one bit set),
		cell (x, y), cells (ordered tuple of distinct cell),
		idx (bitarray index), idxs (ordered tuple of distinct idx),
		the cell order is defined by y-then-x, i.e. (3, 1) < (2, 4).
	- Conversion for passable cells: idx_cells (list), cell_idxs (dict)
	- Neighbors: all_passable_neigh_idxs: list of neigh idxs per idx.
	- Masks via bitarray: barrel_bits, dead_barrel_bits, plate_bits.
	- Special masks: all_bits (all passable), no_bits, accessible_bits.
	- Conversion from/to all equivalency types:
		x=bit/idx/cell    -> to_bit(x),  to_idx(x),  to_cell(x)
		x=bits/idxs/cells -> to_bits(x), to_idxs(x), to_cells(x)
	- Support for non passable cells:
		to_idx_or_none
	- Configuration:
		configure(map)
		reset()
	- Common functionality:
		show_map
		get_cell_type_with_clean_floor
		is_passable_neigh
	- Path finding:
		get_accessible_bits
		get_accessible_neigh_cells
		get_accessible_cells
		get_accessible_distances
		get_accessible_cell_distances
		find_path_idxs
		find_path
	- Supports concept of barrels by storing barrel_bits and respecting
	  self.reverse_barrel_mode via:
		set_barrels
		store_barrels
		store_reset_barrels
		restore_barrels
		barrel_idxs
		barrel_cells
		is_solved_for_barrels
		get_all_adjacent_barrel_pairs
	- Supports Sokoban solution via:
		can_push, can_pull, can_shift, try_opposite_shift
		push, pull, shift, opposite_shift
		try_push, try_pull, try_shift, try_opposite_shift
		is_dead_barrel
		is_four_barrel_deadlock
		is_r_or_l_2x2_barrel_deadlock
		is_surrounding_barrel_deadlock
		get_all_valid_char_barrel_shifts
		prepare_sokoban_solution
		reset_sokoban_solution
	"""

	def __init__(self):
		self.reset()

	def reset(self):
		self.map = None
		self.size_x, self.size_y = 0, 0
		self.idx_cells = []
		self.cell_idxs = {}
		self.num_bits = 0
		self.all_bits = _ZEROBITS
		self.no_bits = _ZEROBITS
		# support concept of barrels
		self.reverse_barrel_mode = False
		self.barrel_bits = _ZEROBITS
		self.orig_barrel_bits_stack = []
		self.plate_bits = _ZEROBITS
		self.reset_sokoban_solution()

	def configure(self, map, reverse_barrel_mode=False):
		self.reset()
		self.map = map
		self.size_x, self.size_y = len(map), len(map[0])

		# build index of passable cells
		self.idx_cells = []
		self.cell_idxs = {}
		for cy in range(self.size_y):
			for cx in range(self.size_x):
				cell = (cx, cy)
				if map[cell] not in CELL_CHAR_MOVE_OBSTACLES:
					idx = len(self.idx_cells)
					self.idx_cells.append(cell)
					self.cell_idxs[cell] = idx

		self.num_bits = len(self.idx_cells)
		self.all_bits = bitarray('1' * self.num_bits)
		self.no_bits = bitarray('0' * self.num_bits)

		# precompute all passable neigbors per each passable cell
		self.all_passable_neigh_idxs = []
		for idx, cell in enumerate(self.idx_cells):
			passable_neigh_idxs = []
			for dir in SORTED_DIRS:
				neigh_cell = apply_diff(cell, dir)
				neigh_idx = self.cell_idxs.get(neigh_cell)
				if neigh_idx is not None:
					passable_neigh_idxs.append(neigh_idx)
			self.all_passable_neigh_idxs.append(tuple(passable_neigh_idxs))

		self.reverse_barrel_mode = reverse_barrel_mode
		self.barrel_bits = self.no_bits.copy()
		self.plate_bits = self.no_bits.copy()
		for idx, cell in enumerate(self.idx_cells):
			if map[cell] == CELL_PLATE:
				self.plate_bits[idx] = True

		self.reset_sokoban_solution()

		debug(DBG_PATH, "Configured map with %d floors" % self.num_bits)
		debug(DBG_PATH2, "- idx_cells: %s" % (self.idx_cells))

	def show_map(self, descr=None, clean=True, combined=True, dual=False, endl=False, char_cell=None, cell_chars={}, show_dead=False, extra_cb=None):
		if descr:
			print(descr)
		def get_cell_type_with_clean_floor(cell):
			return CELL_FLOOR if clean and self.map[cell] in CELL_FLOOR_TYPES else self.map[cell]
		for cy in range(self.size_y):
			if not combined:
				for cx in range(self.size_x):
					cell = (cx, cy)
					print(get_cell_type_with_clean_floor(cell), end="")
				if dual and cell_chars:
					print("    ", end="")
					for cx in range(self.size_x):
						cell = (cx, cy)
						print(cell_chars.get(cell, get_cell_type_with_clean_floor(cell)), end="")
				if dual:
					print("    ", end="")
			if dual or combined:
				for cx in range(self.size_x):
					cell = (cx, cy)
					cell_idx = self.cell_idxs.get(cell)
					cell_ch = get_cell_type_with_clean_floor(cell)
					if show_dead and self.map[cell] in CELL_FLOOR_TYPES and self.dead_barrel_bits[cell_idx]:
						cell_ch = '☓'
					actor_chars = ACTOR_ON_PLATE_CHARS if cell_ch == CELL_PLATE else ACTOR_CHARS
					if cell in cell_chars:
						cell_ch = cell_chars[cell]
					if cell_idx is not None and self.barrel_bits[cell_idx]:
						cell_ch = actor_chars['barrel']
					if extra_cb and (ch := extra_cb(cell, actor_chars)):
						cell_ch = ch
					if cell == char_cell:
						cell_ch = actor_chars['char']
					print(cell_ch, end="")
			print()

	def to_bit(self, idx_or_cell_or_actor):
		bit = self.no_bits.copy()
		bit[self.to_idx(idx_or_cell_or_actor)] = True
		return bit

	def to_idx(self, idx_or_cell_or_actor):
		if isinstance(idx_or_cell_or_actor, int):
			return idx_or_cell_or_actor
		if isinstance_by_name(idx_or_cell_or_actor, 'CellActor'):
			idx_or_cell_or_actor = idx_or_cell_or_actor.c
		return self.cell_idxs[idx_or_cell_or_actor]

	def to_cell(self, idx_or_cell_or_actor):
		return self.idx_cells[self.to_idx(idx_or_cell_or_actor)]

	def to_bits(self, bits_or_idxs_or_cells_or_actors):
		if isinstance(bits_or_idxs_or_cells_or_actors, bitarray):
			return bits_or_idxs_or_cells_or_actors
		bits = self.no_bits.copy()
		for idx_or_cell_or_actor in bits_or_idxs_or_cells_or_actors:
			bits[self.to_idx(idx_or_cell_or_actor)] = True
		return bits

	def to_idxs(self, bits_or_idxs_or_cells_or_actors):
		if isinstance(bits_or_idxs_or_cells_or_actors, bitarray):
			return tuple(bits_or_idxs_or_cells_or_actors.itersearch(_ONE))
		return tuple(self.to_idx(idx_or_cell_or_actor) for idx_or_cell_or_actor in bits_or_idxs_or_cells_or_actors)

	def to_cells(self, bits_or_idxs_or_cells_or_actors):
		if isinstance(bits_or_idxs_or_cells_or_actors, bitarray):
			return tuple(self.idx_cells[idx] for idx in bits_or_idxs_or_cells_or_actors.itersearch(_ONE))
		return tuple(self.idx_cells[self.to_idx(idx_or_cell_or_actor)] for idx_or_cell_or_actor in bits_or_idxs_or_cells_or_actors)

	def to_idx_or_none(self, idx_or_cell_or_actor):
		try:
			return self.to_idx(idx_or_cell_or_actor)
		except KeyError:
			return None

	def is_passable_neigh(self, first, second):
		return self.to_idx(second) in self.all_passable_neigh_idxs[self.to_idx(first)]

	def get_accessible_bits(self, start, obstacle_bits=None):
		start_idx = self.to_idx(start)
		if obstacle_bits is None:
			obstacle_bits = self.barrel_bits

		accessible_bits = self.no_bits.copy()
		accessible_bits[start_idx] = True
		unprocessed_bits = self.no_bits.copy()
		unprocessed_bits[start_idx] = True

		while True:
			new_bits = self.no_bits.copy()

			for idx in unprocessed_bits.itersearch(_ONE):
				for neigh_idx in self.all_passable_neigh_idxs[idx]:
					if not accessible_bits[neigh_idx] and not obstacle_bits[neigh_idx]:
						new_bits[neigh_idx] = True
			if not new_bits.any():
				break
			accessible_bits |= new_bits
			unprocessed_bits = new_bits

		self.last_accessible_bits = accessible_bits

		return accessible_bits

	def get_accessible_neigh_cells(self, cell):
		return self.to_cells(self.all_passable_neigh_idxs[self.to_idx(cell)])

	def get_accessible_cells(self, start, obstacles=()):
		if DBG_PATH in debug.features:
			debug(DBG_PATH, "get_accessible_cells %s" % (self.to_cell(start),))
		accessible_bits = self.get_accessible_bits(start, self.to_bits(obstacles))
		if DBG_PATH in debug.features:
			debug(DBG_PATH2, "- %d cells" % accessible_bits.count())
			debug(DBG_PATH3, "- %s" % str(self.to_cells(accessible_bits)))
		return self.to_cells(accessible_bits)

	def get_accessible_distances(self, start, obstacles=None):
		start_idx = self.to_idx(start)
		obstacle_bits = self.barrel_bits if obstacles is None else self.to_bits(obstacles)

		distances = numpy.full(self.num_bits, -1, dtype=numpy.int16)
		distances[start_idx] = 0

		unprocessed_bits = self.no_bits.copy()
		unprocessed_bits[start_idx] = True

		distance = 0
		while True:
			new_bits = self.no_bits.copy()
			for idx in unprocessed_bits.itersearch(_ONE):
				for neigh_idx in self.all_passable_neigh_idxs[idx]:
					if distances[neigh_idx] == -1 and not obstacle_bits[neigh_idx]:
						new_bits[neigh_idx] = True
			if not new_bits.any():
				break
			distance += 1
			for idx in new_bits.itersearch(_ONE):
				distances[idx] = distance
			unprocessed_bits = new_bits

		return distances

	def get_accessible_cell_distances(self, start, obstacles=None):
		distances = self.get_accessible_distances(start, self.to_bits(obstacles) if obstacles else None)
		return {self.to_cell(idx): distance for idx, distance in enumerate(distances)}

	def find_path_idxs(self, start, target, obstacle_bits=None):
		start_idx = self.to_idx_or_none(start)
		target_idx = self.to_idx_or_none(target)
		if start_idx is None or target_idx is None:
			return None
		if start_idx == target_idx:
			return []
		if obstacle_bits is None:
			obstacle_bits = self.barrel_bits

		distances = self.get_accessible_distances(start_idx, obstacle_bits)
		distance = distances[target_idx]
		if distance < 0:
			return None

		path_idxs = [target_idx]
		while distance > 1:
			distance -= 1
			for neigh_idx in self.all_passable_neigh_idxs[path_idxs[0]]:
				if distances[neigh_idx] == distance:
					path_idxs.insert(0, neigh_idx)
					break
			else:
				die("Bug in get_accessible_distances, no accessible neigh with distance %d for idx %d" % (distance, neigh_idx), True)

		return path_idxs

	def find_path(self, start, target, obstacles=()):
		if DBG_PATH in debug.features:
			debug(DBG_PATH, "find_path %s -> %s" % (self.to_cell(start), self.to_cell(target)))
		path_idxs = self.find_path_idxs(start, target, self.to_bits(obstacles))
		if DBG_PATH in debug.features:
			debug(DBG_PATH2, "- %s" % (
				"%d cells" % len(path_idxs) if path_idxs is not None else "no path"
			))
			if path_idxs:
				debug(DBG_PATH3, "- %s" % str(self.to_cells(path_idxs)))
		return self.to_cells(path_idxs) if path_idxs is not None else None

	def set_barrels(self, barrels):
		self.barrel_bits = self.to_bits(barrels)

	def store_barrels(self):
		self.orig_barrel_bits_stack.append(self.barrel_bits.copy())

	def store_reset_barrels(self):
		self.store_barrels()
		self.barrel_bits = self.no_bits.copy()

	def restore_barrels(self):
		self.barrel_bits = self.orig_barrel_bits_stack.pop()

	@property
	def barrel_idxs(self):
		return self.to_idxs(self.barrel_bits)

	@property
	def barrel_cells(self):
		return self.to_cells(self.barrel_bits)

	def is_solved_for_barrels(self, barrels=None):
		return not (~self.plate_bits & (self.to_bits(barrels) if barrels else self.barrel_bits)).any()

	def is_dead_barrel(self, barrel):
		return bool(self.dead_barrel_bits and self.dead_barrel_bits[self.to_idx(barrel)])

	def is_four_barrel_deadlock(self, cell1, cell2, cell3, cell4):
		barrel_cells = []
		for cell in (cell2, cell3, cell4):
			idx = self.cell_idxs.get(cell)
			if idx is not None:
				if self.barrel_bits[idx]:
					barrel_cells.append(cell)
				else:
					return False
		for barrel_cell in barrel_cells + [cell1]:
			if not self.plate_bits[self.cell_idxs[barrel_cell]]:
				return True
		return False

	def is_r_or_l_2x2_barrel_deadlock(self, barrel_cell, dir):
		barrel_f_cell = apply_diff(barrel_cell, dir)
		barrel_l_cell = apply_diff(barrel_cell, DIR_L if dir in (DIR_U, DIR_D) else DIR_U)
		barrel_lf_cell = apply_diff(barrel_l_cell, dir)
		if self.is_four_barrel_deadlock(barrel_cell, barrel_l_cell, barrel_lf_cell, barrel_f_cell):
			return True
		barrel_r_cell = apply_diff(barrel_cell, DIR_R if dir in (DIR_U, DIR_D) else DIR_D)
		barrel_rf_cell = apply_diff(barrel_r_cell, dir)
		if self.is_four_barrel_deadlock(barrel_cell, barrel_r_cell, barrel_rf_cell, barrel_f_cell):
			return True
		return False

	def is_surrounding_barrel_deadlock(self, char_cell, barrel_cell, dir):
		barrel_f_cell = apply_diff(char_cell, dir)
		barrel_l_cell = apply_diff(char_cell, DIR_L if dir in (DIR_U, DIR_D) else DIR_U)
		barrel_r_cell = apply_diff(char_cell, DIR_R if dir in (DIR_U, DIR_D) else DIR_D)
		if self.is_four_barrel_deadlock(barrel_cell, barrel_l_cell, barrel_r_cell, barrel_f_cell):
			return True
		return False

	def try_push(self, char_cell, barrel_cell):
		assert char_cell in self.cell_idxs and barrel_cell in self.cell_idxs
		if not self.barrel_bits[self.cell_idxs[barrel_cell]]:
			return None

		dir = cell_diff(char_cell, barrel_cell)
		new_barrel_cell = apply_diff(barrel_cell, dir)
		new_barrel_idx = self.cell_idxs.get(new_barrel_cell)
		if new_barrel_idx is None or self.barrel_bits[new_barrel_idx]:
			return None

		new_char_cell = barrel_cell

		# disallow dead-barrel-cells
		if self.dead_barrel_bits[new_barrel_idx]:
			return None

		# eliminate 2x2 deadlocks
		if self.is_r_or_l_2x2_barrel_deadlock(new_barrel_cell, dir):
			return None

		return new_char_cell, new_barrel_cell

	def try_pull(self, char_cell, barrel_cell):
		assert char_cell in self.cell_idxs and barrel_cell in self.cell_idxs
		if not self.barrel_bits[self.cell_idxs[barrel_cell]]:
			return None

		dir = cell_diff(barrel_cell, char_cell)
		new_char_cell = apply_diff(char_cell, dir)
		new_char_idx = self.cell_idxs.get(new_char_cell)
		if new_char_idx is None or self.barrel_bits[new_char_idx]:
			return None

		new_barrel_cell = char_cell

		# disallow dead-barrel-cells
		if self.dead_barrel_bits[self.cell_idxs[new_barrel_cell]]:
			return None

		# eliminate locked-char deadlock
		if self.is_surrounding_barrel_deadlock(new_char_cell, new_barrel_cell, dir):
			return None

		return new_char_cell, new_barrel_cell

	def try_shift(self, char_cell, barrel_cell):
		return (self.try_pull if self.reverse_barrel_mode else self.try_push)(char_cell, barrel_cell)

	def try_opposite_shift(self, char_cell, barrel_cell):
		return (self.try_push if self.reverse_barrel_mode else self.try_pull)(char_cell, barrel_cell)

	def can_push(self, char_cell, barrel_cell):
		return self.try_push(char_cell, barrel_cell) is not None

	def can_pull(self, char_cell, barrel_cell):
		return self.try_pull(char_cell, barrel_cell) is not None

	def can_shift(self, char_cell, barrel_cell):
		return (self.can_pull if self.reverse_barrel_mode else self.can_push)(char_cell, barrel_cell)

	def can_opposite_shift(self, char_cell, barrel_cell):
		return (self.can_push if self.reverse_barrel_mode else self.can_pull)(char_cell, barrel_cell)

	def push(self, char_cell, barrel_cell):
		new_cells = self.try_push(char_cell, barrel_cell)
		if new_cells:
			new_char_cell, new_barrel_cell = new_cells
			self.barrel_bits[self.cell_idxs[barrel_cell]] = False
			self.barrel_bits[self.cell_idxs[new_barrel_cell]] = True
		return new_cells

	def pull(self, char_cell, barrel_cell):
		new_cells = self.try_pull(char_cell, barrel_cell)
		if new_cells:
			new_char_cell, new_barrel_cell = new_cells
			self.barrel_bits[self.cell_idxs[barrel_cell]] = False
			self.barrel_bits[self.cell_idxs[new_barrel_cell]] = True
		return new_cells

	def shift(self, char_cell, barrel_cell):
		return (self.pull if self.reverse_barrel_mode else self.push)(char_cell, barrel_cell)

	def opposite_shift(self, char_cell, barrel_cell):
		return (self.push if self.reverse_barrel_mode else self.pull)(char_cell, barrel_cell)

	# return list of all accessible (char_cell, barrel_cell) pairs valid for shift
	# should to be called after get_accessible_cells()
	def get_all_valid_char_barrel_shifts(self, accessible_bits=None):
		if accessible_bits is None:
			accessible_bits = self.last_accessible_bits
		cell_pairs = []
		for barrel_idx in self.barrel_bits.itersearch(_ONE):
			for char_idx in self.all_passable_neigh_idxs[barrel_idx]:
				if not accessible_bits[char_idx]:
					continue
				char_cell = self.idx_cells[char_idx]
				barrel_cell = self.idx_cells[barrel_idx]
				if self.can_shift(char_cell, barrel_cell):
					cell_pairs.append((char_cell, barrel_cell))
		return cell_pairs

	# disable means to proceed to the solution without calculating minimum-shifts and dead-barrels
	def prepare_sokoban_solution(self, disable=False):
		plate_cells = self.to_cells(self.plate_bits)

		self.min_char_barrel_plate_shifts = min_char_barrel_plate_shifts = {}
		self.min_barrel_plate_shifts = min_barrel_plate_shifts = {}
		if not plate_cells:
			self.dead_barrel_bits = self.all_bits
			return
		self.dead_barrel_bits = self.no_bits
		if disable:
			return

		self.store_reset_barrels()

		# run BFS separately for each plate to compute distances from that plate
		for plate_cell in plate_cells:
			min_barrel_plate_shifts[plate_cell] = 0
			unprocessed = [(char_cell, plate_cell) for char_cell in self.get_accessible_neigh_cells(plate_cell)]

			for depth in range(1, self.num_bits + 1):
				if not unprocessed:
					break

				next_unprocessed = []
				any_new = False

				for last_char_cell, barrel_cell in unprocessed:
					self.set_barrels([barrel_cell])
					accessible_bits = self.get_accessible_bits(last_char_cell)

					for char_idx in self.all_passable_neigh_idxs[self.to_idx(barrel_cell)]:
						if not accessible_bits[char_idx]:
							continue

						new_cells = self.try_opposite_shift(self.idx_cells[char_idx], barrel_cell)
						if not new_cells:
							continue

						if new_cells not in min_char_barrel_plate_shifts:
							min_char_barrel_plate_shifts[new_cells] = depth
							new_char_cell, new_barrel_cell = new_cells
							if new_barrel_cell not in min_barrel_plate_shifts:
								min_barrel_plate_shifts[new_barrel_cell] = depth
							next_unprocessed.append(new_cells)

				unprocessed = next_unprocessed

		self.dead_barrel_bits = ~self.to_bits(min_barrel_plate_shifts.keys()) & self.all_bits
		self.min_char_barrel_plate_shifts = min_char_barrel_plate_shifts
		self.min_barrel_plate_shifts = min_barrel_plate_shifts

		self.restore_barrels()

		if DBG_PATH2 in debug.features:
			self.show_map("Map with dead-barrel cells", show_dead=True)

	def reset_sokoban_solution(self):
		self.dead_barrel_bits = self.no_bits
		self.min_barrel_plate_shifts = None
		self.min_char_barrel_plate_shifts = None

grid = Grid()
