from . import *
from bitarray import frozenbitarray
from functools import reduce
from operator import xor, or_

def shortstr(obj):
	return str(obj) \
		.replace("frozenbitarray('", "'") \
		.replace("')", "'") \
		.replace(",)", ")")

class Solution():
	def __init__(self, open_gates=None, used_plates=set(), passed_gates=set(), visited_spans=set(), pressed_plates=()):
		self.open_gates = open_gates
		self.used_plates = used_plates
		self.passed_gates = passed_gates
		self.visited_spans = visited_spans
		self.pressed_plates = pressed_plates

	def update_copy(self, new_open_gate_bits, plate_idxs, gate_idx, span_idx, pressed_plate_idxs):
		return Solution(
			new_open_gate_bits if self.open_gates is None else self.open_gates | new_open_gate_bits,
			self.used_plates | set(plate_idxs),
			self.passed_gates | set((gate_idx,)),
			self.visited_spans | set((span_idx,)),
			pressed_plate_idxs + self.pressed_plates,
		)

	def __str__(self):
		return "open_gates=%s used_plates=%s passed_gates=%s visited_spans=%s pressed_plates=%s" % \
			(self.open_gates, self.used_plates, self.passed_gates, self.visited_spans, self.pressed_plates)

class SpanModel:
	def __init__(self, spans, num_plates, num_gates, Globals):
		self.spans = spans
		self.num_plates = num_plates
		self.num_gates = num_gates
		self.Globals = Globals
		pass

	def validate_spans(self):
		plate_idxs = set()
		all_plate_idxs = set(range(self.num_plates))
		for span in self.spans:
			span_plate_idxs = span[0]
			if plate_idxs.intersection(span_plate_idxs):
				return False
			plate_idxs.update(span_plate_idxs)
		if plate_idxs != all_plate_idxs:
			return False
		return True

	def find_solution(self, depth, span_idx, open_gate_bits):
		if depth == 0:
			if not self.spans:
				return Solution()
			if not self.validate_spans():
				self.Globals.debug(3, "Fail solution for invalid spans: %s" % shortstr(self.spans))
				return False

			self.visited_span_open_gates = {}
			self.unfinished_span_open_gates = []

		self.Globals.debug(3, depth=depth, str="span=%d open_gates=%s" % (span_idx, open_gate_bits.to01()))

		visited_key = (span_idx, open_gate_bits)

		if visited_key in self.visited_span_open_gates:
			self.Globals.debug(4, depth=depth, str="-> found: %s" % self.visited_span_open_gates[visited_key])
			return self.visited_span_open_gates[visited_key]

		if span_idx == -1:
			solution = Solution()
			self.Globals.debug(4, depth=depth, str="-> finish: %s" % shortstr(solution))
			self.visited_span_open_gates[visited_key] = solution
			return solution

		self.unfinished_span_open_gates.append(visited_key)

		plate_idxs, combined_plate_idxs_to_gate_bits, gate_adj_span_idxs, guide_span_idx = self.spans[span_idx]

		best_solution = None
		best_new_open_gate_bits = None
		best_combined_plate_idxs = ()
		best_gate_idx = None
		is_unknown = False

		for combined_plate_idxs, gate_bits_pair in combined_plate_idxs_to_gate_bits.items():
			combined_gate_bits, toggled_gate_bits = gate_bits_pair
			orig_open_gate_bits = open_gate_bits
			open_gate_bits = open_gate_bits ^ combined_gate_bits
			new_open_gate_bits = open_gate_bits & toggled_gate_bits | combined_gate_bits ^ toggled_gate_bits

			for gate_idx, adj_span_idxs in gate_adj_span_idxs.items():
				if not open_gate_bits[gate_idx]:
					continue
				for adj_span_idx in adj_span_idxs:
					if (adj_span_idx, open_gate_bits) in self.unfinished_span_open_gates and adj_span_idx != guide_span_idx:
						continue
					solution = self.find_solution(depth + 1, adj_span_idx, open_gate_bits)
					if not solution:
						continue

					if not best_solution or len(solution.pressed_plates) + len(combined_plate_idxs) < len(best_solution.pressed_plates) + len(best_combined_plate_idxs):
						best_solution = solution
						best_new_open_gate_bits = new_open_gate_bits
						best_combined_plate_idxs = combined_plate_idxs
						best_gate_idx = gate_idx

			open_gate_bits = orig_open_gate_bits

		self.unfinished_span_open_gates.pop()

		if not best_solution:
			self.Globals.debug(4, depth=depth, str="-> no solution")
			self.visited_span_open_gates[visited_key] = None
			return None

		solution = best_solution.update_copy(best_new_open_gate_bits, best_combined_plate_idxs, best_gate_idx, span_idx, best_combined_plate_idxs)
		self.Globals.debug(4, depth=depth, str="-> %s" % shortstr(solution))
		if depth == 0:
			self.Globals.debug(3, "[solution] plates: %d of %d, gates: %d of %d, spans: %d of %d, states: %d" % (
				len(solution.used_plates), self.num_plates,
				len(solution.passed_gates), self.num_gates,
				len(solution.visited_spans), len(self.spans), len(self.visited_span_open_gates))
			)

		self.visited_span_open_gates[visited_key] = solution

		return solution

	def __str__(self):
		return "plates=%d gates=%d spans=%s" % \
			(self.num_plates, self.num_gates, shortstr(self.spans))

class GatePuzzle(Puzzle):
	def init(self):
		self.load_map_special_cell_types[CELL_PLATE] = 'ints'

	def assert_config(self):
		return flags.is_any_maze

	def is_long_generation(self):
		return True

	def is_finish_cell_required(self):
		return True

	def has_plate(self):
		return True

	def has_gate(self):
		return True

	def on_create_map(self):
		self.room_values = [[None, None, None, None, None, None] for _ in range(flags.NUM_ROOMS)]

	@property
	def num_plates(self):
		return self.room_values[self.room.idx][0]

	@num_plates.setter
	def num_plates(self, num_plates):
		self.room_values[self.room.idx][0] = num_plates

	@property
	def num_gates(self):
		return self.room_values[self.room.idx][1]

	@num_gates.setter
	def num_gates(self, num_gates):
		self.room_values[self.room.idx][1] = num_gates

	@property
	def finish_cell(self):
		return self.room_values[self.room.idx][2]

	@finish_cell.setter
	def finish_cell(self, finish_cell):
		self.room_values[self.room.idx][2] = finish_cell

	@property
	def plate_cells(self):
		return self.room_values[self.room.idx][3]

	@plate_cells.setter
	def plate_cells(self, plate_cells):
		self.room_values[self.room.idx][3] = plate_cells

	@property
	def gate_cells(self):
		return self.room_values[self.room.idx][4]

	@gate_cells.setter
	def gate_cells(self, gate_cells):
		self.room_values[self.room.idx][4] = gate_cells

	@property
	def attached_plate_gate_idxs(self):
		return self.room_values[self.room.idx][5]

	@attached_plate_gate_idxs.setter
	def attached_plate_gate_idxs(self, attached_plate_gate_idxs):
		self.room_values[self.room.idx][5] = attached_plate_gate_idxs

	def store_level(self, stored_level):
		stored_level["room_values"] = self.room_values

	def restore_level(self, stored_level):
		self.room_values = stored_level["room_values"]

	def get_all_gate_bits(self, value='0'):
		return frozenbitarray(value * self.num_gates)

	def get_attached_plate_gate_bits(self, plate_idx):
		return frozenbitarray([gate_idx in self.attached_plate_gate_idxs[plate_idx] for gate_idx in range(self.num_gates)])

	def create_combined_plate_idxs_to_gate_bits(self, plate_idxs):
		combined_plate_idxs_to_gate_bits = {}
		for num in range(1 << len(plate_idxs)):
			selected_plate_idxs = tuple(plate_idxs[idx] for idx in range(len(plate_idxs)) if num & (1 << idx))
			all_attached_gate_bits = [self.get_all_gate_bits()] if num == 0 else \
				[self.get_attached_plate_gate_bits(plate_idx) for plate_idx in selected_plate_idxs]
			combined_gate_bits = reduce(xor, all_attached_gate_bits)
			toggled_gate_bits = reduce(or_, all_attached_gate_bits)
			combined_plate_idxs_to_gate_bits[selected_plate_idxs] = (combined_gate_bits, toggled_gate_bits)
		return combined_plate_idxs_to_gate_bits

	def create_span_model(self, start_cell, finish_cell, plate_cells, gate_cells):
		spans = []
		processed_span_cells = {}
		all_processed_cells = []
		all_gate_span_idxs = {}  # {gate_cell: [span_idxs]}
		all_empty_spans = {}  # {(sorted_gate_cell1, sorted_gate_cell2): span_idx}

		unprocessed_start_cells = [start_cell]
		while unprocessed_start_cells:
			span_idx = len(spans)
			start_cell = unprocessed_start_cells.pop(0)
			if type(start_cell) == list:
				accessible_cells = []
				adj_gate_cells = [start_cell[0], start_cell[1]]
				processed_span_cells[span_idx] = []
				span_plate_idxs = []
			else:
				self.Globals.start_accessible_obstacles()
				accessible_cells = self.Globals.get_accessible_cells(start_cell, gate_cells)
				adj_gate_cells = self.Globals.clear_accessible_obstacles()
				if span_idx == 0 and self.finish_cell in accessible_cells:
					break
				processed_span_cells[span_idx] = accessible_cells
				all_processed_cells.extend(accessible_cells)
				span_plate_idxs = [plate_cells.index(cell) for cell in accessible_cells if cell in plate_cells]
				span_plate_idxs.sort()
			span_gate_adj_span_idxs = {}
			for gate_cell in adj_gate_cells:
				gate_idx = gate_cells.index(gate_cell)
				if gate_idx in all_gate_span_idxs:
					gate_span_idxs = all_gate_span_idxs[gate_idx]
				else:
					gate_span_idxs = [span_idx]
					for gate_next_cell in self.Globals.get_accessible_neighbors(gate_cell, allow_enemy=True, allow_closed_gate=True):
						if gate_next_cell in accessible_cells:
							continue
						if gate_next_cell in gate_cells:
							gate_pair_cells = [gate_cell, gate_next_cell]
							sorted_gate_pair_cells = tuple(sorted(gate_pair_cells))
							if sorted_gate_pair_cells in all_empty_spans:
								adj_span_idx = all_empty_spans[sorted_gate_pair_cells]
							else:
								unprocessed_start_cells.append(gate_pair_cells)
								adj_span_idx = span_idx + len(unprocessed_start_cells)
								all_empty_spans[sorted_gate_pair_cells] = adj_span_idx
						elif self.Globals.is_path_found(gate_next_cell, finish_cell, gate_cells):
							adj_span_idx = -1
						elif gate_next_cell in all_processed_cells:
							adj_span_idx = [span_idx for span_idx, cells in processed_span_cells.items() if gate_next_cell in cells][0]
						else:
							unprocessed_start_cells.append(gate_next_cell)
							adj_span_idx = span_idx + len(unprocessed_start_cells)
						if adj_span_idx not in gate_span_idxs:
							gate_span_idxs.append(adj_span_idx)
							gate_span_idxs.sort()
					all_gate_span_idxs[gate_idx] = gate_span_idxs
				gate_adj_span_idxs = gate_span_idxs.copy()
				gate_adj_span_idxs.remove(span_idx)
				span_gate_adj_span_idxs[gate_idx] = gate_adj_span_idxs
			span_combined_plate_idxs_to_gate_bits = self.create_combined_plate_idxs_to_gate_bits(span_plate_idxs)
			spans.append((span_plate_idxs, span_combined_plate_idxs_to_gate_bits, span_gate_adj_span_idxs))

		# update spans with guide_span_idx closest to finish per each span
		unprocessed_span_idxs = list(range(len(spans)))
		while unprocessed_span_idxs:
			for span_idx in unprocessed_span_idxs.copy():
				for adj_span_idxs in spans[span_idx][2].values():
					for adj_span_idx in adj_span_idxs:
						if adj_span_idx == -1 or len(spans[adj_span_idx]) == 4:
							spans[span_idx] += (adj_span_idx,)
							unprocessed_span_idxs.remove(span_idx)
							break

		return SpanModel(spans, len(plate_cells), len(gate_cells), self.Globals)

	def find_solution(self, span_model, init_open_gate_bits):
		solution = span_model.find_solution(0, 0, init_open_gate_bits)
		self.Globals.debug(2, "Found solution: %s" % shortstr(solution) if solution else "No solution found")
		return solution

	def find_map_solution(self, start_cell):
		span_model = self.create_span_model(start_cell, self.finish_cell, self.plate_cells, self.gate_cells)
		init_open_gate_bits = frozenbitarray([0 if self.map[gate_cell] == CELL_GATE0 else 1 for gate_cell in self.gate_cells])
		self.Globals.debug_map(2, descr="Checking solution for map", full_format=True)
		return self.find_solution(span_model, init_open_gate_bits)

	def find_decent_solution(self, start_cell):
		span_model = self.create_span_model(start_cell, self.finish_cell, self.plate_cells, self.gate_cells)
		self.num_spans = len(span_model.spans)

		for init_open_gate_n in range(1, 1 << self.num_gates):
			init_open_gate_bits = frozenbitarray([0 if init_open_gate_n & (1 << gate_idx) else 1 for gate_idx in range(self.num_gates)])
#			self.Globals.debug_map(2, descr="Checking solution for map with gate_bits=%s" % init_open_gate_bits, full_format=True)
			solution = self.find_solution(span_model, init_open_gate_bits)
			if (solution
				and (not self.all_gates_to_open or solution.open_gates == self.get_all_gate_bits('1'))
				and len(solution.used_plates) >= self.num_plates
				and len(solution.passed_gates) >= self.num_gates
				and len(solution.visited_spans) >= self.num_spans
				and len(solution.pressed_plates) >= self.num_plates_to_press
			):
				solution.init_open_gate_bits = init_open_gate_bits
				return solution

		return None

	def toggle_gate(self, cell):
		self.Globals.toggle_gate(cell)

	def press_plate(self, cell):
		if self.map[cell] != CELL_PLATE:
			return
		plate_idx = self.plate_cells.index(cell)
		for gate_idx in self.attached_plate_gate_idxs[plate_idx]:
			self.toggle_gate(self.gate_cells[gate_idx])

	def generate_random_solvable_room(self, accessible_cells, finish_cell):
		self.num_plates = self.parse_config_num("num_plates", DEFAULT_NUM_GATE_PUZZLE_PLATES)
		self.num_gates  = self.parse_config_num("num_gates",  DEFAULT_NUM_GATE_PUZZLE_GATES)
		self.num_plates_to_press = self.parse_config_num("num_plates_to_press", self.num_plates)
		self.all_gates_to_open = self.config.get("all_gates_to_open", False)

		def select_random_gates_attached_to_plate(num_gates):
			num_attached_gates = randint(MIN_GATE_PUZZLE_ATTACHED_GATES, MAX_GATE_PUZZLE_ATTACHED_GATES)
			if num_attached_gates > num_gates:
				num_attached_gates = num_gates
			attached_gate_idxs = []
			while len(attached_gate_idxs) < num_attached_gates:
				gate_idx = randint(0, num_gates - 1)
				if gate_idx in attached_gate_idxs:
					continue
				attached_gate_idxs.append(gate_idx)
			return attached_gate_idxs

		try_n = 1
		while try_n <= 100000:
			plate_cells = []
			for _ in range(self.num_plates):
				while True:
					cell = accessible_cells[randint(0, len(accessible_cells) - 1)]
					if cell in plate_cells:
						continue
					plate_cells.append(cell)
					break
			plate_cells = sort_cells(plate_cells)

			target_cells = [char.c, finish_cell, *plate_cells]

			gate_cells = []
			for _ in range(self.num_gates):
				while True:
					cell = accessible_cells[randint(0, len(accessible_cells) - 1)]
					if cell in target_cells:
						continue
					if self.Globals.get_num_accessible_target_directions(cell, target_cells) < 2:
						continue
					target_cells.append(cell)
					gate_cells.append(cell)
					break
			gate_cells = sort_cells(gate_cells)

			self.attached_plate_gate_idxs = []
			toggled_gate_idxs = set()
			for _ in range(self.num_plates):
				gate_idxs = select_random_gates_attached_to_plate(self.num_gates)
				toggled_gate_idxs.update(gate_idxs)
				self.attached_plate_gate_idxs.append(gate_idxs)

			# append all unused gates to a plate with the less attached gates
			unused_gate_idxs = [gate_idx for gate_idx in range(self.num_gates) if gate_idx not in toggled_gate_idxs]
			min_plate_idx = min(range(self.num_plates), key=lambda plate_idx: self.attached_plate_gate_idxs[plate_idx])
			self.attached_plate_gate_idxs[min_plate_idx].extend(unused_gate_idxs)

			self.Globals.debug(3, "Generating gate puzzle try=%d" % try_n)
			self.Globals.debug(3, "Attached plate gates: %s" % str(self.attached_plate_gate_idxs))
			self.finish_cell = finish_cell  # redundant, since it was already set
			self.plate_cells = plate_cells
			self.gate_cells = gate_cells
			solution = self.find_decent_solution(char.c)
			if solution:
				break

			try_n += 1
		else:
			print("Can't generate gate puzzle for %d plates and %d gates, sorry" % (self.num_plates, self.num_gates))
			quit()

		for plate_cell in plate_cells:
			self.map[plate_cell] = CELL_PLATE

		for gate_idx, gate_cell in enumerate(gate_cells):
			self.map[gate_cell] = CELL_GATE1 if solution.init_open_gate_bits[gate_idx] else CELL_GATE0

	def generate_room(self):
		self.generate_random_solvable_room(self.accessible_cells, self.finish_cell)

	def on_load_map(self, special_cell_values, extra_values):
		plate_cells = self.get_map_cells(CELL_PLATE)
		gate_cells = self.get_map_cells(CELL_GATE0, CELL_GATE1)

		self.num_plates = len(plate_cells)
		self.num_gates = len(gate_cells)
		self.finish_cell = self.get_map_cells(CELL_FINISH)[0]
		self.plate_cells = plate_cells
		self.gate_cells = gate_cells

		self.attached_plate_gate_idxs = []
		for plate_cell in sort_cells(special_cell_values.keys()):
			plate_gate_idxs = special_cell_values[plate_cell]
			self.attached_plate_gate_idxs.append(plate_gate_idxs)
			if len(self.attached_plate_gate_idxs) >= self.num_plates:
				break

	def get_map_extra_values(self):
		return self.attached_plate_gate_idxs

	def press_cell(self, cell, button=None):
		self.press_plate(char.c)

	def find_solution_func(self):
		solution = self.find_map_solution(char.c)
		if solution:
			solution_items = []
			for plate_cell in (self.plate_cells[plate_idx] for plate_idx in solution.pressed_plates):
				solution_items.append({plate_cell})
				solution_items.append(plate_cell)
			solution_items.append({self.finish_cell})
			return solution_items, None
		return None, None

	def prepare_solution(self):
		return ("Preparing to find solution", self.find_solution_func)

