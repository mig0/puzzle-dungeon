from . import *
from pygame.rect import Rect

CELL_BEAM_OBSTACLES  = (*CELL_WALL_TYPES, CELL_GATE0, CELL_LOCK1, CELL_LOCK2)

CELL_BEAM_H1 = '~h1'
CELL_BEAM_H2 = '~h2'
CELL_BEAM_V1 = '~v1'
CELL_BEAM_V2 = '~v2'

BEAM_MASK_H1 = 1 << 0
BEAM_MASK_H2 = 1 << 1
BEAM_MASK_V1 = 1 << 2
BEAM_MASK_V2 = 1 << 3

BEAM_CELL_TYPE_MASKS = {
	CELL_BEAM_H1: BEAM_MASK_H1,
	CELL_BEAM_H2: BEAM_MASK_H2,
	CELL_BEAM_V1: BEAM_MASK_V1,
	CELL_BEAM_V2: BEAM_MASK_V2,
}

DIR_BEAM_MASKS = {
	(DIR_L, 0): BEAM_MASK_H1,
	(DIR_L, 1): BEAM_MASK_H2,
	(DIR_R, 0): BEAM_MASK_H2,
	(DIR_R, 1): BEAM_MASK_H1,
	(DIR_U, 0): BEAM_MASK_V1,
	(DIR_U, 1): BEAM_MASK_V2,
	(DIR_D, 0): BEAM_MASK_V2,
	(DIR_D, 1): BEAM_MASK_V1,
}

DIR_TRANSFORMATIONS = {
	(DIR_L, 0): DIR_R,
	(DIR_L, 1): DIR_D,
	(DIR_L, 2): DIR_L,
	(DIR_L, 3): DIR_U,
	(DIR_R, 0): DIR_L,
	(DIR_R, 1): DIR_U,
	(DIR_R, 2): DIR_R,
	(DIR_R, 3): DIR_D,
	(DIR_U, 0): DIR_U,
	(DIR_U, 1): DIR_R,
	(DIR_U, 2): DIR_D,
	(DIR_U, 3): DIR_L,
	(DIR_D, 0): DIR_D,
	(DIR_D, 1): DIR_L,
	(DIR_D, 2): DIR_U,
	(DIR_D, 3): DIR_R,
}

DIR_USAGE = {
	DIR_L: 1 << 0,
	DIR_R: 1 << 1,
	DIR_U: 1 << 2,
	DIR_D: 1 << 3,
}

class HintFlags:
	can_move     = False
	can_rotate   = False
	can_activate = False
	all_active   = True
	has_gates    = False
	has_locks    = False
	has_portals  = False

def build_hint(hint):
	mirror_verbs = []
	if hint.can_move:
		mirror_verbs.append("{move-word}")
	if hint.can_rotate:
		mirror_verbs.append("{rotate-word}")
	if hint.can_activate:
		mirror_verbs.append("{deactivate-word}" if hint.all_active else "{activate-word}")

	parts = []

	if mirror_verbs:
		parts.append(concatenate_items(mirror_verbs) + " {mirrors-word}")

	if hint.has_gates:
		parts.append("{toggle-gates}")
	if hint.has_locks:
		parts.append("{open-locks}")
	if hint.has_portals:
		parts.append("{use-portals}")

	if not parts:
		parts = ["{think-word}"]

	return concatenate_items(parts) + " {to-solve}"

class MirrorPuzzle(Puzzle):
	def init(self):
		self.load_map_special_cell_types[CELL_PLATE] = 'ints'
		self.update_beam = False
		self.won = False

	def load_beam_images(self):
		beam_image = load_theme_cell_image('beam')
		beam_v1 = create_cell_subimage(beam_image, cell=(0,    0), area=(Rect(0,           0, CELL_W, CELL_H // 2)), rotate_angle=0)
		beam_v2 = create_cell_subimage(beam_image, cell=(0, -0.5), area=(Rect(0, CELL_H // 2, CELL_W, CELL_H // 2)), rotate_angle=0)
		beam_h1 = create_cell_subimage(beam_image, cell=(0,    0), area=(Rect(0,           0, CELL_W, CELL_H // 2)), rotate_angle=90)
		beam_h2 = create_cell_subimage(beam_image, cell=(0, -0.5), area=(Rect(0, CELL_H // 2, CELL_W, CELL_H // 2)), rotate_angle=90)
		self.beam_images = {
			BEAM_MASK_H1: beam_h1,
			BEAM_MASK_H2: beam_h2,
			BEAM_MASK_V1: beam_v1,
			BEAM_MASK_V2: beam_v2,
		}
		self.beamgn = create_theme_image('beamgn')
		self.beamcl = create_theme_image('beamcl')

	def assert_config(self):
		return not flags.is_any_maze

	def has_start(self):
		return self.get_room_cells(CELL_START)

	def has_finish(self):
		return self.get_room_cells(CELL_FINISH)

	def has_plate(self):
		return True

	def has_portal(self):
		return True

	def has_gate(self):
		return True

	def has_locks(self):
		return True

	def has_sand(self):
		return True

	def has_odirs(self):
		return True

	def has_glass(self):
		return True

	def has_trap(self):
		return True

	def has_beam(self):
		return True

	def is_goal_to_be_solved(self):
		return True

	def is_solved(self):
		return self.won

	def store_level(self, stored_level):
		stored_level["beamgn_cell"] = self.beamgn_cell
		stored_level["beamcl_cell"] = self.beamcl_cell

	def restore_level(self, stored_level):
		self.set_beam_cells(stored_level["beamgn_cell"], stored_level["beamcl_cell"])
		self.bind_mirrors()

	def on_set_theme():
		self.load_beam_images()

	def get_cell_beam_mask(self, cell):
		return self.cell_beam_masks.get(cell, 0)

	def set_cell_beam_mask(self, cell, dir, incoming=0):
		self.cell_beam_masks[cell] = self.get_cell_beam_mask(cell) | DIR_BEAM_MASKS[(dir, incoming)]

	def create_beam(self):
		self.cell_beam_masks = dict()
		for dir in DIRS:
			visited_used_active_flips = {}
			visited_mirror_cells = {}
			cell = self.beamgn_cell
			i = 0
			while True:
				# apply outgoing half and advance beam
				self.set_cell_beam_mask(cell, dir, 0)
				cell = apply_diff(cell, dir)
				if not self.is_in_room(cell) or self.map[cell] in CELL_BEAM_OBSTACLES:
					break

				# apply incoming half and check for win
				self.set_cell_beam_mask(cell, dir, 1)
				if cell == self.beamgn_cell:
					break
				if cell == self.beamcl_cell:
					self.won = True
					break

				# process mirror or portal
				mirror = get_actor_on_cell(cell, mirrors)
				if mirror:
					if mirror.is_active_flip():
						visited_used_active_flips[cell] = cell in visited_used_active_flips
					visited_key = (dir, dir)
					if mirror.is_active(cell in visited_mirror_cells):
						dir = DIR_TRANSFORMATIONS[(dir, mirror.orientation)]
						visited_key = (visited_key[0], dir)
					if not cell in visited_mirror_cells:
						visited_mirror_cells[cell] = []
					if visited_key in visited_mirror_cells[cell] and all(used for cell, used in visited_used_active_flips.items()):
						break
					visited_mirror_cells[cell].append(visited_key)
				if cell in portal_destinations:
					cell = portal_destinations[cell]
				i += 1
				if i > 10000:
					self.Globals.debug_map(0, "Deadlock")
					return
		self.update_beam = False

	def set_beam_cells(self, beamgn_cell, beamcl_cell):
		self.beamgn_cell = beamgn_cell
		self.beamcl_cell = beamcl_cell

	def bind_mirrors(self):
		is_void_bg = self.Globals.get_bg_image() is not None
		for mirror in mirrors:
			mirror.watch("cell_changed", self)
			if not mirror.host in lifts:
				is_void_bg = False
		self.is_void_bg = is_void_bg
		for lift in lifts:
			if lift.mirror:
				lift.hidden = True

	def on_set_theme(self):
		self.load_beam_images()

	def on_actor_cell_changed(self, actor):
		clock.schedule(self.create_beam, ARROW_KEYS_RESOLUTION * (0.1 if game.during_undo else 0.8))

	def get_room_hint(self):
		hint = HintFlags()
		for mirror in mirrors:
			if mirror.host in barrels or mirror.host in (carts + lifts) and mirror.host.type != MOVE_N:
				hint.can_move = True
			if not mirror.fixed_orientation:
				hint.can_rotate = True
			if not mirror.fixed_activeness:
				hint.can_activate = True
			if not mirror.is_active():
				hint.all_active = False

		if self.get_room_cells(CELL_GATE0, CELL_GATE1):
			hint.has_gates = True
		if self.get_room_cells(CELL_LOCK1, CELL_LOCK2):
			hint.has_locks = True
		if self.get_room_cells(CELL_PORTAL):
			hint.has_portals = True
		return hint

	def on_enter_room(self):
		self.create_beam()

		hint = self.get_room_hint()
		set_status_message(t(build_hint(hint)).capitalize(), self, 2, 15)

	def on_load_map(self, special_cell_values, extra_values):
		beam_cells = self.get_map_cells(CELL_BEAMGN, CELL_BEAMCL)
		if len(beam_cells) != 2 or self.map[beam_cells[0]] == beam_cells[1]:
			self.die("Invalid map. Must contain exactly one beam generator and collector")
		if self.map[beam_cells[0]] == CELL_BEAMCL:
			beam_cells.reverse()
		self.set_beam_cells(*beam_cells)

		gate_cells = self.get_map_cells(CELL_GATE0, CELL_GATE1, CELL_TRAP0, CELL_TRAP1)
		self.attached_plate_gate_cells = {}

		for cell, data in special_cell_values.items():
			if self.map[cell] == CELL_PLATE:
				self.attached_plate_gate_cells[cell] = tuple(gate_cells[idx] for idx in data)
		self.bind_mirrors()

	def press_cell(self, cell, button=None):
		mirror = get_actor_on_cell(cell, mirrors)

		if cell == char.c and self.map[cell] == CELL_PLATE:
			for gate_cell in self.attached_plate_gate_cells[cell]:
				self.Globals.toggle_gate(gate_cell)
		elif not mirror:
			return False

		if mirror:
			if button in (2, 4, 5):
				if mirror.fixed_orientation:
					return False
				mirror.rotate_mirror(-1 if button == 4 else +1)
			elif button in (None, 1, 3):
				if mirror.fixed_activeness:
					return False
				if button == 3:
					mirror.toggle_active_flip()
				else:
					mirror.toggle_active()
			elif button == 6:
				mirror.reset()
			else:
				return False

		self.create_beam()
		return True

	def on_press_key(self, keyboard):
		if keyboard.shift and keyboard.delete:
			for mirror in mirrors:
				mirror.reset()
			self.create_beam()

	def modify_cell_types_to_draw(self, cell, cell_types):
		if self.is_void_bg and cell in (self.beamgn_cell, self.beamcl_cell):
			cell_types.remove(CELL_FLOOR)
		if BEAM_DRAW_MODE != 0:
			return
		beam_mask = self.get_cell_beam_mask(cell)
		if not beam_mask:
			return
		beam_cell_types = []
		if beam_mask & BEAM_MASK_H1:
			beam_cell_types.append(CELL_BEAM_H1)
		if beam_mask & BEAM_MASK_H2:
			beam_cell_types.append(CELL_BEAM_H2)
		if beam_mask & BEAM_MASK_V1:
			beam_cell_types.append(CELL_BEAM_V1)
		if beam_mask & BEAM_MASK_V2:
			beam_cell_types.append(CELL_BEAM_V2)
		idx = (1 if cell_types[0] == CELL_FLOOR else 0) if cell in (self.beamgn_cell, self.beamcl_cell) else len(cell_types)
		for cell_type in beam_cell_types:
			cell_types.insert(idx, cell_type)

	def get_cell_image_to_draw(self, cell, cell_type):
		if BEAM_DRAW_MODE != 0:
			return None
		if cell_type in BEAM_CELL_TYPE_MASKS:
			return self.beam_images[BEAM_CELL_TYPE_MASKS[cell_type]]
		return None

	def on_draw(self):
		if BEAM_DRAW_MODE == 0:
			return
		for cell in room.cells:
			beam_mask = self.get_cell_beam_mask(cell)
			for mask in (BEAM_MASK_H1, BEAM_MASK_H2, BEAM_MASK_V1, BEAM_MASK_V2):
				if beam_mask & mask:
					game.screen.blit(self.beam_images[mask], cell_to_pos_00(cell))
		if BEAM_DRAW_MODE == 1:
			for mirror in mirrors:
				mirror.draw()
		self.beamgn.draw(self.beamgn_cell)
		self.beamcl.draw(self.beamcl_cell)
		char.draw()

	def on_prepare_enter_cell(self):
		if self.map[char.c] in (CELL_LOCK1, CELL_LOCK2):
			self.update_beam = True

	def on_enter_cell(self):
		if self.update_beam:
			self.create_beam()

	def on_undo_move(self):
		self.create_beam()
