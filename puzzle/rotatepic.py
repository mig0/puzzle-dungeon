from . import *

ROTATEPIC_PUZZLE_VALUE_OUTSIDE = -1
CLOCKWISE = -1
COUNTERCLOCKWISE = +1
UPSIDEDOWN = 2
CELL_ROTATEPIC_BOX = '~b'

class RotatepicPuzzle(Puzzle):
	def init(self):
		self.rotatepic_map = None
		self.image = None
		self.draw_solved_mode = False

	def assert_config(self):
		return not flags.is_any_maze

	def on_create_map(self):
		self.rotatepic_map = ndarray((MAP_SIZE_X, MAP_SIZE_X), dtype=int)
		self.rotatepic_map.fill(ROTATEPIC_PUZZLE_VALUE_OUTSIDE)

	def is_goal_to_be_solved(self):
		return True

	def get_real_rotatepic_map(self):
		return self.rotatepic_map[ix_(self.area.x_range, self.area.y_range)]

	def is_solved(self):
		real_rotatepic_map = self.get_real_rotatepic_map()
		for num in self.get_real_rotatepic_map().flat:
			if num != 0:
				return False
		return True

	def store_level(self, stored_level):
		stored_level["rotatepic_map"] = self.rotatepic_map.copy()

	def restore_level(self, stored_level):
		self.rotatepic_map = stored_level["rotatepic_map"]

	def on_set_room(self):
		self.set_area_from_config(min_size=(1, 1), align_to_center=True)
		self.max_num = self.area.size_x * self.area.size_y

	def on_enter_room(self):
		self.is_shared_bg = self.level.get("bg_image") is not None
		if not self.is_shared_bg:
			self.image = self.Globals.load_image(self.config.get("image", "bg/stonehenge.jpg"), (self.area.size_x * CELL_W, self.area.size_y * CELL_H), self.config.get("image_crop", False))

	def rotate_cell(self, cell, delta=COUNTERCLOCKWISE):
		if self.rotatepic_map[cell] == ROTATEPIC_PUZZLE_VALUE_OUTSIDE:
			return False

		self.rotatepic_map[cell] = (self.rotatepic_map[cell] + delta) % 4
		return True

	def scramble(self):
		for cell in self.area.cells:
			# make 0 to be twice less frequent than 1, 2 or 3
			delta = randint(1, 7) // 2
			self.rotate_cell(cell, delta)

	def generate_room(self):
		# create the solved position - populate boxes with 0
		real_rotatepic_map = ndarray((self.area.size_x, self.area.size_y), dtype=int)
		real_rotatepic_map.fill(0)
		self.rotatepic_map[ix_(self.area.x_range, self.area.y_range)] = real_rotatepic_map
		# scramble boxes
		self.scramble()

		if self.is_solved():
			self.generate_room()

	def modify_cell_types_to_draw(self, cell, cell_types):
		if self.rotatepic_map[cell] == ROTATEPIC_PUZZLE_VALUE_OUTSIDE:
			if self.is_shared_bg:
				cell_types.clear()
			return
		cell_types.append(CELL_ROTATEPIC_BOX)

	def get_cell_image_to_draw(self, cell, cell_type):
		if cell_type == CELL_ROTATEPIC_BOX:
			image = self.image if not self.is_shared_bg else self.Globals.get_bg_image()
			starting_cell = (self.area.x1, self.area.y1) if not self.is_shared_bg else (0, 0)
			rotate_angle = 0 if self.draw_solved_mode else self.rotatepic_map[cell] * 90
			return self.Globals.create_cell_subimage(image, cell, starting_cell, rotate_angle)
		return None

	def press_cell(self, cell, button=None):
		return self.rotate_cell(cell, CLOCKWISE if button in (None, 3, 5) else UPSIDEDOWN if button == 2 else COUNTERCLOCKWISE)

	def on_press_key(self, keyboard):
		if keyboard.backspace:
			self.scramble()
		self.draw_solved_mode = keyboard.kp_enter and not self.draw_solved_mode and not solution.is_active()

	def is_char_phased(self):
		return self.rotatepic_map[char.c] != ROTATEPIC_PUZZLE_VALUE_OUTSIDE

	def find_solution_func(self):
		solution_items = []
		for cell in self.area.cells:
			if self.rotatepic_map[cell] == 1:
				solution_items.append(cell)
			elif self.rotatepic_map[cell] == 2:
				solution_items.append((cell, 2))
			elif self.rotatepic_map[cell] == 3:
				solution_items.append((cell, 1))	
		shuffle(solution_items)  # optionally randomize the solution
		return solution_items, None

	def prepare_solution(self):
		return ("Finding solution", self.find_solution_func)

