from . import *

SINGLE_MINOTAUR_MOVE_DURATION = ARROW_KEYS_RESOLUTION

class MinotaurPuzzle(Puzzle):
	def init(self):
		self.minotaur = CellActor('minotaur')
		self._is_lost = False

	def has_portal(self):
		return True

	def has_finish(self):
		return True

	def is_lost(self):
		return self._is_lost

	def store_level(self, stored_level):
		stored_level["minotaur_cell"] = self.minotaur.c

	def restore_level(self, stored_level):
		self.minotaur.c = stored_level["minotaur_cell"]

	def get_minotaur_dir(self, axis_idx, minotaur_cell=None):
		return cmp(char.c[axis_idx], (minotaur_cell or self.minotaur.c)[axis_idx])

	def calculate_single_minotaur_move(self, dest_cells):
		minotaur_cell = dest_cells[-1] if dest_cells else self.minotaur.c
		
		# check horizontal then vertical move
		for axis_idx, diff in ([0, (1, 0)], [1, (0, 1)]):
			factor = cmp(char.c[axis_idx], minotaur_cell[axis_idx])
			if factor:
				dest_cell = apply_diff(minotaur_cell, diff, factor=factor)
				if self.Globals.is_cell_accessible(dest_cell):
					dest_cells.append(dest_cell)
					if char.c == dest_cell:
						self._is_lost = True
					return

	def make_single_minotaur_move(self, dest_cells):
		if not dest_cells:
			return
		dest_cell, *dest_cells = dest_cells
		self.minotaur.move_animated(target=dest_cell, on_finished=lambda: self.make_single_minotaur_move(dest_cells))

	def make_minotaur_move(self):
		# calculate single moves
		dest_cells = []
		for _ in range(2):
			self.calculate_single_minotaur_move(dest_cells)

		# animate single moves
		if not dest_cells:
			self.minotaur.move_pos((self.get_minotaur_dir(0), self.get_minotaur_dir(1)), factor=8)
			self.minotaur.animate(SINGLE_MINOTAUR_MOVE_DURATION, "bounce_end")
		else:
			self.make_single_minotaur_move(dest_cells)

	def set_finish_cell(self, goal_cell):
		if self.Globals.is_cell_accessible(self.room.cell11):
			finish_cell = self.Globals.get_closest_accessible_cell(self.room.cell11, self.room.cell22)
			self.Globals.create_portal(goal_cell, self.room.cell11)
			self.map[finish_cell] = CELL_FINISH
		else:
			self.map[goal_cell] = CELL_FINISH

	def generate_random_nonsolvable_floor_cell(self):
		# set finish in bottom-right cell, plus random 7 walls, char and minotaur
		self.set_finish_cell(self.area.cell22)
		for _ in range(7):
			self.map[self.get_random_floor_cell_in_area()] = CELL_WALL
		char_cell = self.get_random_floor_cell_in_area()
		self.Globals.set_char_cell(char_cell)
		self.minotaur.c = self.get_random_floor_cell_in_area([char_cell])

	def generate_room(self):
		self.set_area_from_config(default_size=DEFAULT_HERO_PUZZLE_SIZE, request_odd_size=True, align_to_center=True)

		self.set_area_border_walls()
		self.generate_random_nonsolvable_floor_cell()

	def on_draw(self, mode):
		self.minotaur.draw()

	def on_press_key(self, keyboard):
		if keyboard.space:
			# skip move
			self.make_minotaur_move()

	def on_enter_cell(self):
		self.make_minotaur_move()
