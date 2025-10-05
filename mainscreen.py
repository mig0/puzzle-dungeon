from puzzle import *
from numpy import array, all
from level import Level, Collection

class MainScreen(VirtualPuzzle):
	def init(self):
		self.main_screen_color = array((80, 80, 80))

	def is_goal_to_kill_enemies(self):
		return False

	def is_central_flash_needed(self):
		return True

	def has_plate(self):
		return True

	def advance_main_screen_color(self):
		while True:
			step = array(choice(((1, 1, -2), (1, -2, 1), (-2, 1, 1), (-1, -1, 2), (-1, 2, -1), (2, -1, -1)))) * randint(1, 2)
			self.main_screen_color += step
			if all(self.main_screen_color < 256) and all(self.main_screen_color >= 0):
				break
			self.main_screen_color -= step

	def press_cell(self, cell, button=None):
		if not cell in self.plate_collections:
			return False
		game.set_requested_new_level(self.plate_collections[cell].get_level_id())
		return False

	def on_press_key(self, keyboard):
		if not (False
			or keyboard.right or keyboard.left or keyboard.up or keyboard.down
			or keyboard.escape or keyboard.space or keyboard.enter
		):
			game.set_requested_new_level(game.collections[0].get_level_id())

	def on_draw_map(self):
		for cell in self.plate_cells:
			cell_with_offset = apply_diff(cell, (0.2, -0.2))
			self.plate_icons[cell].draw(cell_with_offset)

	def on_draw(self):
		self.advance_main_screen_color()
		draw_central_flash(True, tuple(self.main_screen_color))

	def on_enter_room(self):
		self.on_enter_cell()

	def on_enter_cell(self):
		if self.map[char.c] == CELL_PLATE:
			set_status_message("Press Space to play %s" % self.plate_collections[char.c].name)
		else:
			set_status_message("Press Tab to play levels in order")

	def on_generate_map(self):
		char_cell = next(cell for cell in room.cells if self.Globals.is_cell_accessible(cell, place=True))
		accessible_cell_distances = self.Globals.get_accessible_cell_distances(char_cell, allow_enemy=True)
		del accessible_cell_distances[char_cell]  # remove char cell
		accessible_cells = list(accessible_cell_distances.keys())
		self.plate_cells = sample(accessible_cells, k=len(game.collections))
		self.plate_cells.sort(key=lambda cell: accessible_cell_distances[cell])
		self.plate_collections = dict(zip(self.plate_cells, game.collections))

		self.plate_icons = {}
		for cell in self.plate_cells:
			self.map[cell] = CELL_PLATE
			plate_icon = CellActor(load_image('images/' + self.plate_collections[cell].icon, (CELL_W * 0.4, CELL_H * 0.4)))
			self.plate_icons[cell] = plate_icon

main_screen_level = Level()
main_screen_level.set_from_config(Collection("mainscreen", {}), 1, {
	"num-enemies": 3,
	"theme": "ancient2",
	"music": "valiant_warriors",
	"char-health": 100,
	"use-clock": True,
	"goal": 'select-level',
	"random-maze": True,
	"puzzle-type": "MainScreen",
})
