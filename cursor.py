from objects import char, lifts
from cellactor import CellActor, get_actor_on_cell
from celltools import apply_diff

class Cursor(CellActor):
	def init(self):
		self.selected_actor = self
		self.reset()

	def activate(self):
		self.c = self.selected_actor.c
		self.hidden = False
		self.selected_actor.selected = False
		self.selected_actor = self

	def set_actor(self, actor, selected):
		self.hidden = True
		self.selected_actor.selected = False
		self.selected_actor = actor
		self.selected_actor.selected = selected

	def reset(self):
		self.set_actor(char, False)

	def is_active(self):
		return not self.hidden

	def is_char_selected(self):
		return self.selected_actor == char

	def is_lift_selected(self):
		return not self.is_active() and not self.is_char_selected()

	def toggle(self):
		if not self.is_active():
			self.activate()
			return

		if self.c != char.c and (lift := get_actor_on_cell(self.c, lifts)):
			self.set_actor(lift, True)
		else:
			self.reset()

