from . import *

class SwitchBoxPuzzle(Puzzle):
	def init(self):
		self.load_map_special_cell_types[CELL_PLATE] = 'ints'
		self.hide_colors = self.config.get("hide_colors", False)

	def has_plate(self):
		return True

	def has_gate(self):
		return True

	def has_finish(self):
		return True

	def get_object_color_idx(self, plate_idxs):
		if not plate_idxs:
			return None
		plate_idx = plate_idxs[0]
		color_idx = self.plate_color_idxs[plate_idx]
		if color_idx is None:
			return None
		return color_idx

	def get_plate_color_image(self, plate_idx):
		if type(plate_idx) == tuple:
			plate_idx = self.plate_cells.index(plate_idx)
		color_idx = self.plate_color_idxs[plate_idx]
		if color_idx is None:
			return None
		return self.color_floor_images[color_idx]

	def get_gate_color_image(self, gate_idx):
		if type(gate_idx) == tuple:
			gate_idx = self.gate_cells.index(gate_idx)
		color_idx = self.get_object_color_idx(self.attached_gate_plate_idxs[gate_idx])
		if color_idx is None:
			return None
		return self.color_floor_images[color_idx]

	def get_barrel_color(self, barrel_idx):
		if type(barrel_idx) == CellActor:
			barrel_idx = barrels.index(barrel_idx)
		color_idx = self.get_object_color_idx(self.attached_barrel_plate_idxs[barrel_idx])
		if color_idx is None:
			return None
		return EXTENDED_COLOR_RGB_VALUES[color_idx % len(EXTENDED_COLOR_RGB_VALUES)]

	def assign_object_colors(self):
		plate_gate_idxs = [[] for _ in range(len(self.plate_cells))]
		for gate_idx in range(len(self.gate_cells)):
			plate_idxs = self.attached_gate_plate_idxs[gate_idx]
			for plate_idx in plate_idxs:
				plate_gate_idxs[plate_idx].append(gate_idx)

		plate_barrel_idxs = [[] for _ in range(len(self.plate_cells))]
		for barrel_idx in range(len(barrels)):
			plate_idxs = self.attached_barrel_plate_idxs[barrel_idx]
			for plate_idx in plate_idxs:
				plate_barrel_idxs[plate_idx].append(barrel_idx)

		plate_seen_color_idxs = {}
		new_color_idx = 0
		self.plate_color_idxs = []
		for plate_idx in range(len(self.plate_cells)):
			plate_seen_key = tuple(plate_gate_idxs[plate_idx]) + (None,) + tuple(plate_barrel_idxs[plate_idx])
			if plate_seen_key == (None,):
				color_idx = None
			elif plate_seen_key in plate_seen_color_idxs:
				color_idx = plate_seen_color_idxs[plate_seen_key]
			else:
				color_idx = new_color_idx
				new_color_idx += 1
				plate_seen_color_idxs[plate_seen_key] = color_idx
			self.plate_color_idxs.append(color_idx)

	def switch_barrel_colors(self):
		for barrel in barrels:
			barrel.color = None if self.hide_colors else self.get_barrel_color(barrel)

	def on_set_theme(self):
		self.color_floor_images = []
		gray_floor_image = make_grayscale_image(self.Globals.load_theme_cell_image('floor'))
		for color_idx in range(len(self.plate_color_idxs)):
			color = EXTENDED_COLOR_RGB_VALUES[color_idx % len(EXTENDED_COLOR_RGB_VALUES)]
			self.color_floor_images.append(colorize_image(gray_floor_image.copy(), color))

		if not self.hide_colors:
			self.switch_barrel_colors()

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
		self.assign_object_colors()

	def get_cell_image_to_draw(self, cell, cell_type):
		if self.hide_colors:
			return None
		if cell_type == CELL_FLOOR and self.map[cell] == CELL_PLATE:
			return self.get_plate_color_image(cell)
		if cell_type == CELL_FLOOR and self.map[cell] in (CELL_GATE0, CELL_GATE1):
			return self.get_gate_color_image(cell)
		return None

	def on_press_key(self, keyboard):
		if keyboard.c:
			self.hide_colors = not self.hide_colors
			self.switch_barrel_colors()

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

	def on_enter_room(self):
		set_status_message("Press 'c' to hide or show colors", self, 0, 12)

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

		self.assign_object_colors()

	def on_prepare_enter_cell(self):
		self.update_gate_and_barrel_states()
