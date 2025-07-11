from . import *

class HeroPuzzle(Puzzle):
	def init(self):
		self.is_strict_floors = bool(self.config.get("strict_floors"))

	def assert_config(self):
		return bool(char.power)

	def has_finish(self):
		return True

	def has_portal(self):
		return self.is_strict_floors

	def has_gate(self):
		return True

	def has_odirs(self):
		return self.is_strict_floors

	def is_goal_to_kill_enemies(self):
		return self.is_strict_floors

	def is_goal_to_be_solved(self):
		return not self.is_goal_to_kill_enemies()

	def is_solved(self):
		return self.get_num_keys_in_room() == 0

	def get_num_keys_in_room(self):
		num_keys = 0
		for drop_key in (drop_key1, drop_key2):
			for cell in drop_key.cells:
				if self.is_in_room(cell):
					num_keys += 1
		return num_keys

	def generate_random_nonsolvable_floor_cell(self, cell):
		slot_type = randint(0, 2)
		if slot_type == 0:
			create_enemy(cell, randint(10, 50))
		elif slot_type == 1:
			op = choice('×÷+-')
			factor = (2, 3)[randint(0, 1)] if op in ('×', '÷') else (50, 100)[randint(0, 1)]
			drop_might.instantiate(cell, op, factor)

	def generate_room(self):
		self.set_area_from_config(default_size=DEFAULT_HERO_PUZZLE_SIZE, request_odd_size=True, align_to_center=True)

		num_floors = (self.area.size_y + 1) / 2
		num_slots = self.area.size_x - 1

		self.set_area_border_walls()
		if self.area.x1 > room.x1:
			self.map[self.area.x1 - 1, (self.area.y1 + self.area.y2) // 2] = CELL_GATE1

		for cell in self.area.cells:
			if (cell[1] - self.area.y1) % 2 == 1:
				if cell[0] != self.area.x1:
					self.map[cell] = CELL_WALL
			elif cell[0] == self.area.x1:
				if self.is_strict_floors:
					self.map[cell] = CELL_ODIRR
			elif cell[0] == self.area.x2:
				if self.is_strict_floors:
					create_portal(cell, (self.area.x1, cell[1]))
				else:
					choice((drop_key1, drop_key2)).instantiate(cell)
			else:
				self.generate_random_nonsolvable_floor_cell(cell)

		self.map[room.x1, room.y2] = CELL_FINISH
