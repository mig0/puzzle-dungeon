import sys, inspect

CELL_W = 64
CELL_H = 64

MAP_POS_X1 = 0
MAP_POS_Y1 = 0

DEFAULT_MAP_SIZE = (13, 13)

MAP_SIZE = None
MAP_SIZE_X = None
MAP_SIZE_Y = None
PLAY_SIZE_X = None
PLAY_SIZE_Y = None
MAP_W = None
MAP_H = None
WIDTH = None
HEIGHT = None
POS_CENTER_X = None
POS_CENTER_Y = None
POS_STATUS_Y = None
PLAY_X1 = None
PLAY_X2 = None
PLAY_Y1 = None
PLAY_Y2 = None
PLAY_X_RANGE = None
PLAY_Y_RANGE = None
MAP_X_RANGE = None
MAP_Y_RANGE = None
ROOM_4_X1 = None
ROOM_4_X2 = None
ROOM_4_Y1 = None
ROOM_4_Y2 = None
ROOM_4_BORDERS_X = None
ROOM_4_BORDERS_Y = None
ROOM_9_X1 = None
ROOM_9_X2 = None
ROOM_9_Y1 = None
ROOM_9_Y2 = None
ROOM_9_BORDERS_X = None
ROOM_9_BORDERS_Y = None

def set_map_size(size, has_border=True):
	global MAP_SIZE
	global MAP_SIZE_X
	global MAP_SIZE_Y
	global PLAY_SIZE_X
	global PLAY_SIZE_Y
	global MAP_W
	global MAP_H
	global WIDTH
	global HEIGHT
	global POS_CENTER_X
	global POS_CENTER_Y
	global POS_STATUS_Y
	global PLAY_X1
	global PLAY_X2
	global PLAY_Y1
	global PLAY_Y2
	global PLAY_X_RANGE
	global PLAY_Y_RANGE
	global MAP_X_RANGE
	global MAP_Y_RANGE
	global ROOM_4_X1
	global ROOM_4_X2
	global ROOM_4_Y1
	global ROOM_4_Y2
	global ROOM_4_BORDERS_X
	global ROOM_4_BORDERS_Y
	global ROOM_9_X1
	global ROOM_9_X2
	global ROOM_9_Y1
	global ROOM_9_Y2
	global ROOM_9_BORDERS_X
	global ROOM_9_BORDERS_Y

	border_width = 1 if has_border else 0

	if size == MAP_SIZE and PLAY_X1 == border_width:
		return

	MAP_SIZE = size

	MAP_SIZE_X = size[0]
	MAP_SIZE_Y = size[1]

	PLAY_SIZE_X = MAP_SIZE_X - 2 * border_width
	PLAY_SIZE_Y = MAP_SIZE_Y - 2 * border_width

	MAP_W = CELL_W * MAP_SIZE_X
	MAP_H = CELL_H * MAP_SIZE_Y

	WIDTH = CELL_W * MAP_SIZE_X
	HEIGHT = CELL_H * (MAP_SIZE_Y + 1)
	POS_CENTER_X = MAP_W / 2
	POS_CENTER_Y = MAP_H / 2
	POS_STATUS_Y = HEIGHT - CELL_H / 2

	PLAY_X1 = border_width
	PLAY_X2 = PLAY_X1 + PLAY_SIZE_X - 1
	PLAY_Y1 = border_width
	PLAY_Y2 = PLAY_Y1 + PLAY_SIZE_Y - 1

	PLAY_X_RANGE = range(PLAY_X1, PLAY_X2 + 1)
	PLAY_Y_RANGE = range(PLAY_Y1, PLAY_Y2 + 1)

	MAP_X_RANGE = range(0, MAP_SIZE_X)
	MAP_Y_RANGE = range(0, MAP_SIZE_Y)

	odd_room_size_x = (PLAY_SIZE_X - 1) // 2
	odd_room_size_y = (PLAY_SIZE_Y - 1) // 2
	ROOM_4_X1 = [
		PLAY_X1,
		PLAY_X1 + odd_room_size_x + 1,
		PLAY_X1,
		PLAY_X1 + odd_room_size_x + 1,
	]
	ROOM_4_X2 = [
		PLAY_X1 + odd_room_size_x - 1,
		PLAY_X2,
		PLAY_X1 + odd_room_size_x - 1,
		PLAY_X2,
	]
	ROOM_4_Y1 = [
		PLAY_Y1,
		PLAY_Y1,
		PLAY_Y1 + odd_room_size_y + 1,
		PLAY_Y1 + odd_room_size_y + 1,
	]
	ROOM_4_Y2 = [
		PLAY_Y1 + odd_room_size_y - 1,
		PLAY_Y1 + odd_room_size_y - 1,
		PLAY_Y2,
		PLAY_Y2,
	]

	ROOM_4_BORDERS_X = [ROOM_4_X2[0] + 1]
	ROOM_4_BORDERS_Y = [ROOM_4_Y2[0] + 1]

	odd_room_size_x = (PLAY_SIZE_X - 1) // 3
	evn_room_size_x = PLAY_SIZE_X - 2 - (PLAY_SIZE_X - 1) // 3 * 2
	odd_room_size_y = (PLAY_SIZE_Y - 1) // 3
	evn_room_size_y = PLAY_SIZE_Y - 2 - (PLAY_SIZE_Y - 1) // 3 * 2
	ROOM_9_X1 = [
		PLAY_X1,
		PLAY_X1 + odd_room_size_x + 1,
		PLAY_X1 + odd_room_size_x + 1 + evn_room_size_x + 1,
		PLAY_X1,
		PLAY_X1 + odd_room_size_x + 1,
		PLAY_X1 + odd_room_size_x + 1 + evn_room_size_x + 1,
		PLAY_X1,
		PLAY_X1 + odd_room_size_x + 1,
		PLAY_X1 + odd_room_size_x + 1 + evn_room_size_x + 1,
	]
	ROOM_9_X2 = [
		ROOM_9_X1[0] + odd_room_size_x - 1,
		ROOM_9_X1[1] + evn_room_size_x - 1,
		PLAY_X2,
		ROOM_9_X1[0] + odd_room_size_x - 1,
		ROOM_9_X1[1] + evn_room_size_x - 1,
		PLAY_X2,
		ROOM_9_X1[0] + odd_room_size_x - 1,
		ROOM_9_X1[1] + evn_room_size_x - 1,
		PLAY_X2,
	]
	ROOM_9_Y1 = [
		PLAY_Y1,
		PLAY_Y1,
		PLAY_Y1,
		PLAY_Y1 + odd_room_size_y + 1,
		PLAY_Y1 + odd_room_size_y + 1,
		PLAY_Y1 + odd_room_size_y + 1,
		PLAY_Y1 + odd_room_size_y + 1 + evn_room_size_y + 1,
		PLAY_Y1 + odd_room_size_y + 1 + evn_room_size_y + 1,
		PLAY_Y1 + odd_room_size_y + 1 + evn_room_size_y + 1,
	]
	ROOM_9_Y2 = [
		ROOM_9_Y1[0] + odd_room_size_y - 1,
		ROOM_9_Y1[0] + odd_room_size_y - 1,
		ROOM_9_Y1[0] + odd_room_size_y - 1,
		ROOM_9_Y1[3] + evn_room_size_y - 1,
		ROOM_9_Y1[3] + evn_room_size_y - 1,
		ROOM_9_Y1[3] + evn_room_size_y - 1,
		PLAY_Y2,
		PLAY_Y2,
		PLAY_Y2,
	]

	ROOM_9_BORDERS_X = [ROOM_9_X2[0] + 1, ROOM_9_X2[1] + 1]
	ROOM_9_BORDERS_Y = [ROOM_9_Y2[0] + 1, ROOM_9_Y2[3] + 1]

def import_size_constants(dest_module=None):
	if hasattr(dest_module, "__module__"):
		dest_module = sys.modules[dest_module.__module__]
	dest_globals = inspect.stack()[1][0].f_globals if dest_module is None else vars(dest_module)

	for name in dir(sys.modules[__name__]):
		if name.isupper():
			dest_globals[name] = globals()[name]
