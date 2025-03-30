from time import time
from config import SOLUTION_MOVE_DELAY
from objects import char
from cellactor import cell_diff
from statusmessage import set_status_message

find_path    = None
move_char    = None
press_cell   = None

def is_cell(cell):
	return type(cell) == tuple and len(cell) == 2 and \
		all(type(i) == int and type(i) == int for i in cell)

def is_cell_list(cells):
	return type(cells) in (tuple, list) and all(is_cell(cell) for cell in cells)

class SolutionItem:
	def __init__(self, arg):
		self.cell_to_press = arg if is_cell(arg) else None
		self.target_cell = list(arg)[0] if type(arg) == set and is_cell(list(arg)[0]) else None
		self.path_cells = list(arg) if is_cell_list(arg) else None

		if not self.target_cell and self.path_cells is None and not self.cell_to_press:
			raise TypeError("Unsupported arg %s in constuctor" % str(arg))

		self.is_done = True if self.path_cells is not None and not self.path_cells else False

	def get_num_moves(self):
		return len(self.path_cells) if self.path_cells is not None else 0

	def get_num_presses(self):
		return 1 if self.cell_to_press else 0

	def get_num_targets(self):
		return 1 if self.target_cell else 0

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
			press_cell(self.cell_to_press)
			self.is_done = True
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
		self.solution_items = None
		self.play_mode = False
		self.is_status_drawn = False
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

	def get_num_moves_presses_str(self):
		num_moves = sum(item.get_num_moves() for item in self.solution_items)
		num_presses = sum(item.get_num_presses() for item in self.solution_items)
		num_targets = sum(item.get_num_targets() for item in self.solution_items)
		num_strs = []
		if num_moves:
			num_strs.append("%d moves" % num_moves)
		if num_presses:
			num_strs.append("%d presses" % num_presses)
		if num_targets:
			num_strs.append("%d targets" % num_targets)
		return ", ".join(num_strs)

	def set(self, args):
		self.find_mode = False
		self.solution_items = [SolutionItem(arg) for arg in args]
		self.play_mode = False
		num_left_str = self.get_num_moves_presses_str()
		set_status_message("Found solution with %s, press again to show" % num_left_str, self, 1)

	def set_not_found(self):
		self.reset()
		set_status_message("Failed to find solution", self, 1, 5)

	def is_play_mode(self):
		return self.play_mode

	def set_play_mode(self):
		self.play_mode = self.is_active()
		if self.play_mode:
			self.next_solution_move_time = time() + SOLUTION_MOVE_DELAY
			num_left_str = self.get_num_moves_presses_str()
			set_status_message("%s left until solved" % num_left_str, self, 1)
		else:
			self.next_solution_move_time = None
			set_status_message(None, self, 1)

	def play_move(self):
		if not self.play_mode:
			return

		if time() > self.next_solution_move_time:
			self.solution_items[0].play_move()
			if self.solution_items[0].is_done:
				self.solution_items.pop(0)

			self.set_play_mode()

solution = Solution()

def set_solution_funcs(func1, func2, func3):
	global find_path, move_char, press_cell
	find_path    = func1
	move_char    = func2
	press_cell   = func3
