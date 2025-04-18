from . import *

class SwitchBoxPuzzle(Puzzle):
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
		stored_level["attached_barrel_plate_idxs"] = self.attached_barrel_plate_idxs

	def restore_level(self, stored_level):
		self.plate_cells = stored_level["plate_cells"]
		self.gate_cells = stored_level["gate_cells"]
		self.attached_gate_plate_idxs = stored_level["attached_gate_plate_idxs"]
		self.attached_barrel_plate_idxs = stored_level["attached_barrel_plate_idxs"]

	def is_plate_pressed(self, plate_idx):
		plate_cell = self.plate_cells[plate_idx]
		return self.Globals.is_cell_occupied(plate_cell, include_phased=True)

	def is_object_triggered(self, is_triggered, plate_idxs):
		for plate_idx in plate_idxs:
			if self.is_plate_pressed(plate_idx):
				is_triggered = True
		return is_triggered

	def update_gate_and_barrel_states(self):
		for gate_idx, gate_cell in enumerate(self.gate_cells):
			is_open = self.map[gate_cell] == CELL_GATE1
			be_open = self.is_object_triggered(self.Globals.is_cell_occupied(gate_cell, include_phased=True), self.attached_gate_plate_idxs[gate_idx])
			if is_open != be_open:
				self.Globals.toggle_gate(gate_cell)

		for barrel_idx, barrel in enumerate(barrels):
			be_phased = self.is_object_triggered(barrel.c == char.c, self.attached_barrel_plate_idxs[barrel_idx])
			if be_phased != barrel.phased:
				self.Globals.toggle_actor_phased(barrel)

	def on_load_map(self, special_cell_values, extra_values):
		plate_cells = self.get_map_cells(CELL_PLATE)
		gate_cells = self.get_map_cells(CELL_GATE0, CELL_GATE1)

		self.num_plates = len(plate_cells)
		self.num_gates = len(gate_cells)
		self.finish_cell = self.get_map_cells(CELL_FINISH)[0]
		self.plate_cells = plate_cells
		self.gate_cells = gate_cells

		attached_plate_gate_idxs = []
		attached_plate_barrel_idxs = []
		for plate_cell in sort_cells(special_cell_values.keys()):
			idxs = special_cell_values[plate_cell]
			if None in idxs:
				none_idx = idxs.index(None)
				gate_idxs = idxs[0:none_idx]
				barrel_idxs = idxs[none_idx + 1:]
			else:
				gate_idxs = idxs
				barrel_idxs = []
			attached_plate_gate_idxs.append(gate_idxs)
			attached_plate_barrel_idxs.append(barrel_idxs)

		self.attached_gate_plate_idxs = []
		for gate_idx in range(len(gate_cells)):
			plate_idxs = [ plate_idx for plate_idx, gate_idxs in enumerate(attached_plate_gate_idxs) if gate_idx in gate_idxs ]
			self.attached_gate_plate_idxs.append(plate_idxs)

		self.attached_barrel_plate_idxs = []
		for barrel_idx in range(len(barrels)):
			plate_idxs = [ plate_idx for plate_idx, barrel_idxs in enumerate(attached_plate_barrel_idxs) if barrel_idx in barrel_idxs ]
			self.attached_barrel_plate_idxs.append(plate_idxs)

	def on_prepare_enter_cell(self):
		self.update_gate_and_barrel_states()
