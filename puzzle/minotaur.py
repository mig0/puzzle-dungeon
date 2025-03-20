from . import *

SINGLE_MINOTAUR_MOVE_DURATION = ARROW_KEYS_RESOLUTION

class MinotaurPuzzle(Puzzle):
	def init(self):
		self.minotaur = CellActor('minotaur')
		self.minotaur_cells = [None] * flags.NUM_ROOMS
		self.goal_cells = [None] * flags.NUM_ROOMS
		self._is_lost = False

	def has_portal(self):
		return True

	def has_finish(self):
		return True

	@property
	def minotaur_cell(self):
		return self.minotaur_cells[self.room.idx]

	@minotaur_cell.setter
	def minotaur_cell(self, cell):
		self.minotaur_cells[self.room.idx] = cell

	@property
	def goal_cell(self):
		return self.goal_cells[self.room.idx]

	@goal_cell.setter
	def goal_cell(self, cell):
		self.goal_cells[self.room.idx] = cell

	def is_lost(self):
		return self._is_lost

	def store_level(self, stored_level):
		stored_level["minotaur_cells"] = self.minotaur_cells
		stored_level["goal_cells"] = self.goal_cells

	def restore_level(self, stored_level):
		self.minotaur_cells = stored_level["minotaur_cells"]
		self.goal_cells = stored_level["goal_cells"]

	def get_minotaur_dir(self, axis_idx, minotaur_cell=None):
		return cmp(char.c[axis_idx], (minotaur_cell or self.minotaur.c)[axis_idx])

	# after 2 calls the initial dest_cells=[] become list of 0, 1 or 2 minotaur cells to move
	def calculate_single_minotaur_move(self, dest_cells, char_cell, minotaur_cell):
		if char_cell == minotaur_cell:
			return True

		if dest_cells:
			minotaur_cell = dest_cells[-1]

		# check horizontal then vertical move
		for axis_idx, diff in ([0, (1, 0)], [1, (0, 1)]):
			factor = cmp(char_cell[axis_idx], minotaur_cell[axis_idx])
			if factor:
				dest_cell = apply_diff(minotaur_cell, diff, factor=factor)
				if self.Globals.is_cell_accessible(dest_cell):
					dest_cells.append(dest_cell)
					return char_cell == dest_cell and char_cell != self.goal_cell

		return False

	def calculate_minotaur_move(self, char_cell=None, minotaur_cell=None):
		# calculate single moves
		dest_cells = []
		is_lost = False
		for _ in range(2):
			is_lost |= self.calculate_single_minotaur_move(dest_cells, char_cell or char.c, minotaur_cell or self.minotaur.c)
		return dest_cells, is_lost

	def make_single_minotaur_move(self, dest_cells):
		if not dest_cells:
			return
		dest_cell, *dest_cells = dest_cells
		self.minotaur.move_animated(target=dest_cell, on_finished=lambda: self.make_single_minotaur_move(dest_cells))

	def make_minotaur_move(self):
		dest_cells, self._is_lost = self.calculate_minotaur_move()

		# animate single moves
		if not dest_cells:
			self.minotaur.move_pos((self.get_minotaur_dir(0), self.get_minotaur_dir(1)), factor=8)
			self.minotaur.animate(SINGLE_MINOTAUR_MOVE_DURATION, "bounce_end")
		else:
			self.make_single_minotaur_move(dest_cells)

	def on_set_room(self):
		self.set_area_from_config(default_size=DEFAULT_MINOTAUR_PUZZLE_SIZE, align_to_center=True)

	def set_goal_and_finish_cell(self, goal_cell):
		self.goal_cell = goal_cell
		if self.Globals.is_cell_accessible(self.room.cell11):
			finish_cell = self.Globals.get_closest_accessible_cell(self.room.cell11, self.room.cell22)
			self.Globals.create_portal(goal_cell, self.room.cell11)
		else:
			finish_cell = goal_cell
		self.map[finish_cell] = CELL_FINISH

	def check_path_victory(self, char_cells, minotaur_cell):
		is_won = True
		for char_cell in char_cells:
			dest_cells, is_lost = self.calculate_minotaur_move(char_cell, minotaur_cell)
			if is_lost:
				is_won = False
				break
			if dest_cells:
				minotaur_cell = dest_cells[-1]
		return is_won

	def generate_random_nonsolvable_room(self):
		# set finish in bottom-right cell, plus random 7 walls, char and minotaur
		self.set_goal_and_finish_cell(self.area.cell22)
		for _ in range(7):
			self.map[self.get_random_floor_cell_in_area()] = CELL_WALL
		char_cell = self.get_random_floor_cell_in_area()
		self.Globals.set_char_cell(char_cell)
		self.minotaur_cell = self.get_random_floor_cell_in_area([char_cell])

	def generate_random_floor_path(self, start_cell, target_cell):
		return self.Globals.generate_random_free_path(start_cell, target_cell, self.area)

	def generate_random_solvable_room(self):
		num_tries = 3000

		while num_tries > 0:
			# 1) initialize entire room to WALL
			for cell in self.area.cells:
				self.map[cell] = CELL_WALL

			# 2) set goal in bottom-right cell
			self.set_goal_and_finish_cell(self.area.cell22)

			# 3) place char randomly
			char_cell = self.get_random_wall_cell_in_area()
			self.convert_to_floor(char_cell)

			# 4) create random path from char to goal and set it to floor
			self.generate_random_floor_path(char_cell, self.goal_cell)

			# 5) place minotaur randomly
			minotaur_cell = self.get_random_wall_cell_in_area()
			self.convert_to_floor(minotaur_cell)

			# 6) create random path from minotaur to goal and set it to floor
			self.generate_random_floor_path(minotaur_cell, self.goal_cell)

			# 7) create random path from minotaur to char and set it to floor
			self.generate_random_floor_path(minotaur_cell, char_cell)

			# 8) create random path from random cell to goal and set it to floor
			random_cell = self.get_random_wall_cell_in_area()
			self.generate_random_floor_path(random_cell, self.goal_cell)

			# 9) create random floors in the area
			for _ in range(self.area.size_x):
				cell = self.get_random_wall_cell_in_area()
				if not cell:
					break
				self.convert_to_floor(cell)

			# 10) find shortest path from char to goal
			path_cells = self.Globals.find_path(char_cell, self.goal_cell)
			if not path_cells:
				print("Bug in generate_random_solvable_room after find_path")
				quit()

			# 11) check whether the shortest path leads to win
			has_trivial_solution = self.check_path_victory(path_cells, minotaur_cell)

			# 12) check existence of winning path (only if the shortest path leads to defeat)
			def get_minotaur_cell(char_cell, old_char_cell, old_minotaur_cell):
				if char_cell == old_minotaur_cell:
					return None
				if old_minotaur_cell is None:
					new_minotaur_cell = minotaur_cell
				else:
					dest_cells, is_lost = self.calculate_minotaur_move(char_cell, old_minotaur_cell)
					if is_lost:
						return None
					new_minotaur_cell = dest_cells[-1] if dest_cells else old_minotaur_cell
				return new_minotaur_cell

			solution_cells = None
			if not has_trivial_solution:
				solution_cells = self.Globals.find_best_path(char_cell, self.goal_cell, allow_stay=True, state_func=get_minotaur_cell)

			if DEBUG_LEVEL:
				title = "Non-trivial solution" if solution_cells else "Only trivial solution" if has_trivial_solution else "No solution"
				self.Globals.debug_map(2, title, char_cell=char_cell, cell_chars={c: '⨯' for c in (solution_cells or [0])[:-1]} | {minotaur_cell: '⚚'})

			# found non-trivial solution
			if solution_cells:
				self.Globals.set_char_cell(char_cell)
				self.minotaur_cell = minotaur_cell
				return

			num_tries -= 1

		self.Globals.debug(0, "Can't generate minotaur level, making it random unsolvable")
		for cell in self.area.cells:
			self.convert_to_floor(cell)
		self.generate_random_nonsolvable_room()

	def generate_room(self):
		self.set_area_border_walls()
		self.generate_random_solvable_room()

	def on_enter_room(self):
		self.minotaur.c = self.minotaur_cell

	def on_draw(self, mode):
		self.minotaur.draw()

	def on_press_key(self, keyboard):
		if keyboard.space:
			# skip move
			self.make_minotaur_move()

	def on_prepare_enter_cell(self):
		self.make_minotaur_move()

		if char.c == self.goal_cell and self.map[char.c] == CELL_PORTAL:
			self.Globals.demolish_portal(self.goal_cell, self.Globals.get_random_floor_cell_type())
