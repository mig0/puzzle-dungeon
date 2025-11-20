import numpy
from bitarray import bitarray, frozenbitarray

from constants import *
from celltools import apply_diff, cell_diff, cell_dir, sort_cells, get_bounding_area
from common import die
from debug import *

DBG_GRID  = "grid"
DBG_GRID2 = "grid+"
DBG_GRID3 = "grid++"

DBG_PATH  = "path"
DBG_PATH2 = "path+"
DBG_PATH3 = "path++"

DBG_SZSB  = "szsb"
DBG_SZSB2 = "szsb+"

_ONE = frozenbitarray('1')
_ZEROBITS = frozenbitarray('')
SORTED_DIRS = sort_cells(DIRS)

# support bitarray prior to 2.9.x, replace search with more efficient itersearch
search_bits = bitarray.itersearch if hasattr(bitarray, 'itersearch') else bitarray.search

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
		self.num_plates = 0
		self.plate_bits = _ZEROBITS
		self.dead_barrel_bits = _ZEROBITS

	def configure(self, map, area=None, reverse_barrel_mode=False, cut_outer_floors=False):
		self.reset()
		self.map = map
		self.size_x, self.size_y = map.shape

		self._build_passable_cells_and_neighs()

		if cut_outer_floors:
			cut_bits = self.no_bits.copy()
			for cy in range(self.size_y):
				for cx in range(self.size_x):
					if 0 < cx < self.size_x - 1 and 0 < cy < self.size_y - 1:
						continue
					cell = cx, cy
					idx = self.cell_idxs.get(cell)
					if self.map[cell] in CELL_FLOOR_TYPES and not cut_bits[idx]:
						cut_bits |= self.get_accessible_bits(idx, self.no_bits)
			if cut_bits != self.no_bits:
				for idx in search_bits(cut_bits, _ONE):
					self.map[self.idx_cells[idx]] = CELL_VOID
				self._build_passable_cells_and_neighs()

		self.area = area or get_bounding_area(self.idx_cells)
		self.all_bits = ~self.no_bits

		self.reverse_barrel_mode = reverse_barrel_mode
		self.cut_outer_floors = cut_outer_floors
		self.barrel_bits = self.no_bits.copy()
		self.plate_bits = self.no_bits.copy()
		for idx, cell in enumerate(self.idx_cells):
			if map[cell] == CELL_PLATE or ACTOR_AND_PLATE_BY_CHAR.get(map[cell], ("", False))[1]:
				self.plate_bits[idx] = True
				self.num_plates += 1
			if map[cell] in (ACTOR_CHARS['barrel'], ACTOR_ON_PLATE_CHARS['barrel']):
				self.barrel_bits[idx] = True

		self.dead_barrel_bits = self.no_bits

		debug(DBG_GRID, "Configured map with %d floors" % self.num_bits)
		debug(DBG_GRID2, "- idx_cells: %s" % (self.idx_cells))

	def reconfigure(self):
		self.configure(self.map, self.area, self.reverse_barrel_mode, self.cut_outer_floors)

	def _build_passable_cells_and_neighs(self):
		# build index of passable cells
		self.idx_cells = []
		self.cell_idxs = {}
		for cy in range(self.size_y):
			for cx in range(self.size_x):
				cell = (cx, cy)
				if self.map[cell] not in CELL_CHAR_MOVE_OBSTACLES:
					idx = len(self.idx_cells)
					self.idx_cells.append(cell)
					self.cell_idxs[cell] = idx

		assert self.idx_cells, "Grid without passable cells is not supported"

		self.num_bits = len(self.idx_cells)
		self.no_bits  = bitarray('0' * self.num_bits)

		# precompute all passable neigbors per each passable cell
		self.all_passable_neigh_idxs = []
		self.all_passable_neigh_bits = []
		for idx, cell in enumerate(self.idx_cells):
			passable_neigh_idxs = []
			for dir in SORTED_DIRS:
				neigh_cell = apply_diff(cell, dir)
				neigh_idx = self.cell_idxs.get(neigh_cell)
				if neigh_idx is not None:
					passable_neigh_idxs.append(neigh_idx)
			self.all_passable_neigh_bits.append(self.to_bits(passable_neigh_idxs))
			self.all_passable_neigh_idxs.append(tuple(passable_neigh_idxs))

	def show_map(self, descr=None, clean=True, combined=True, dual=False, endl=False, char=None, barrels=None, cell_chars={}, show_dead=False, extra_cb=None):
		if descr:
			print(descr)
		char_cell = self.to_cell(char) if char else None
		if barrels:
			self.store_reset_barrels(barrels)
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
					is_plate = cell_idx is not None and self.plate_bits[cell_idx]
					cell_ch = CELL_PLATE if is_plate else get_cell_type_with_clean_floor(cell)
					if show_dead and cell_idx is not None and self.dead_barrel_bits[cell_idx]:
						cell_ch = '☓'
					actor_chars = ACTOR_ON_PLATE_CHARS if is_plate else ACTOR_CHARS
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
		if barrels:
			self.restore_barrels()

	def to_bit(self, idx_or_cell_or_actor):
		bit = self.no_bits.copy()
		bit[self.to_idx(idx_or_cell_or_actor)] = True
		return bit

	def to_idx(self, idx_or_cell_or_actor):
		if type(idx_or_cell_or_actor) == int:
			return idx_or_cell_or_actor
		if hasattr(idx_or_cell_or_actor, 'c'):
			idx_or_cell_or_actor = idx_or_cell_or_actor.c
		return self.cell_idxs[idx_or_cell_or_actor]

	def to_cell(self, idx_or_cell_or_actor):
		return self.idx_cells[self.to_idx(idx_or_cell_or_actor)]

	def to_bits(self, bits_or_idxs_or_cells_or_actors):
		if type(bits_or_idxs_or_cells_or_actors) == bitarray:
			return bits_or_idxs_or_cells_or_actors
		bits = self.no_bits.copy()
		for idx_or_cell_or_actor in bits_or_idxs_or_cells_or_actors:
			bits[self.to_idx(idx_or_cell_or_actor)] = True
		return bits

	def to_idxs(self, bits_or_idxs_or_cells_or_actors):
		if type(bits_or_idxs_or_cells_or_actors) == bitarray:
			return tuple(search_bits(bits_or_idxs_or_cells_or_actors, _ONE))
		return tuple(self.to_idx(idx_or_cell_or_actor) for idx_or_cell_or_actor in bits_or_idxs_or_cells_or_actors)

	def to_cells(self, bits_or_idxs_or_cells_or_actors):
		if type(bits_or_idxs_or_cells_or_actors) == bitarray:
			return tuple(self.idx_cells[idx] for idx in search_bits(bits_or_idxs_or_cells_or_actors, _ONE))
		return tuple(self.idx_cells[self.to_idx(idx_or_cell_or_actor)] for idx_or_cell_or_actor in bits_or_idxs_or_cells_or_actors)

	def to_idx_or_none(self, idx_or_cell_or_actor):
		try:
			return self.to_idx(idx_or_cell_or_actor)
		except KeyError:
			return None

	def to_idxs_or_none(self, bits_or_idxs_or_cells_or_actors):
		if type(bits_or_idxs_or_cells_or_actors) == bitarray:
			return tuple(search_bits(bits_or_idxs_or_cells_or_actors, _ONE))
		return tuple(self.to_idx_or_none(idx_or_cell_or_actor) for idx_or_cell_or_actor in bits_or_idxs_or_cells_or_actors)

	# Support for path finding

	def is_passable_neigh(self, first, second):
		return self.to_idx(second) in self.all_passable_neigh_idxs[self.to_idx(first)]

	def get_accessible_bits(self, start, obstacles=None):
		start_idx = self.to_idx(start)
		obstacle_bits = self.barrel_bits if obstacles is None else self.to_bits(obstacles)

		accessible_bits = self.no_bits.copy()
		accessible_bits[start_idx] = True
		unprocessed_bits = self.no_bits.copy()
		unprocessed_bits[start_idx] = True
		processed_bits = obstacle_bits.copy()
		processed_bits[start_idx] = True

		while True:
			new_bits = self.no_bits.copy()

			for idx in search_bits(unprocessed_bits, _ONE):
				new_bits |= self.all_passable_neigh_bits[idx]
			new_bits &= ~processed_bits
			if new_bits == self.no_bits:
				break
			accessible_bits |= new_bits
			processed_bits |= new_bits
			unprocessed_bits = new_bits

		self.last_accessible_bits = accessible_bits

		return accessible_bits

	def get_min_last_accessible_idx(self):
		return next(search_bits(self.last_accessible_bits, _ONE))

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

	def get_accessible_distance(self, start, target, obstacles=None):
		start_idx = self.to_idx_or_none(start)
		target_idx = self.to_idx_or_none(target)
		if start_idx is None or target_idx is None:
			return None
		if start_idx == target_idx:
			return 0
		obstacle_bits = self.barrel_bits if obstacles is None else self.to_bits(obstacles)
		if obstacle_bits[target_idx]:
			return None

		unprocessed_bits = self.no_bits.copy()
		unprocessed_bits[start_idx] = True
		processed_bits = obstacle_bits.copy()
		processed_bits[start_idx] = True

		distance = 1
		while True:
			new_bits = self.no_bits.copy()
			for idx in search_bits(unprocessed_bits, _ONE):
				new_bits |= self.all_passable_neigh_bits[idx]
				if new_bits[target_idx]:
					return distance
			new_bits &= ~processed_bits
			if new_bits == self.no_bits:
				return None
			processed_bits |= new_bits
			unprocessed_bits = new_bits
			distance += 1

	def get_accessible_distances(self, start, obstacles=None):
		start_idx = self.to_idx(start)
		obstacle_bits = self.barrel_bits if obstacles is None else self.to_bits(obstacles)

		distances = numpy.full(self.num_bits, -1, dtype=numpy.int16)
		distances[start_idx] = 0

		unprocessed_bits = self.no_bits.copy()
		unprocessed_bits[start_idx] = True
		processed_bits = obstacle_bits.copy()
		processed_bits[start_idx] = True

		distance = 1
		while True:
			new_bits = self.no_bits.copy()
			for idx in search_bits(unprocessed_bits, _ONE):
				new_bits |= self.all_passable_neigh_bits[idx]
			new_bits &= ~processed_bits
			if new_bits == self.no_bits:
				break
			for idx in search_bits(new_bits, _ONE):
				distances[idx] = distance
			processed_bits |= new_bits
			unprocessed_bits = new_bits
			distance += 1

		return distances

	def get_accessible_cell_distances(self, start, obstacles=None):
		distances = self.get_accessible_distances(start, obstacles)
		return {self.to_cell(idx): distance for idx, distance in enumerate(distances)}

	def find_path_idxs(self, start, target, obstacles=None):
		start_idx = self.to_idx_or_none(start)
		target_idx = self.to_idx_or_none(target)
		if start_idx is None or target_idx is None:
			return None
		if start_idx == target_idx:
			return []
		obstacle_bits = self.barrel_bits if obstacles is None else self.to_bits(obstacles)

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

	def find_path(self, start, target, obstacles=None):
		if DBG_PATH in debug.features:
			debug(DBG_PATH, "find_path %s -> %s" % (self.to_cell(start), self.to_cell(target)))
		path_idxs = self.find_path_idxs(start, target, obstacles)
		if DBG_PATH in debug.features:
			debug(DBG_PATH2, "- %s" % (
				"%d cells" % len(path_idxs) if path_idxs is not None else "no path"
			))
			if path_idxs:
				debug(DBG_PATH3, "- %s" % str(self.to_cells(path_idxs)))
		return self.to_cells(path_idxs) if path_idxs is not None else None

	# Support for barrel mechanics

	def set_barrels(self, barrels):
		self.barrel_bits = self.to_bits(barrels)

	def store_barrels(self):
		self.orig_barrel_bits_stack.append(self.barrel_bits.copy())

	def store_reset_barrels(self, barrels=None):
		self.store_barrels()
		if barrels:
			self.set_barrels(barrels)
		else:
			self.barrel_bits = self.no_bits.copy()

	def restore_barrels(self):
		self.barrel_bits = self.orig_barrel_bits_stack.pop()

	@property
	def barrel_idxs(self):
		return self.to_idxs(self.barrel_bits)

	@property
	def barrel_cells(self):
		return self.to_cells(self.barrel_bits)

	@property
	def num_barrels(self):
		return len(self.barrel_idxs)

	@property
	def plate_idxs(self):
		return self.to_idxs(self.plate_bits)

	@property
	def plate_cells(self):
		return self.to_cells(self.plate_bits)

	def is_solved_for_barrels(self, barrels=None):
		return (~self.plate_bits & (self.to_bits(barrels) if barrels else self.barrel_bits)) == self.no_bits

	def is_dead_barrel(self, barrel):
		return bool(self.dead_barrel_bits and self.dead_barrel_bits[self.to_idx(barrel)])

	def is_four_barrel_deadlock(self, cell1, cell2, cell3, cell4):
		is_deadlock = False
		for cell in (cell2, cell3, cell4):
			idx = self.cell_idxs.get(cell)
			if idx is not None:
				if not self.barrel_bits[idx]:
					return False
				if not self.plate_bits[idx]:
					is_deadlock = True
		return is_deadlock or not self.plate_bits[self.cell_idxs[cell1]]

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

	# Support for sokoban zsb puzzles
	# https://groups.io/g/sokoban/topic/zero_space_puzzles/113333167

	def is_valid_zsb_area_size(self):
		return self.area.size_x % 2 == 1 and self.area.size_y % 2 == 1 and self.area.size_x >= 5 and self.area.size_y >= 5

	def get_zsb_size(self):
		return ((self.area.size_x - 1) // 2, (self.area.size_y - 1) // 2)

	def get_zsb_size_str(self):
		return 'x'.join(map(str, self.get_zsb_size()))

	def get_zsb_wall_cells(self):
		return [cell for cell in self.area.cells if self.area.is_cell_oddodd(cell)]

	def is_zsb_anchor_cell(self, cell):
		return self.area.is_cell_inside(cell, 1) and (self.area.is_cell_evnodd(cell) or self.area.is_cell_oddevn(cell))

	def get_all_zsb_anchor_cells(self):
		return [cell for cell in self.area.cells if self.is_zsb_anchor_cell(cell)]

	def get_zsb_anchor_move_type(self, cell):
		return MOVE_V if self.area.is_cell_evnodd(cell) else MOVE_H if self.area.is_cell_oddevn(cell) else die("No anchor argument", True)

	def is_zsb_graph_connected(self, anchor_cells):
		wall_cells = self.get_zsb_wall_cells()
		wall_graphs = [(wall_cell,) for wall_cell in wall_cells]
		for anchor_cell in anchor_cells:
			dirs = (DIR_L, DIR_R) if self.get_zsb_anchor_move_type(anchor_cell) == MOVE_V else (DIR_U, DIR_D)
			wall1_cell = apply_diff(anchor_cell, dirs[0])
			wall2_cell = apply_diff(anchor_cell, dirs[1])
			wall1_graph = next(wall_graph for wall_graph in wall_graphs if wall1_cell in wall_graph)
			wall2_graph = next(wall_graph for wall_graph in wall_graphs if wall2_cell in wall_graph)
			if wall1_graph == wall2_graph:
				return False
			wall_graphs.remove(wall1_graph)
			wall_graphs.remove(wall2_graph)
			wall_graphs.append((*wall1_graph, *wall2_graph))
		return True  # the same: len(wall_graphs) == 1

	def is_zsb_correspondence(self, source_cells, target_cells):
		zsb_size = self.get_zsb_size()
		def count_anchors_in_row(anchor_cells, r):
			return sum(1 for cell in anchor_cells if cell[0] == self.area.x1 + r * 2 + 2)
		for r in range(zsb_size[0] - 1):
			if count_anchors_in_row(source_cells, r) != count_anchors_in_row(target_cells, r):
				return False
		def count_anchors_in_col(anchor_cells, c):
			return sum(1 for cell in anchor_cells if cell[1] == self.area.y1 + c * 2 + 2)
		for c in range(zsb_size[1] - 1):
			if count_anchors_in_col(source_cells, c) != count_anchors_in_col(target_cells, c):
				return False
		return True

	def get_all_valid_zsb_barrel_moves(self, barrel_cells):
		all_barrel_moves = []
		for barrel_cell in barrel_cells:
			dirs = (DIR_L, DIR_R) if self.get_zsb_anchor_move_type(barrel_cell) == MOVE_H else (DIR_U, DIR_D)
			for dir in dirs:
				target_cell = apply_diff(barrel_cell, dir, factor=2)
				if not self.area.is_cell_inside(target_cell) or target_cell in barrel_cells:
					continue
				if not self.is_zsb_graph_connected([cell for cell in barrel_cells if cell != barrel_cell] + [target_cell]):
					continue
				all_barrel_moves.append((barrel_cell, target_cell))
		return all_barrel_moves

	def get_all_valid_zsb_char_barrel_moves(self):
		return [(apply_diff(barrel_cell, cell_dir(target_cell, barrel_cell), self.reverse_barrel_mode), barrel_cell)
			for barrel_cell, target_cell in self.get_all_valid_zsb_barrel_moves(self.barrel_cells)]

	def check_zsb(self):
		self.is_zsb = False

		if debug.has(DBG_SZSB2):
			self.show_map()

		if not self.is_valid_zsb_area_size():
			debug(DBG_SZSB, "check_zsb: it's not ZSB, no valid zsb area size")
			return

		# check that walls are only on odd-odd cells and nowhere else
		for cell in self.area.cells:
			is_wall_cell = self.area.is_cell_oddodd(cell)
			idx = self.to_idx_or_none(cell)
			if is_wall_cell and idx is not None or not is_wall_cell and idx is None:
				debug(DBG_SZSB, "check_zsb: it's not ZSB, cell %s '%s' must%s be WALL" % (cell, self.map[cell], "" if is_wall_cell else " NOT"))
				return

		# check number and connectivity of barrels and plates
		zsb_size = self.get_zsb_size()
		num_expected_barrels = zsb_size[0] * zsb_size[1] - 1
		for archor_cells in (self.barrel_cells, self.plate_cells):
			if len(archor_cells) != num_expected_barrels:
				debug(DBG_SZSB, "check_zsb: it's not ZSB, wrong number of barrels/plates")
				return
			for cell in archor_cells:
				if not self.is_zsb_anchor_cell(cell):
					debug(DBG_SZSB, "check_zsb: it's not ZSB, barrel/plate %s misplaced" % (cell,))
					return
			if not self.is_zsb_graph_connected(archor_cells):
				debug(DBG_SZSB, "check_zsb: it's not ZSB, barrels/plates are not graph-connected")
				return

		# check correspondence of barrels and plates
		if not self.is_zsb_correspondence(self.barrel_cells, self.plate_cells):
			debug(DBG_SZSB, "check_zsb: it's not ZSB, no barrels/plates correspondence")
			return

		debug(DBG_SZSB, "check_zsb: it's ZSB")
		debug(DBG_SZSB2, [1], {"plates": self.plate_bits, "barrels": self.barrel_bits})
		self.is_zsb = True

	# Support for sokoban solvers

	# return list of all accessible (char_cell, barrel_cell) pairs valid for shift
	# should to be called after get_accessible_bits()
	def get_all_valid_char_barrel_shifts(self, accessible_bits=None):
		if accessible_bits is None:
			accessible_bits = self.last_accessible_bits
		cell_pairs = []
		for barrel_idx in search_bits(self.barrel_bits, _ONE):
			for char_idx in self.all_passable_neigh_idxs[barrel_idx]:
				if not accessible_bits[char_idx]:
					continue
				char_cell = self.idx_cells[char_idx]
				barrel_cell = self.idx_cells[barrel_idx]
				if self.can_shift(char_cell, barrel_cell):
					cell_pairs.append((char_cell, barrel_cell))
		return cell_pairs

grid = Grid()
