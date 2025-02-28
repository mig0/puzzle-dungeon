import sys
from constants import *
from cellactor import *
from sizetools import import_size_constants

class Drop:
	def __init__(self, name):
		self.reset()
		self.name = name
		self.image_name = DEFAULT_IMAGE_PREFIX + name
		self.actor = CellActor(self.image_name)
		self.status_actor = CellActor(self.image_name, scale=0.7)
		self.disappeared_actors = []

	def set_image(self, image_name):
		self.image_name = image_name
		for actor in (self.actor, self.status_actor):
			actor.image = image_name

	def reset(self):
		self.active = False
		self.num_contained = 0
		self.num_collected = 0
		self.cells = {}

		import_size_constants()

	def has_instance(self, cell):
		return cell in self.cells

	def contain(self, actor):
		self.num_contained += 1

	def instantiate(self, actor, *args):
		if isinstance(actor, tuple):
			cell = actor
		else:
			cell = actor.c
			self.num_contained -= 1
		self.cells[cell] = args

	def collect(self, curr_cell):
		for cell in self.cells:
			if cell == curr_cell:
				self.num_collected += 1
				return self.cells.pop(cell)
		return None

	def consume(self):
		self.num_collected -= 1

	def draw_instances(self, draw_actor_hint):
		for cell in self.cells:
			if is_cell_in_actors(cell, self.disappeared_actors):
				continue
			self.actor.c = cell
			self.actor.draw()
			args = self.cells[cell]
			if len(args) == 2 and args[0] in '×÷+-':
				draw_actor_hint(self.actor, args[0] + str(args[1]), (0, -CELL_H * 0.5 - 14), DROP_FACTOR_COLORS)
		for actor in self.disappeared_actors:
			actor.draw()

	def disappear(self, cell, start_time, animate_duration):
		if animate_duration <= 0:
			return
		actor = create_actor(self.image_name, cell)
		actor.activate_inplace_animation(start_time, animate_duration, scale=[1, 0.2], tween='linear', on_finished=lambda: self.disappeared_actors.remove(actor))
		self.disappeared_actors.append(actor)

	def store(self):
		return self.cells.copy()

	def restore(self, stored):
		self.cells = stored

	@property
	def num_instances(self):
		return len(self.cells)

	@property
	def num_total(self):
		return self.num_contained + self.num_instances + self.num_collected

	def str(self):
		return "%s/%s" % (self.num_collected, self.num_total)

def draw_status_drops(screen, drops):
	active_drops = [ drop for drop in drops if drop.active ]
	n = len(active_drops)
	i = 0
	for drop in active_drops:
		pos_x = POS_CENTER_X + CELL_W * STATUS_DROP_X_SIZE * (i - (n - 1) / 2)
		drop.status_actor.pos = (pos_x + CELL_W * STATUS_DROP_X_ACTOR_OFFSET, POS_STATUS_Y)
		drop.status_actor.draw()
		screen.draw.text(drop.str(), center=(pos_x + CELL_W * STATUS_DROP_X_TEXT_OFFSET, POS_STATUS_Y), color="#FFAA00", gcolor="#AA6600", owidth=1.2, ocolor="#404030", alpha=1, fontsize=24)
		i += 1
