from time import time
from flags import flags
from config import SOLUTION_MOVE_DELAY, SOLUTION_MOVE_DELAY_RANGE, SOLUTION_MOVE_DELAY_CHANGE
from objects import char
from constants import DIR_NAMES, DIRS_BY_NAME
from celltools import apply_diff, cell_diff
from clipboard import clipboard
from statusmessage import set_status_message

find_path    = None
move_char    = None
press_cell   = None
prepare_move = None

def is_cell(cell):
	return type(cell) == tuple and len(cell) == 2 and all(type(i) == int for i in cell)

def is_cell_list(cells):
	return type(cells) in (tuple, list) and all(is_cell(cell) for cell in cells)

def is_cell_button_tuple(pair):
	return type(pair) == tuple and len(pair) == 2 and is_cell(pair[0]) and type(pair[1]) == int

class SolutionItem:
	def __init__(self, arg):
		# TODO: slide - arg = (cell, direction)
		self.cell_to_press = arg if is_cell(arg) else None
		self.button_to_press = None
		if is_cell_button_tuple(arg):
			self.cell_to_press = arg[0]
			self.button_to_press = arg[1]
		self.shift_dir = DIRS_BY_NAME[arg] if type(arg) == str and arg in DIRS_BY_NAME else None
		self.target_cell = list(arg)[0] if type(arg) == set and is_cell(list(arg)[0]) else None
		self.path_cells = list(arg) if is_cell_list(arg) else None

		if not self.target_cell and self.path_cells is None and not self.shift_dir and not self.cell_to_press:
			raise TypeError("Unsupported arg %s in constuctor" % str(arg))

		self.is_done = True if self.path_cells is not None and not self.path_cells else False

	def get_num_moves(self):
		return len(self.path_cells) if self.path_cells is not None else 0

	def get_num_shifts(self):
		return 1 if self.shift_dir else 0

	def get_num_presses(self):
		return 1 if self.cell_to_press else 0

	def get_num_targets(self):
		return 1 if self.target_cell else 0

	def get_str(self, current_cell_ref):
		if self.shift_dir:
			current_cell_ref[0] = apply_diff(current_cell_ref[0], self.shift_dir)
			return DIR_NAMES[self.shift_dir].upper()
		if self.cell_to_press:
			return 'press%s%s' % (str(self.cell_to_press), '' if self.button_to_press is None else '^%d' % self.button_to_press)
		if self.target_cell:
			current_cell_ref[0] = self.target_cell
			return 'goto%s' % str(self.target_cell)
		if self.path_cells:
			cell_directions = []
			for cell in self.path_cells:
				cell_directions.append(DIR_NAMES.get(cell_diff(current_cell_ref[0], cell), str(cell)))
				current_cell_ref[0] = cell
			return ' '.join(cell_directions)
		return '?'

	def play_move(self):
		if self.target_cell and self.path_cells is None:
			self.path_cells = find_path(char.c, self.target_cell, allow_enemy=True)
			self.target_cell = None
			if self.path_cells is None:
				raise ValueError("Can't find path from %s to %s" % (str(char.c), str(self.target_cell)))
			self.is_done = not self.path_cells

		if self.is_done:
			print("Warning: Called play_move on SolutionItem that is done; ignoring")
			return

		if self.cell_to_press:
			press_cell(self.cell_to_press, self.button_to_press)
			self.is_done = True
		elif self.shift_dir:
			old_cell = char.c
			move_char(self.shift_dir)
			# allow repeating the same push or pull until a potentional enemy is killed
			self.is_done = char.c != old_cell
		else:
			new_cell = self.path_cells[0]
			move_char(cell_diff(char.c, new_cell))
			# allow repeating the same move until a potentional enemy is killed
			if char.c == new_cell:
				self.path_cells.pop(0)
			self.is_done = not self.path_cells

class Solution:
	def __init__(self):
		self.reset()

	def reset(self):
		self.find_mode = False
		self.stop_find = False
		self.solution_items = None
		self.play_mode = False
		self.is_status_drawn = False
		self.reset_move_delay()
		set_status_message(None, self, 1)

	def is_active(self):
		return bool(self.solution_items)

	def is_find_mode(self):
		return self.is_status_drawn and self.find_mode

	def set_find_mode(self, msg):
		self.find_mode = True
		self.solution_items = None
		self.play_mode = False
		self.is_status_drawn = False
		set_status_message(msg, self, 1)

	def set_status_drawn(self):
		self.is_status_drawn = True

	def set_find_func(self, find_func):
		if not self.find_mode:
			raise AssertionError("Called set_find_func not in find_mode")
		self.find_func = find_func

	def call_find_func(self):
		if not self.is_find_mode():
			raise AssertionError("Called call_find_func not in find_mode")
		return self.find_func()

	def get_num_info_str(self):
		num_moves = sum(item.get_num_moves() for item in self.solution_items)
		num_shifts = sum(item.get_num_shifts() for item in self.solution_items)
		num_presses = sum(item.get_num_presses() for item in self.solution_items)
		num_targets = sum(item.get_num_targets() for item in self.solution_items)
		num_moves += num_shifts  # a shift (push or pull) is considered a move too
		num_strs = []
		if num_moves:
			num_strs.append("%d moves" % num_moves)
		if num_shifts:
			num_strs.append("%d %s" % (num_shifts, "pulls" if flags.is_reverse_barrel else "pushes"))
		if num_presses:
			num_strs.append("%d presses" % num_presses)
		if num_targets:
			num_strs.append("%d targets" % num_targets)
		return ", ".join(num_strs)

	def get_str(self):
		current_cell_ref = [char.c]
		return ' '.join(item.get_str(current_cell_ref) for item in self.solution_items)

	def set(self, args):
		self.find_mode = False
		self.solution_items = [item for item in (SolutionItem(arg) for arg in args) if not item.is_done]
		self.play_mode = False
		num_left_str = self.get_num_info_str()
		set_status_message("Found solution with %s, press again to show" % num_left_str, self, 1)
		clipboard.put(self.get_str())

	def set_not_found(self):
		self.reset()
		set_status_message("Failed to find solution", self, 1, 5)

	def is_play_mode(self):
		return self.play_mode

	def set_play_mode(self):
		self.play_mode = self.is_active()
		if self.play_mode:
			self.next_solution_move_time = time() + self.move_delay
			num_left_str = self.get_num_info_str()
			set_status_message("%s left until solved" % num_left_str, self, 1)
		else:
			self.next_solution_move_time = None
			set_status_message(None, self, 1)

	def play_move(self):
		if not self.play_mode:
			return

		if time() > self.next_solution_move_time:
			prepare_move()
			self.solution_items[0].play_move()
			if self.solution_items[0].is_done:
				self.solution_items.pop(0)

			self.set_play_mode()

	def is_pull_in_progress(self):
		return self.is_play_mode() and self.solution_items[0].shift_dir and flags.is_reverse_barrel

	def set_move_delay(self, new_move_delay):
		if not SOLUTION_MOVE_DELAY_RANGE[0] <= new_move_delay <= SOLUTION_MOVE_DELAY_RANGE[1]:
			return
		if self.play_mode:
			self.next_solution_move_time += new_move_delay - self.move_delay
		self.move_delay = new_move_delay

	def dec_move_delay(self):
		self.set_move_delay(self.move_delay / SOLUTION_MOVE_DELAY_CHANGE)

	def inc_move_delay(self):
		self.set_move_delay(self.move_delay * SOLUTION_MOVE_DELAY_CHANGE)

	def reset_move_delay(self):
		self.set_move_delay(SOLUTION_MOVE_DELAY)

solution = Solution()

def set_solution_funcs(func1, func2, func3, func4):
	global find_path, move_char, press_cell, prepare_move
	find_path    = func1
	move_char    = func2
	press_cell   = func3
	prepare_move = func4
