from common import die
from constants import DIR_NAMES
from sizetools import CELL_W, CELL_H

def cmp(n1, n2):
	return 1 if n1 > n2 else 0 if n1 == n2 else -1

def product(x_range, y_range, run_by_y=False):
	if run_by_y:
		for x in x_range:
			for y in y_range:
				yield (x, y)
	else:
		for y in y_range:
			for x in x_range:
				yield (x, y)

def apply_diff(orig, diff, subtract=False, factor=1):
	if subtract:
		factor = -factor
	return (orig[0] + diff[0] * factor, orig[1] + diff[1] * factor)

def cell_diff(cell1, cell2, reverse=False, assert_adjacent=False):
	diff = (cell2[0] - cell1[0], cell2[1] - cell1[1])
	if reverse:
		diff = (-diff[0], -diff[1])
	if assert_adjacent and diff not in DIR_NAMES:
		die("Cells %s and %s are not adjacent", True)
	return diff

def cell_dir(cell1, cell2):
	return (cmp(cell2[0], cell1[0]), cmp(cell2[1], cell1[1]))

def cell_to_pos_offset(cell, offset):
	return (CELL_W * (cell[0] + offset[0]), CELL_H * (cell[1] + offset[1]))

def cell_to_pos_00(cell):
	return cell_to_pos_offset(cell, (0, 0))

def cell_to_pos(cell):
	return cell_to_pos_offset(cell, (0.5, 0.5))

def pos_to_cell(pos):
	return (pos[0] // CELL_W, pos[1] // CELL_H)

def cell_distance(cell1, cell2):
	return abs(cell2[0] - cell1[0]) + abs(cell2[1] - cell1[1])

def sort_cells(cells):
	return sorted(cells, key=lambda cell: (cell[1], cell[0]))

class Area:
	x1 = None
	y1 = None
	x2 = None
	y2 = None
	size_x = None
	size_y = None
	x_range = None
	y_range = None

	@property
	def num_cells(self):
		return len(self.x_range) * len(self.y_range)

	@property
	def cells(self):
		return product(self.x_range, self.y_range)

	@property
	def cell11(self):
		return (self.x1, self.y1)

	@property
	def cell12(self):
		return (self.x1, self.y2)

	@property
	def cell21(self):
		return (self.x2, self.y1)

	@property
	def cell22(self):
		return (self.x2, self.y2)

	def is_cell_evnevn(self, cell):
		return (cell[0] - self.x1) % 2 == 0 and (cell[1] - self.y1) % 2 == 0

	def is_cell_evnodd(self, cell):
		return (cell[0] - self.x1) % 2 == 0 and (cell[1] - self.y1) % 2 == 1

	def is_cell_oddevn(self, cell):
		return (cell[0] - self.x1) % 2 == 1 and (cell[1] - self.y1) % 2 == 0

	def is_cell_oddodd(self, cell):
		return (cell[0] - self.x1) % 2 == 1 and (cell[1] - self.y1) % 2 == 1

	def is_cell_inside(self, cell, margin=0):
		return self.x1 + margin <= cell[0] <= self.x2 - margin and self.y1 + margin <= cell[1] <= self.y2 - margin

	def is_cell_on_margin(self, cell, margin=0):
		if margin > 0:
			return self.is_cell_inside(cell) and not self.is_cell_inside(cell, margin)
		if margin < 0:
			return not self.is_cell_inside(cell) and self.is_cell_inside(cell, margin)
		return False

