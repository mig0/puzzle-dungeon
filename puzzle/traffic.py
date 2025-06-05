from . import *

class TrafficPuzzle(Puzzle):
	def has_gate(self):
		return True

	def is_goal_to_be_solved(self):
		return True

	def on_set_room(self):
		self.set_area_from_config(default_size=DEFAULT_TRAFFIC_PUZZLE_SIZE, align_to_center=True)

	def generate_random_nonsolvable_room(self):
		num_targets_left = self.num_targets
		color_idx = 0
		self.exit_color_idxs = {}
		for _ in range(self.area.num_cells - self.num_free_cells):
			cell = self.get_random_matching_cell_in_area([CELL_VOID], [lift.c for lift in lifts])
			lift_type = LIFT_V if randint(0, 1) == 0 else LIFT_H
			self.Globals.create_lift(cell, lift_type)
			lift = lifts[-1]
			if num_targets_left > 0:
				exit_cell = (self.area.x1 - 1, lift.cy) if lift_type == LIFT_H else (lift.cx, self.area.y1 - 1)
				if exit_cell not in self.exit_color_idxs:
					self.exit_color_idxs[exit_cell] = color_idx
					color_idx = (color_idx + 1) % len(EXTENDED_COLOR_RGB_VALUES)
				lift.color = EXTENDED_COLOR_RGB_VALUES[self.exit_color_idxs[exit_cell]]
				num_targets_left -= 1

	def generate_room(self):
		self.num_free_cells = self.parse_config_num("num_free_cells", 2)
		self.num_targets = self.parse_config_num("num_targets", 1)
		self.set_area_cells(CELL_VOID, add_border_walls=True)

		self.generate_random_nonsolvable_room()

	def on_set_theme(self):
		self.color_void_images = []
		gray_void_image = make_grayscale_image(self.Globals.load_theme_cell_image('floor'))
		for color_idx in range(len(self.exit_color_idxs)):
			color = EXTENDED_COLOR_RGB_VALUES[color_idx % len(EXTENDED_COLOR_RGB_VALUES)]
			self.color_void_images.append(colorize_image(gray_void_image.copy(), color))

	def get_cell_image_to_draw(self, cell, cell_type):
		if cell in self.exit_color_idxs:
			return self.color_void_images[self.exit_color_idxs[cell]]
		return None
