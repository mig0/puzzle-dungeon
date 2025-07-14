from . import *

FIFTEEN_PUZZLE_VALUE_OUTSIDE = -1
CELL_FIFTEEN_FRAME = '~f'
CELL_FIFTEEN_VALUE = '~v'

class FifteenPuzzle(Puzzle):
	def init(self):
		self.fifteen_map = None
		self.frame_image = None
		self.max_num = 0
		self.draw_solved_mode = False

	def assert_config(self):
		return not flags.is_any_maze

	def on_set_theme(self):
		self.frame_image = load_theme_cell_image('floor_gray_frame')

	def on_create_map(self):
		self.fifteen_map = ndarray((MAP_SIZE_X, MAP_SIZE_X), dtype=int)
		self.fifteen_map.fill(FIFTEEN_PUZZLE_VALUE_OUTSIDE)

	def is_goal_to_be_solved(self):
		return True

	def get_num_solved(self, cell):
		return (cell[1] - self.area.y1) * self.area.size_x + (cell[0] - self.area.x1) + 1

	def is_solved(self):
		for cell in self.area.cells:
			if self.fifteen_map[cell] != self.get_num_solved(cell):
				return False
		return True

	def store_level(self, stored_level):
		stored_level["fifteen_map"] = self.fifteen_map.copy()

	def restore_level(self, stored_level):
		self.fifteen_map = stored_level["fifteen_map"]

	def on_set_room(self):
		self.set_area_from_config(align_to_center=True)
		self.max_num = self.area.size_x * self.area.size_y

	def is_empty_cell(self, cell):
		return self.fifteen_map[cell] == self.max_num

	def get_empty_cell(self):
		return list(tuple(cell) for cell in argwhere(self.fifteen_map == self.max_num) if self.is_in_area(cell))[0]

	def get_cells_on_one_line_between_two_cells(self, cell1, cell2):
		cells = []
		if cell1 == cell2 or cell1[0] != cell2[0] and cell1[1] != cell2[1]:
			return cells

		dir = cell_dir(cell1, cell2)
		cell = cell1
		while cell != cell2:
			cell = apply_diff(cell, dir)
			cells.append(cell)
		return cells

	def swap(self, cell1, cell2):
		self.fifteen_map[cell1], self.fifteen_map[cell2] = self.fifteen_map[cell2], self.fifteen_map[cell1]

	def move(self, cell, empty_cell, neigh_only=False):
		is_moved = False
		if neigh_only:
			neighbors = self.Globals.get_actor_neighbors(char, self.area.x_range, self.area.y_range)
			if empty_cell not in neighbors:
				return False
			self.swap(cell, empty_cell)
			is_moved = True
		else:
			last_cell = empty_cell
			for cell in self.get_cells_on_one_line_between_two_cells(empty_cell, cell):
				self.swap(last_cell, cell)
				is_moved = True
				last_cell = cell

		return is_moved

	def get_random_non_equal(self, range, n):
		r = n
		while r == n:
			r = randint(range.start, range.stop - 1)
		return r

	def scramble(self):
		# scramble by real moves
		num_moves_left = self.max_num * 12
		empty_cell = self.get_empty_cell()
		is_row = True
		while num_moves_left > 0:
			is_row = not is_row
			if is_row:
				cell = (empty_cell[0], self.get_random_non_equal(self.area.y_range, empty_cell[1]))
			else:
				cell = (self.get_random_non_equal(self.area.x_range, empty_cell[0]), empty_cell[1])
			self.move(cell, empty_cell)
			empty_cell = cell
			num_moves_left -= 1

	def generate_room(self):
		# create the solved position - populate numbers from 1 to max_num
		real_fifteen_map = arange(self.max_num).reshape(self.area.size_y, self.area.size_x)
		real_fifteen_map += 1
		self.fifteen_map[ix_(self.area.x_range, self.area.y_range)] = real_fifteen_map.transpose()
		# scramble fifteen map
		self.scramble()

		if self.is_solved():
			self.generate_room()

	def modify_cell_types_to_draw(self, cell, cell_types):
		if self.fifteen_map[cell] == FIFTEEN_PUZZLE_VALUE_OUTSIDE:
			return
		cell_types.append(CELL_FIFTEEN_FRAME)
		if self.is_empty_cell(cell) and (not self.draw_solved_mode or not self.is_in_area(cell)) or cell == (self.area.x2, self.area.y2) and self.draw_solved_mode:
			return
		cell_types.append(CELL_FIFTEEN_VALUE)

	def get_cell_image_to_draw(self, cell, cell_type):
		if cell_type == CELL_FIFTEEN_FRAME:
			return self.frame_image
		if cell_type == CELL_FIFTEEN_VALUE:
			num = self.fifteen_map[cell] if not self.draw_solved_mode or not self.is_in_area(cell) else self.get_num_solved(cell)
			return create_text_cell_image(str(num), color='#FFFFC0', gcolor="#808040", owidth=1, ocolor="#404030")
		return None

	def press_cell(self, cell, button=None):
		if self.fifteen_map[cell] == FIFTEEN_PUZZLE_VALUE_OUTSIDE:
			return False
		if button not in (None, 1):
			return True

		empty_cell = self.get_empty_cell()
		self.move(cell, empty_cell, FIFTEEN_PUZZLE_MOVE_NEIGHBOUR_ONLY)
		return True

	def on_press_key(self, keyboard):
		self.draw_solved_mode = keyboard.kp_enter and not self.draw_solved_mode

	def is_char_phased(self):
		return self.fifteen_map[char.c] != FIFTEEN_PUZZLE_VALUE_OUTSIDE

