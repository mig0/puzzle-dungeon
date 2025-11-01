from common import load_tabbed_yaml, get_pgzero_game_from_stack, warn, die
from config import DATA_DIR, pgconsole_config
from level import Collection, Level, parse_level_id
from sokobanparser import parse_sokoban_levels
from sizetools import set_display_size
from room import room
import pygame
import copy
import os

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

class CharMove:
	def __init__(self, char, dir):
		self.char = char
		self.dir = dir
		self.is_barrel_push = False
		self.is_barrel_pull = False
		self.is_barrel_shift = False
		self.is_continued = False

	def store_pos(self):
		self.old_char_cell = self.char.c
		self.old_char_pos = self.char.pos

	def move(self):
		self.char.move(self.dir)

	def undo_move(self):
		self.char.move(self.dir, undo=True)

	def finalize(self):
		self.is_barrel_shift = self.is_barrel_push or self.is_barrel_pull
		self.is_continued = False

class Game:
	def __init__(self):
		self.map = None
		self.screen = None
		self.console = None
		self.char_cells = None
		self.orig_handlers = {}
		self.requested_new_level = None
		self.undo_frames = []
		self.in_level = False
		self.during_undo = False
		self.last_char_move = None

		self._set_display_size()
		self.screen_size_fitting_display = None

		self.collections = []
		self.level = Level()
		self._register_all_collections()
		self._create_custom_collection()

	def begin_char_move(self, char, dir):
		char_move = self.last_char_move
		if not (char_move and char_move.is_continued):
			char_move = CharMove(char, dir)
		char_move.store_pos()
		char_move.move()
		return char_move

	def cancel_char_move(self, char_move):
		char_move.undo_move()
		char_move.finalize()

	def commit_char_move(self, char_move):
		char_move.finalize()
		self.last_char_move = char_move

	def init_console(self):
		self.console = None
		try:
			from pgconsole import Console
			self.console = Console(self, WIDTH, pgconsole_config)
		except:
			pass

	def is_console_enabled(self):
		return self.console and self.console.enabled

	def show_console(self):
		if self.is_console_enabled():
			self.console.show(game.screen)

	def update_console(self, event):
		if not self.is_console_enabled():
			return
		if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
			self.toggle_console()
			return
		self.console.update([event])

	def toggle_console(self):
		if self.console:
			self.console.toggle()
			pgzgame = get_pgzero_game_from_stack()
			for event_type in (pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.TEXTINPUT):
				if self.is_console_enabled():
					# replace handlers temporarily
					self.orig_handlers[event_type] = pgzgame.handlers.get(event_type)
					pgzgame.handlers[event_type] = self.update_console
				else:
					# restore original handlers
					pgzgame.handlers[event_type] = self.orig_handlers[event_type]
					if not pgzgame.handlers[event_type]: del pgzgame.handlers[event_type]

	def set_char_cell(self, cell, room_idx=None):
		self.char_cells[room.idx if room_idx is None else room_idx] = cell

	@property
	def undo_frame(self):
		return self.undo_frames[-1] if self.undo_frames else None

	def start_level(self):
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

		self.during_undo = True
		self.undo_frames.pop().restore_all_changes()
		self.during_undo = False

		return True

	def _set_display_size(self):
		display_size = pygame.display.get_desktop_sizes()[0]
		set_display_size(display_size)

	def calc_screen_size_fitting_display(self):
		if DISPLAY_W > WIDTH and DISPLAY_H - EXTRA_DISPLAY_H > HEIGHT:
			self.screen_size_fitting_display = None
			return
		scale_factor = max(WIDTH / DISPLAY_W, HEIGHT / (abs(DISPLAY_H - EXTRA_DISPLAY_H) or 1))
		self.screen_size_fitting_display = (int(WIDTH / scale_factor), int(HEIGHT / scale_factor))

	def set_requested_new_level(self, level_id=None, reload_stored=False):
		if not level_id:
			level_id = self.level.get_id()
		if not self.is_valid_level_id(level_id):
			return False
		self.requested_new_level = (level_id, reload_stored)
		return True

	def _find_all_collections(self, dir_path, id, all_collections=None):
		if all_collections is None:
			all_collections = []

		config_path = dir_path + '/config'
		if os.path.isfile(config_path):
			config = load_tabbed_yaml(config_path)
			collection = Collection(id, config)
			collections = []
			sokoban_map_files_by_id = {}
			if sokoban_map_files_by_sub_id := config.get('sokoban-map-files'):
				del config['sokoban-map-files']
				if type(sokoban_map_files_by_sub_id) == tuple:
					sokoban_map_files_by_sub_id_tuple = sokoban_map_files_by_sub_id
					width = len(str(len(sokoban_map_files_by_sub_id_tuple)))
					sokoban_map_files_by_sub_id = {}
					for i, sokoban_map_file in enumerate(sokoban_map_files_by_sub_id_tuple):
						sub_id = "%0*d" % (width, i + 1)
						sokoban_map_files_by_sub_id[sub_id] = sokoban_map_file
				for sub_id, sokoban_map_file in sokoban_map_files_by_sub_id.items():
					c = copy.copy(collection)
					c.id += '/%s' % sub_id
					c.name += ' - %s' % sub_id
					collections.append(c)
					sokoban_map_files_by_id[c.id] = sokoban_map_file
			elif collection.level_configs is not None or config.get('sokoban-map-file'):
				collections.append(collection)
			for collection in collections:
				if sokoban_map_file := config.get('sokoban-map-file') or sokoban_map_files_by_id.get(collection.id):
					if 'sokoban-map-file' in config:
						del config['sokoban-map-file']
					collection.level_configs = parse_sokoban_levels(sokoban_map_file)
				if collection.num_levels == 0:
					warn("Ignoring collection %s with no levels" % collection.id)
				else:
					all_collections.append(collection)
			if not collections:
				warn("Ignoring collection %s with no levels and no sokoban-map-files" % collection.id)

		with os.scandir(dir_path) as entries:
			for entry in entries:
				if entry.is_dir():
					entry_id = id + ('/' if id else '') + entry.name
					self._find_all_collections(dir_path + '/' + entry.name, entry_id, all_collections)

		return all_collections

	def _register_all_collections(self):
		collections = self._find_all_collections(DATA_DIR + '/levels', '')

		# assign unique integer 'n' with magic-n fill logic
		def sort_collection_by_magic_n(c):
			# None goes last; otherwise by magic_n numeric; tie-breaker by id
			return (c.magic_n or 1000, c.id)

		collections.sort(key=sort_collection_by_magic_n)

		used_n = set()
		next_n = 1

		for collection in collections:
			if collection.magic_n is not None and next_n < collection.magic_n:
				next_n = collection.magic_n
			while next_n in used_n:
				next_n += 1
			collection.n = next_n
			used_n.add(next_n)
			next_n += 1

		self.collections = sorted(collections, key=lambda c: c.n)

	def _create_custom_collection(self):
		self.custom_collection_config = {
			'icon': 'default/trap0',
			'name': 'Custom collection',
			'n': 0,
		}
		self.custom_collection = Collection("custom", self.custom_collection_config)

	def set_custom_collection_config(self, config):
		config |= self.custom_collection_config
		self.custom_collection.config = config

	def set_custom_collection_level_configs(self, level_configs):
		num_levels0 = self.custom_collection.num_levels
		self.custom_collection.level_configs = level_configs
		num_levels1 = self.custom_collection.num_levels
		if num_levels0 and not num_levels1:
			game.collections.remove(self.custom_collection)
		if not num_levels0 and num_levels1:
			game.collections.insert(0, self.custom_collection)
		if num_levels1 and game.set_requested_new_level(self.custom_collection.get_level_id()):
			self.level.unset()
			return True
		return False

	def get_collection_level_config_by_id(self, level_id, assert_valid=False):
		collection_id, level_index = parse_level_id(level_id, assert_valid)
		if not collection_id:
			return (None, None, None)
		collection = self.get_collection_by_id(collection_id)
		if collection and 1 <= level_index <= collection.num_levels:
			return collection, level_index, collection.level_configs[level_index - 1]
		if assert_valid:
			if not collection:
				die("Unexisting collection for level_id %s" % level_id, True)
			die("Level is out of range in collection for level_id %s" % level_id, True)
		return (None, None, None)

	def get_collection_by_id(self, collection_id):
		try:
			return next(c for c in self.collections if c.has_id(collection_id))
		except:
			return None

	def get_adjacent_collection(self, offset, collection=None):
		collection = collection or self.level.collection
		idx = self.collections.index(collection)
		if offset < 0 and idx + offset < 0 or offset > 0 and idx + offset > len(self.collections) - 1:
			return None
		return self.collections[idx + offset]

	def get_adjacent_level_id(self, offset, collection_offset=None):
		if collection_offset is not None:
			collection = self.get_adjacent_collection(collection_offset)
			if collection is None:
				collection = self.level.collection
				if offset <= 0:
					# very first level
					return collection.get_level_id()
				if self.level.index >= collection.num_levels:
					# end of levels
					return None
				# very last level
				return collection.get_id() + collection.get_padded_level_index_suffix(collection.num_levels)
			return collection.get_level_id()

		if offset == 0:
			return self.level.get_id()
		if offset == -1:
			if self.level.index <= 1:
				collection = self.get_adjacent_collection(-1)
				if collection is None:
					return self.level.get_id()
				level_index = collection.num_levels
			else:
				collection = self.level.collection
				level_index = self.level.index - 1
		elif offset == 1:
			if self.level.index >= self.level.collection.num_levels:
				collection = self.get_adjacent_collection(+1)
				if collection is None:
					return None
				level_index = 1
			else:
				collection = self.level.collection
				level_index = self.level.index + 1
		else:
			die("Currently get_adjacent_level_id only supports offset (-1, 0, 1), not %s" % str(offset))

		return collection.get_id() + collection.get_padded_level_index_suffix(level_index)

	def set_level_id(self, level_id):
		self.level.set_from_config(*self.get_collection_level_config_by_id(level_id, True))

	def is_valid_level_id(self, level_id):
		for collection in self.collections:
			if collection.has_level_id(level_id):
				return True
		return False

game = Game()
