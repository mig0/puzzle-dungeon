from . import *

CELL_ROTATEPIC_HINT = '~h'

SKIPPED_PORTAL_IDXS_PER_NUM = (
	[0, 1, 2],
	[0, 3],
	[0],
	[],
)

def get_hall_portal_cell(hall_idx, portal_idx):
	return (
		(ROOM_9_X1[hall_idx], ROOM_9_Y1[hall_idx]),
		(ROOM_9_X2[hall_idx], ROOM_9_Y1[hall_idx]),
		(ROOM_9_X1[hall_idx], ROOM_9_Y2[hall_idx]),
		(ROOM_9_X2[hall_idx], ROOM_9_Y2[hall_idx]),
	)[portal_idx]

def get_hall_center_cell(hall_idx):
	return ((ROOM_9_X1[hall_idx] + ROOM_9_X2[hall_idx]) // 2, (ROOM_9_Y1[hall_idx] + ROOM_9_Y2[hall_idx]) // 2)

class PortalPuzzle(Puzzle):
	def init(self):
		self.portal_cell_to_hall_idx = {}
		self.hall_center_cell_to_idx = {}
		self.dst_hall_idx_to_src_hall_idxs = {i: [] for i in range(0, 9)}
		self.draw_hint_mode = False
		self.num_portals_per_hall = self.config.get("num_portals_per_hall", 4)

	def assert_config(self):
		return not flags.is_any_maze and not flags.MULTI_ROOMS

	def has_finish(self):
		return True

	def has_portal(self):
		return True

	def store_level(self, stored_level):
		stored_level["portal_cell_to_hall_idx"] = self.portal_cell_to_hall_idx

	def restore_level(self, stored_level):
		self.portal_cell_to_hall_idx = stored_level["portal_cell_to_hall_idx"]

	def is_fully_reachable_and_solvable(self):
		# disallow the trivial solution
		if 0 in self.dst_hall_idx_to_src_hall_idxs[4]:
			return False

		# check reachability of all halls
		for dst_hall_id in range(0, 9):
			if len(self.dst_hall_idx_to_src_hall_idxs[dst_hall_id]) == 0:
				return False

		# check existence of a path from the initial hall_idx=0 to the final hall_idx=4
		visited_hall_ids = {}
		unprocessed_hall_ids = [4]
		while unprocessed_hall_ids:
			dst_hall_id = unprocessed_hall_ids.pop(0)
			visited_hall_ids[dst_hall_id] = True
			for src_hall_idx in self.dst_hall_idx_to_src_hall_idxs[dst_hall_id]:
				if src_hall_idx == 0:
					return True
				if src_hall_idx not in visited_hall_ids:
					unprocessed_hall_ids.append(src_hall_idx)

		return False

	def create_portal(self, portal_cell, hall_idx, dst_hall_id):
		debug(3, "  create_portal %s %d -> %d" % (str(portal_cell), hall_idx, dst_hall_id))
		create_portal(portal_cell, get_hall_center_cell(dst_hall_id))
		self.portal_cell_to_hall_idx[portal_cell] = dst_hall_id
		self.dst_hall_idx_to_src_hall_idxs[dst_hall_id].append(hall_idx)

	def generate_room(self):
		for cy in MAP_Y_RANGE:
			for cx in MAP_X_RANGE:
				if cx in ROOM_9_BORDERS_X or cy in ROOM_9_BORDERS_Y:
					self.map[cx, cy] = CELL_WALL

		while True:
			for hall_idx in range(0, 9):
				debug(3, "hall_idx %d" % hall_idx)
				self.hall_center_cell_to_idx[get_hall_center_cell(hall_idx)] = hall_idx
				if hall_idx != 4:
					for portal_idx in range(0, 4):
						debug(3, "  portal_idx %d" % portal_idx)
						if portal_idx in SKIPPED_PORTAL_IDXS_PER_NUM[self.num_portals_per_hall - 1]:
							continue
						portal_cell = get_hall_portal_cell(hall_idx, portal_idx)
						dst_hall_id = randint(0, 8)
						self.create_portal(portal_cell, hall_idx, dst_hall_id)
				else:
					portal_cell = ROOM_9_X1[hall_idx], ROOM_9_Y1[hall_idx]
					self.create_portal(portal_cell, hall_idx, 0)
					self.map[ROOM_9_X2[hall_idx], ROOM_9_Y2[hall_idx]] = CELL_FINISH

			if self.is_fully_reachable_and_solvable():
				if "has_start" not in self.level:
					self.Globals.set_char_cell(get_hall_center_cell(0))
				return

			self.portal_cell_to_hall_idx = {}
			self.dst_hall_idx_to_src_hall_idxs = {i: [] for i in range(0, 9)}

	def modify_cell_types_to_draw(self, cell, cell_types):
		if self.draw_hint_mode and (self.map[cell] == CELL_PORTAL or cell in self.hall_center_cell_to_idx):
			cell_types.append(CELL_ROTATEPIC_HINT)

	def get_cell_image_to_draw(self, cell, cell_type):
		if cell_type == CELL_ROTATEPIC_HINT:
			hall_idx = self.hall_center_cell_to_idx[cell] if cell in self.hall_center_cell_to_idx else self.portal_cell_to_hall_idx[cell]
			return create_text_cell_image(str(hall_idx + 1))
		return None

	def on_press_key(self, keyboard):
		self.draw_hint_mode = keyboard.kp_enter and not self.draw_hint_mode

