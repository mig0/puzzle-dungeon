from objects import char, lifts
from cellactor import CellActor, apply_diff, get_actor_on_cell

class Cursor(CellActor):
	def __init__(self, image=None):
		super().__init__(image)
		self.reset()

	def reset(self):
		self.hidden = True
		self.selected_actor = char

	def is_active(self):
		return not self.hidden

	def is_char_selected(self):
		return self.selected_actor == char

	def is_lift_selected(self):
		return not self.is_active() and not self.is_char_selected()

	def toggle(self):
		if not self.is_active():
			self.c = self.selected_actor.c
			self.hidden = False
			self.selected_actor = self
			return

		self.hidden = True
		if self.c != char.c and (lift := get_actor_on_cell(self.c, lifts)):
			self.selected_actor = lift
		else:
			self.selected_actor = char

