from . import *

COLOR_MAP_VALUE_OUTSIDE = -1
COLOR_MAP_VALUE_SOLVED  = 1  # GREEN

class ColorPuzzle(Puzzle):
	def init(self):
		self.color_map = None
		self.cell_images = []

	def assert_config(self):
		return not flags.is_any_maze

	def has_plate(self):
		return True

	def is_goal_to_be_solved(self):
		return True

	def on_set_theme(self):
		gray_tiles_image = load_theme_cell_image('floor_gray_tiles')
		self.cell_images = []
		for color in MAIN_COLOR_RGB_VALUES:
			color_cell_image = colorize_cell_image(gray_tiles_image, color)
			self.cell_images.append(color_cell_image)

	def on_set_room(self):
		self.set_area_from_config(request_odd_size=True, align_to_center=True)

	def on_create_map(self):
		self.color_map = ndarray((MAP_SIZE_X, MAP_SIZE_Y), dtype=int)
		self.color_map.fill(COLOR_MAP_VALUE_OUTSIDE)

	def get_num_values(self):
		return self.config.get("num_values", DEFAULT_NUM_COLOR_PUZZLE_COLORS)

	def increment_cell_color(self, cell):
		self.color_map[cell] = (self.color_map[cell] + 1) % self.get_num_values()

	def press_plate(self, cell):
		for neigh in self.Globals.get_all_neighbors(cell, include_self=True):
			self.increment_cell_color(neigh)
			if "is_extended" in self.config and (neigh[0] != cell[0] and neigh[1] != cell[1]) ^ (cell[0] % 3 != 0 or cell[2] % 3 != 0):
				self.increment_cell_color(neigh)

	def get_cell_image(self, cell):
		return self.cell_images[self.color_map[cell]]

	def is_plate(self, cell):
		return self.map[cell] == CELL_PLATE

	def is_cell_for_plate(self, cell):
		return self.is_in_area(cell) and (cell[0] - self.area.x1) % 2 == 1 and (cell[1] - self.area.y1) % 2 == 1

	def is_solved(self):
		for cell in self.area.cells:
			if not self.is_plate(cell) and self.color_map[cell] != COLOR_MAP_VALUE_SOLVED:
				return False
		return True

	def store_level(self, stored_level):
		stored_level["color_map"] = self.color_map.copy()

	def restore_level(self, stored_level):
		self.color_map = stored_level["color_map"]

	def get_cell_image_to_draw(self, cell, cell_type):
		if cell_type == CELL_FLOOR and not self.is_plate(cell) and self.color_map[cell] != COLOR_MAP_VALUE_OUTSIDE:
			return self.get_cell_image(cell)
		return None

	def get_all_plate_cells(self):
		return [cell for cell in self.area.cells if self.is_cell_for_plate(cell)]

	def generate_room(self):
		for cell in self.area.cells:
			self.color_map[cell] = COLOR_MAP_VALUE_SOLVED
			if self.is_cell_for_plate(cell):
				self.map[cell] = CELL_PLATE
		num_tries = 5
		while num_tries > 0:
			for plate_cell in self.get_all_plate_cells():
				for i in range(randint(0, self.get_num_values() - 1)):
					self.press_plate(plate_cell)
			if not self.is_solved():
				break
			num_tries -= 1

	def press_cell(self, cell, button=None):
		if not self.is_in_area(cell):
			return False

		if self.is_plate(cell):
			self.press_plate(cell)

		return True

	def find_solution_func(self):
		solution_items = []
		for plate_cell in self.get_all_plate_cells():
			for i in range((COLOR_MAP_VALUE_SOLVED - self.color_map[plate_cell]) % self.get_num_values()):
				solution_items.append(plate_cell)
		shuffle(solution_items)  # optionally randomize the solution
		return solution_items, None

	def prepare_solution(self):
		return ("Finding solution", self.find_solution_func)

