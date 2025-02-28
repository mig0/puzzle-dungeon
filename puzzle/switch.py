from . import *

class SwitchPuzzle(Puzzle):
	def init(self):
		self.load_map_special_cell_types[CELL_PLATE] = 'ints'

	def has_plate(self):
		return True

	def has_gate(self):
		return True

	def has_finish(self):
		return True

	def store_level(self, stored_level):
		stored_level["plate_cells"] = self.plate_cells
		stored_level["gate_cells"] = self.gate_cells
		stored_level["attached_gate_plate_idxs"] = self.attached_gate_plate_idxs

	def restore_level(self, stored_level):
		self.plate_cells = stored_level["plate_cells"]
		self.gate_cells = stored_level["gate_cells"]
		self.attached_gate_plate_idxs = stored_level["attached_gate_plate_idxs"]

	def update_gate_states(self):
		for gate_idx, gate_cell in enumerate(self.gate_cells):
			is_open = self.map[gate_cell] == CELL_GATE1
			be_open = self.Globals.is_cell_occupied(gate_cell)
			for plate_idx in self.attached_gate_plate_idxs[gate_idx]:
				plate_cell = self.plate_cells[plate_idx]
				if self.Globals.is_cell_occupied(plate_cell):
					be_open = True
			if is_open != be_open:
				self.Globals.toggle_gate(gate_cell)

	def on_set_room(self):
		self.plate_gate_cells = {}

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
			gate_idxs = special_cell_values[plate_cell]
			self.attached_plate_gate_idxs.append(gate_idxs)

		self.attached_gate_plate_idxs = []
		for gate_idx in range(len(gate_cells)):
			plate_idxs = [ plate_idx for plate_idx, gate_idxs in enumerate(self.attached_plate_gate_idxs) if gate_idx in gate_idxs ]
			self.attached_gate_plate_idxs.append(plate_idxs)

	def on_enter_room(self):
		self.update_gate_states()

	def on_prepare_enter_cell(self):
		self.update_gate_states()
