class UndoFrame:
	def __init__(self):
		self.map_cell_types = {}
		self.obj_states = {}
		self.extra_obj_states = {}
		self.collection_elems = []  # tuple (list-or-set, elem)

	def is_empty(self):
		return (
			not self.map_cell_types and
			not self.obj_states and
			not self.extra_obj_states and
			not self.collection_elems
		)

	def remove_empty_changes(self):
		for cell, old_cell_type in list(self.map_cell_types.items()):
			if game.map[cell] == old_cell_type:
				del self.map_cell_types[cell]

		for obj, old_state in list(self.obj_states.items()):
			if obj.get_state() == old_state:
				del self.obj_states[obj]

		for obj, old_state in list(self.extra_obj_states.items()):
			if obj.get_extra_state() == old_state:
				del self.extra_obj_states[obj]

		for collection, elem in list(self.collection_elems):
			if elem in collection:
				self.collection_elems.remove((collection, elem))

		return self.is_empty()

	def store_map_cell(self, cell):
		if not cell in self.map_cell_types:
			self.map_cell_types[cell] = game.map[cell]

	def store_obj_state(self, obj):
		if not obj in self.obj_states:
			self.obj_states[obj] = obj.get_state()

	def store_extra_obj_state(self, obj):
		if not obj in self.extra_obj_states:
			self.extra_obj_states[obj] = obj.get_extra_state()

	def store_collection_elem(self, collection, elem):
		if not (collection, elem) in self.collection_elems:
			self.collection_elems.append((collection, elem))

	def restore_all_changes(self):
		for cell, old_cell_type in self.map_cell_types.items():
			game.map[cell] = old_cell_type

		for obj, old_state in self.obj_states.items():
			obj.restore_state(old_state)

		for obj, old_state in self.extra_obj_states.items():
			obj.restore_extra_state(old_state)

		for collection, elem in self.collection_elems:
			collection.add(elem) if type(collection) == set else collection.append(elem)

class Game:
	def __init__(self):
		self.undo_frames = []
		self.in_level = False

	@property
	def undo_frame(self):
		return self.undo_frames[-1] if self.undo_frames else None

	def start_level(self, map):
		self.map = map
		self.undo_frames.clear()
		self.in_level = True
		self.start_move()  # always have undo_frame, even before the first char move

	def stop_level(self):
		self.in_level = False

	def assert_in_level(self):
		if not self.in_level:
			import inspect
			func_names = []
			frame = inspect.currentframe().f_back
			while frame:
				code = frame.f_code
				func_names.append("%s, line %s" % (code.co_qualname, code.co_firstlineno))
				frame = frame.f_back
			print("Called method outside the level. Fix the bug. Traceback:\n\t", end='')
			print('\n\t'.join(func_names))
			quit()

	def remove_empty_undo_frames(self):
		while self.undo_frames:
			if self.undo_frame.remove_empty_changes():
				self.undo_frames.pop()
			else:
				return

	def start_move(self):
		self.assert_in_level()

		self.remove_empty_undo_frames()

		self.undo_frames.append(UndoFrame())

	def remember_map_cell(self, cell):
		if not self.in_level:
			return
		self.undo_frame.store_map_cell(cell)

	def remember_obj_state(self, obj):
		if not self.in_level:
			return
		self.undo_frame.store_obj_state(obj)

	def remember_extra_obj_state(self, obj):
		if not self.in_level:
			return
		self.undo_frame.store_extra_obj_state(obj)

	def remember_collection_elem(self, collection, elem):
		if not self.in_level:
			return
		self.undo_frame.store_collection_elem(collection, elem)

	def undo_move(self):
		self.assert_in_level()

		self.remove_empty_undo_frames()

		if not self.undo_frames:
			return False

		self.undo_frames.pop().restore_all_changes()

		return True

game = Game()
