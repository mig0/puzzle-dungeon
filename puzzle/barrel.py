from . import *
import bisect

MIN_SOLUTION_DEPTH = 5
MAX_SOLUTION_DEPTH = 500
SOLUTION_DEPTH_STEP = 5
MAX_FIND_SOLUTION_TIME = 25 * 60 * 60

SOLUTION_TYPE_BY_SHIFTS = 1
SOLUTION_TYPE_BY_MOVES = 2

SOLUTION_ALG_DFS   = "DFS"
SOLUTION_ALG_BFS   = "BFS"
SOLUTION_ALG_PQ    = "PQ"
SOLUTION_ALG_ASTAR = "A*"

FLOOR_COST = 1
CHAR_FLOOR_COST = -1
WALL_COST = 100
OBSTACLE_COST = None

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
			self._solution_cost = game.puzzle.get_min_solution_depth(self.barrel_cells) or 0
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
		game.puzzle.num_created_positions += 1
		debug([self.depth], DBG_SOLV2, "Created %s" % self)

	@property
	def nums_str(self):
		return "%d/%d" % (self.total_nums[0], self.total_nums[1])

	@property
	def is_solved(self):
		return self.super.is_solved

	def cmp(self, pos2):
		total_nums2 = pos2 if type(pos2) == tuple else pos2.total_nums
		(m1, s1), (m2, s2), stype = self.total_nums, total_nums2, game.puzzle.solution_type
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
			own_cost = m + s * (3 if game.puzzle.solution_type == SOLUTION_TYPE_BY_SHIFTS else 0)
			self._solution_cost = own_cost // (self.depth + 1) + self.super.solution_cost * 8
		return self._solution_cost

	def to_solution_pairs(self):
		solution_pairs = self.parent.to_solution_pairs() if self.parent else []
		for path_cells, char_cell, barrel_cell in self.segments:
			solution_pairs.append([path_cells, DIR_NAMES[cell_diff(char_cell, barrel_cell, flags.is_reverse_barrel, True)]])
		return solution_pairs

	def __str__(self):
		return "{◰[%d] %s ☻%s ■%s}" % \
			(self.depth, self.nums_str, self.char_cell, ' '.join(map(str, self.super.barrel_cells)))

class BarrelPuzzle(Puzzle):
	def init(self):
		self.is_zsb = False
		self.solution_alg = SOLUTION_ALG_BFS
		self.disable_budget_solution = False
		self.disable_prepare_solution = False
		self.orig_barrels_stack = []

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
		return MOVE_V if self.area.is_cell_evnodd(cell) else MOVE_H if self.area.is_cell_oddevn(cell) else self.die("No anchor argument")

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
				if target_cell in barrel_cells or self.map[target_cell] in CELL_CHAR_MOVE_OBSTACLES:
					continue
				if not self.is_zsb_graph_connected([cell for cell in barrel_cells if cell != barrel_cell] + [target_cell]):
					continue
				all_barrel_moves.append((barrel_cell, target_cell))
		return all_barrel_moves

	def get_all_valid_zsb_char_barrel_moves(self):
		return [[apply_diff(barrel_cell, cell_dir(target_cell, barrel_cell), flags.is_reverse_barrel), barrel_cell]
			for barrel_cell, target_cell in self.get_all_valid_zsb_barrel_moves(self.barrel_cells)]

	def max_valid_zsb_barrel_shuffle(self, barrel_cells, num_moves):
		orig_barrel_cells = barrel_cells
		barrel_cells = barrel_cells.copy()
		max_barrel_cells = orig_barrel_cells
		max_total_distance = 0
		for _ in range(num_moves):
			barrel_cell, target_cell = choice(self.get_all_valid_zsb_barrel_moves(barrel_cells))
			barrel_cells[barrel_cells.index(barrel_cell)] = target_cell
			total_distance = sum(cell_distance(cell1, cell2) for cell1, cell2 in zip(barrel_cells, orig_barrel_cells))
			if total_distance > max_total_distance:
				max_barrel_cells = barrel_cells.copy()
				max_total_distance = total_distance
		return max_barrel_cells

	def generate_random_zsb_room(self):
		if not self.is_valid_zsb_area_size():
			self.die("Invalid area size %s for Zero Space type-B puzzle" % str(self.area.size))
		self.set_area_border_walls(0)

		zsb_size = self.get_zsb_size()
		num_barrels = zsb_size[0] * zsb_size[1] - 1
		all_anchor_cells = self.get_all_zsb_anchor_cells()
		debug(2, "Generating Zero Space type-B puzzle %s with %d barrels" % (self.get_zsb_size_str(), num_barrels))

		# 1) initialize zsb walls
		for cell in self.get_zsb_wall_cells():
			self.map[cell] = CELL_WALL

		# 2) create random barrels and plates until both are connected and correspond to each other
		while True:
			barrel_cells = sample(all_anchor_cells, k=num_barrels)
			if not self.is_zsb_graph_connected(barrel_cells):
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

	def check_zsb(self):
		self.is_zsb = False
		zsb_size = self.get_zsb_size()
		num_barrels = zsb_size[0] * zsb_size[1] - 1

		# check valid area size
		if not self.is_valid_zsb_area_size():
			return

		# check that walls are only on odd-odd cells and nowhere else
		for cell in self.area.cells:
			is_wall_cell = self.area.is_cell_oddodd(cell)
			if is_wall_cell and self.map[cell] != CELL_WALL or not is_wall_cell and not self.map[cell] in (*CELL_FLOOR_TYPES, CELL_PLATE):
				debug(3, "Cell %s must%s be WALL for ZSB, but it is '%s', concluding no ZSB" % (str(cell), "" if is_wall_cell else " NOT", self.map[cell]))
				return

		# check number and connectivity of barrels and plates
		for archor_cells in (self.stock_barrel_cells, self.plate_cells):
			if len(archor_cells) != num_barrels:
				return
			for cell in archor_cells:
				if not self.is_zsb_anchor_cell(cell):
					return
			if not self.is_zsb_graph_connected(archor_cells):
				return

		# check correspondence of barrels and plates
		if not self.is_zsb_correspondence(self.stock_barrel_cells, self.plate_cells):
			return

		self.is_zsb = True

	def check_special_setups(self):
		self.check_zsb()
		reverse_str = " reverse" if flags.is_reverse_barrel else ""
		if self.is_zsb:
			msg = "This is Zero Space type-B %s%s puzzle!" % (self.get_zsb_size_str(), reverse_str)
		else:
			msg = "This is Sokoban%s puzzle" % reverse_str
		set_status_message(msg, self)

	def reset_solution_data(self):
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
		self.stock_char_cell = char.c
		self.stock_barrel_cells = self.get_room_barrel_cells()
		self.has_extra_barrels = len(self.plate_cells) < len(barrels)
		self.has_extra_plates  = len(self.plate_cells) > len(barrels)

		self.num_moves = 0
		self.num_shifts = 0

		self.reset_solution_data()
		self.check_special_setups()

	def get_room_plate_cells(self):
		return self.get_room_cells(CELL_PLATE)

	def get_room_barrels(self):
		return [ barrel for barrel in barrels if is_actor_in_room(barrel) ]

	def get_room_barrel_cells(self):
		return sort_cells([ barrel.c for barrel in self.get_room_barrels() ])

	def get_min_solution_depth(self, barrel_cells):
		solution_depth = 0
		for barrel_cell in barrel_cells:
			num_shifts = grid.min_barrel_plate_shifts[min(grid.min_barrel_plate_shifts.keys(), key=lambda cell:
				grid.min_barrel_plate_shifts[cell] if cell == barrel_cell else grid.num_bits
			)] if grid.min_barrel_plate_shifts else grid.num_bits
			solution_depth += num_shifts

		return solution_depth

	def estimate_solution_depth(self):
		if (solution_depth := self.get_min_solution_depth(self.get_room_barrel_cells())) is None:
			return MIN_SOLUTION_DEPTH

		solution_depth = max(solution_depth, MIN_SOLUTION_DEPTH)

		if self.solution_alg != SOLUTION_ALG_DFS:
			return solution_depth
		return ((solution_depth - MIN_SOLUTION_DEPTH - 1) // SOLUTION_DEPTH_STEP + 1) * SOLUTION_DEPTH_STEP + MIN_SOLUTION_DEPTH

	def find_or_create_super_position(self, char_cell, barrel_cells):
		if self.is_zsb:
			accessible_cells = None
			super_position_id = (*barrel_cells,)
		else:
			accessible_cells = grid.get_accessible_cells(char_cell, barrel_cells)
			super_position_id = (frozenset(accessible_cells), *barrel_cells)

		if super_position_id in self.visited_super_positions:
			return self.visited_super_positions[super_position_id]

		grid.set_barrels(barrel_cells)
		if self.is_zsb:
			accessible_cells_near_barrels = self.get_all_valid_zsb_char_barrel_moves()
		else:
			accessible_cells_near_barrels = grid.get_all_valid_char_barrel_shifts()

		accessible_cells_near_barrels.sort(key=lambda two_cells: grid.min_char_barrel_plate_shifts.get(two_cells, grid.num_bits) or grid.num_bits)
		all_proto_segments = tuple([(None, char_cell, barrel_cell)] for char_cell, barrel_cell in accessible_cells_near_barrels)
		if self.is_zsb:
			for proto_segments in all_proto_segments:
				_, char_cell, barrel_cell = proto_segments[0]
				if flags.is_reverse_barrel:
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
			self.char_cell = char_cell
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

		if not self.disable_budget_solution and time() > self.budget_solution_time:
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
			return True

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
		return game.in_level and self.is_solved_for_barrel_cells([ barrel.c for barrel in self.get_room_barrels() ])

	def get_cell_image_to_draw(self, cell, cell_type):
		if cell_type == CELL_FLOOR and grid.is_dead_barrel(cell):
			return self.red_floor_image

	def on_press_key(self, keyboard):
		if keyboard.ralt and not solution.is_find_mode():
			if keyboard.a:
				self.solution_alg = SOLUTION_ALG_ASTAR
			if keyboard.b:
				self.solution_alg = SOLUTION_ALG_BFS
			if keyboard.d:
				self.solution_alg = SOLUTION_ALG_DFS
			if keyboard.p:
				self.solution_alg = SOLUTION_ALG_PQ
			if keyboard.minus:
				self.disable_prepare_solution = not self.disable_prepare_solution
			if keyboard.k_0:
				self.disable_budget_solution = not self.disable_budget_solution
			msg = "Going to use solution algorithm %s; budget of 1s is %s; prepare is %s" % (self.solution_alg,
				("disabled" if self.disable_budget_solution else "enabled"),
				("disabled" if self.disable_prepare_solution else "enabled"),
			)
			set_status_message(msg, self, None, 4)
			return
		if keyboard.e and keyboard.alt:
			game.level.reverse_barrel_mode = not game.level.reverse_barrel_mode
			game.set_requested_new_level(None, True)
		if keyboard.kp_enter:
			if solution.is_active() and ((self.solution_type == SOLUTION_TYPE_BY_MOVES) ^ keyboard.shift):
				solution.reset()
			if not solution.is_active() and not solution.is_find_mode():
				self.solution_type = SOLUTION_TYPE_BY_MOVES if keyboard.shift else SOLUTION_TYPE_BY_SHIFTS

	def on_enter_cell(self):
		self.num_moves += 1
		self.num_shifts += game.last_char_move.is_barrel_shift

	def on_draw(self):
		game.screen.draw.text("%d/%d" % (self.num_moves, self.num_shifts), center=(CELL_W * 1.5, CELL_H * 0.5), color="#00FFAA", gcolor="#00AA66", owidth=2, ocolor="#3C403C", alpha=1, fontsize=27)

	def get_found_solution_items(self, reason):
		solution_items = None
		if self.solved_position:
			solution_items = [item for pair in self.solved_position.to_solution_pairs() for item in pair]
		debug(DBG_SOLV, "Finding solution %s, returning %s solution" % (reason, self.solved_position.nums_str if self.solved_position else "no"))
		self.reset_solution_data()
		return solution_items

	def get_find_solution_status_str(self):
		time_str = get_time_str(time() - self.start_solution_time)
		status_str = "Finding %s optimal solution" % ("move" if self.solution_type == SOLUTION_TYPE_BY_MOVES else "push")
		status_str += "; %s" % time_str
		if self.solution_alg in (SOLUTION_ALG_DFS, SOLUTION_ALG_BFS):
			status_str += "; depth %d" % self.solution_depth
		status_str += "; positions: %d" % self.num_processed_positions
		if self.solution_alg in (SOLUTION_ALG_BFS, SOLUTION_ALG_PQ, SOLUTION_ALG_ASTAR):
			status_str += " + %d" % len(self.unprocessed_positions)
		if self.solved_position:
			status_str += "; found %s" % self.solved_position.nums_str
		debug(DBG_SOLV, status_str + "; sp: %d p: %d" % (len(self.visited_super_positions), self.num_created_positions))
		return (status_str, self.barrel_spinner)

	def find_solution_func(self):
		self.budget_solution_time = time() + 1

		if not self.initial_position:
			# preparing to find solution
			self.start_solution_time = time()
			self.end_solution_time = time() + MAX_FIND_SOLUTION_TIME
			grid.configure(game.map, flags.is_reverse_barrel)
			grid.prepare_sokoban_solution(self.disable_prepare_solution)
			if self.solution_alg in (SOLUTION_ALG_DFS, SOLUTION_ALG_BFS):
				self.solution_depth = self.estimate_solution_depth()
			game.puzzle = self
			super_position = self.find_or_create_super_position(char.c, tuple(self.get_room_barrel_cells()))
			self.initial_position = Position(super_position, char.c, None, None, None)
			self.unprocessed_positions = [self.initial_position]
			if self.solution_alg == SOLUTION_ALG_PQ:
				self.sort_positions = lambda position: position.total_nums
			if self.solution_alg == SOLUTION_ALG_ASTAR:
				self.sort_positions = lambda position: position.solution_cost
			return None, self.get_find_solution_status_str()

		if solution.stop_find or self.solution_depth > MAX_SOLUTION_DEPTH or time() > self.end_solution_time:
			return self.get_found_solution_items("terminated"), None

		debug([0], DBG_SOLV, "Using %s%s" % (self.solution_alg, " up to depth %d" % self.solution_depth if self.solution_depth < MAX_SOLUTION_DEPTH else ""))

		is_finished = (
			self.find_solution_using_dfs() if self.solution_alg == SOLUTION_ALG_DFS else
			self.find_solution_using_bfs() if self.solution_alg == SOLUTION_ALG_BFS else
			self.find_solution_using_pq()
		)

		if is_finished:
			return self.get_found_solution_items("finished"), None

		# solution in progress
		if is_finished is False:
			if self.solution_alg == SOLUTION_ALG_BFS:
				self.solution_depth += 1
			elif self.solution_alg == SOLUTION_ALG_DFS:
				self.solution_depth += SOLUTION_DEPTH_STEP
		return None, self.get_find_solution_status_str()

	def prepare_solution(self):
		return ("Preparing to find solution", self.find_solution_func)

