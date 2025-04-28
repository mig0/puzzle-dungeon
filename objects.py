from cellactor import CellActor
from drop import Drop

class Fighter(CellActor):
	def get_extra_state(self):
		return (self.power, self.health, self.attack)

	def restore_extra_state(self, state):
		self.power, self.health, self.attack = state

char = Fighter()

enemies = []
barrels = []
lifts = []

portal_destinations = {}

drop_heart = Drop('heart')
drop_sword = Drop('sword')
drop_might = Drop('might')
drop_key1  = Drop('key1')
drop_key2  = Drop('key2')

drops = (drop_heart, drop_sword, drop_might, drop_key1, drop_key2)

from cursor import Cursor

cursor = Cursor()
