from random import randint
from constants import *
from cellactor import *
from common import *
from mirror import Mirror
from theme import *
from room import is_cell_in_room
from drop import Drop

__all__ = [
	'set_map',  # temporarily
	'char', 'enemies', 'barrels', 'carts', 'lifts', 'mirrors', 'portal_destinations',
	'drop_heart', 'drop_sword', 'drop_might', 'drop_key1', 'drop_key2', 'drops',
	'cursor', 'create_enemy', 'create_barrel',
	'create_cart', 'create_lift', 'get_lift_target', 'get_lift_target_at_neigh',
	'create_mirror', 'create_portal', 'create_portal_pair',
]

class Fighter(CellActor):
	def get_extra_state(self):
		return (self.power, self.health, self.attack)

	def restore_extra_state(self, state):
		self.power, self.health, self.attack = state

char = Fighter()

enemies = []
barrels = []
carts = []
lifts = []
mirrors = []

portal_destinations = {}

drop_heart = Drop('heart')
drop_sword = Drop('sword')
drop_might = Drop('might')
drop_key1  = Drop('key1')
drop_key2  = Drop('key2')

drops = (drop_heart, drop_sword, drop_might, drop_key1, drop_key2)

from cursor import Cursor

cursor = Cursor()

# temporary solution, will be refactored later
map = None
def set_map(_map):
	global map
	map = _map

def create_enemy(cell, health=None, attack=None, drop=None):
	enemy = Fighter()
	enemy.c = cell
	enemy.power  = health if char.power else None
	enemy.health = None if char.power else health if health is not None else randint(MIN_ENEMY_HEALTH, MAX_ENEMY_HEALTH)
	enemy.attack = None if char.power else attack if attack is not None else randint(MIN_ENEMY_ATTACK, MAX_ENEMY_ATTACK)
	enemy.drop   = None if char.power else drop   if drop   is not None else (None, drop_heart, drop_sword)[randint(0, 2)]
	if enemy.drop:
		enemy.drop.contain(enemy)
	enemies.append(enemy)

	return enemy

def create_barrel(cell):
	barrel = create_theme_actor("barrel", cell)
	barrels.append(barrel)

	return barrel

def create_cart(cell, move_type, exit_cell=None, image_name=None, surface=None):
	opacity = None
	if image_name is None:
		image_name = "lift" + move_type
		opacity = 0.5
	cart = create_actor(surface, cell) if surface else create_theme_actor(image_name, cell)
	cart.type = move_type
	if opacity is not None:
		cart.opacity = opacity
	if not surface:
		angle = 0
		if move_type in (MOVE_H, MOVE_L):
			angle = -90
		elif move_type in (MOVE_R):
			angle = 90
		elif move_type in (MOVE_D):
			angle = 180
		cart.angle = angle
	carts.append(cart)

	return cart

def create_lift(cell, move_type, surface=None):
	image_name = "lift" + move_type
	lift = create_actor(surface, cell) if surface else create_theme_actor(image_name, cell)
	lift.type = move_type
	lifts.append(lift)

	return lift

def get_lift_target(cell, diff):
	lift = get_actor_on_cell(cell, lifts)
	if not lift or diff not in MOVE_TYPE_DIRS[lift.type]:
		return None
	while True:
		next_cell = apply_diff(cell, diff)
		if not is_cell_in_room(next_cell) or map[next_cell] != CELL_VOID or is_cell_in_actors(next_cell, lifts):
			return cell if cell != lift.c else None
		cell = next_cell

def get_lift_target_at_neigh(lift, neigh):
	return get_lift_target(lift.c, cell_diff(lift.c, neigh))

def create_mirror(host, data=None):
	mirror = Mirror(get_theme_image_name('mirror'), host)
	if data:
		mirror.from_data(data)
	host.mirror = mirror
	mirrors.append(mirror)

	return mirror

def create_portal(cell, dst_cell):
	if cell == dst_cell:
		die("BUG: Portal destination can't be the same cell %s, exiting" % str(cell))

	map[cell] = CELL_PORTAL
	portal_destinations[cell] = dst_cell

def create_portal_pair(cell1, cell2):
	create_portal(cell1, cell2)
	create_portal(cell2, cell1)
