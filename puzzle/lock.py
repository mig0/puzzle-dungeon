from . import *

class LockPuzzle(Puzzle):
	def assert_config(self):
		return flags.is_any_maze

	def is_finish_cell_required(self):
		return True

	def has_locks(self):
		return True

	def generate_random_solvable_room(self, accessible_cells, finish_cell):
		def get_random_accessible_non_occupied_cell(accessible_cells):
			num_tries = 100
			while num_tries > 0:
				cell = accessible_cells[randint(0, len(accessible_cells) - 1)]
				if not self.Globals.is_cell_occupied(cell):
					return cell
				num_tries -= 1
			return None

		origin_map = self.map.copy()
		orig_accessible_cells = accessible_cells.copy()

		num_locks = 1 if flags.is_nine_rooms else 2 if flags.is_four_rooms else randint(self.config.get("min_locks") or 2, self.config.get("max_locks") or 4)

		num_tries = 10000
		while num_tries > 0:
			# exclude the finish
			accessible_cells.pop()
			for l in range(num_locks):
				lock_cell = get_random_accessible_non_occupied_cell(accessible_cells)
				if not lock_cell:
					# failed to find free cell for lock, try again
					break
				lock_type = CELL_LOCK1 if randint(0, 1) == 0 else CELL_LOCK2
				self.map[lock_cell] = lock_type

				accessible_cells = self.Globals.get_all_accessible_cells()
				if len(accessible_cells) < 3:
					# failed to generate, try again
					break
				# exclude the char
				accessible_cells.pop(0)
				# exclude the finish
				accessible_cells.pop()

				key_cell = get_random_accessible_non_occupied_cell(accessible_cells)
				if not key_cell:
					# failed to find free cell for key, try again
					break
				drop = drop_key1 if lock_type == CELL_LOCK1 else drop_key2
				if flags.is_enemy_key_drop:
					self.Globals.create_enemy(key_cell, drop=drop)
				else:
					drop.instantiate(key_cell)
			else:
				break

			debug(2, "Failed to generate solvable lock room, trying again")
			copyto(self.map, origin_map)
			accessible_cells = orig_accessible_cells.copy()
			if flags.is_enemy_key_drop:
				enemies.clear()
			drop_key1.reset()
			drop_key2.reset()
			num_tries -= 1
		else:
			print("Can't generate lock puzzle, sorry")
			quit()

	def generate_room(self):
		self.generate_random_solvable_room(self.accessible_cells, self.finish_cell)

