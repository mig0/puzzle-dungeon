from config import *

CELL_WALL   = '▓'
CELL_FLOOR  = '•'
CELL_CRACK  = '⦁'
CELL_BONES  = '⸗'
CELL_ROCKS  = '◦'
CELL_PLATE  = '⎵'
CELL_GATE0  = '★'
CELL_GATE1  = '☆'
CELL_START  = '►'
CELL_FINISH = '◄'
CELL_PORTAL = '𝟘'
CELL_SAND   = '⧛'
CELL_LOCK1  = '𝟙'
CELL_LOCK2  = '𝟚'
CELL_VOID   = '·'
CELL_ODIRL  = '⇺'
CELL_ODIRR  = '⇻'
CELL_ODIRU  = '⇞'
CELL_ODIRD  = '⇟'
CELL_GLASS  = '░'
CELL_TRAP0  = '⬨'
CELL_TRAP1  = '⬧'

CELL_CURSOR = '▉'
CELL_SPECIAL0 = '0'
CELL_INTERNAL1 = '1'
CELL_OUTER_WALL = '▒'

CELL_WALL_TYPES = (CELL_WALL, CELL_OUTER_WALL)
CELL_FLOOR_TYPES_RANDGEN = (CELL_CRACK, CELL_BONES, CELL_ROCKS)
CELL_FLOOR_TYPES_FREQUENT = (*CELL_FLOOR_TYPES_RANDGEN, *((CELL_FLOOR,) * EMPTY_FLOOR_FREQUENCY))
CELL_FLOOR_TYPES = (*CELL_FLOOR_TYPES_RANDGEN, CELL_FLOOR)
CELL_FLOOR_EXTENSIONS = (*CELL_FLOOR_TYPES_RANDGEN, CELL_PLATE, CELL_START, CELL_FINISH, CELL_PORTAL, CELL_GATE0, CELL_GATE1, CELL_LOCK1, CELL_LOCK2, CELL_ODIRL, CELL_ODIRR, CELL_ODIRU, CELL_ODIRD, CELL_GLASS, CELL_TRAP0, CELL_TRAP1)
CELL_ENEMY_PLACE_OBSTACLES = (*CELL_WALL_TYPES, CELL_PORTAL, CELL_START, CELL_FINISH, CELL_GATE0, CELL_GATE1, CELL_SAND, CELL_LOCK1, CELL_LOCK2, CELL_VOID, CELL_GLASS, CELL_TRAP0, CELL_TRAP1)
CELL_CHAR_PLACE_OBSTACLES = (*CELL_WALL_TYPES, CELL_PLATE, CELL_PORTAL, CELL_GATE0, CELL_GATE1, CELL_SAND, CELL_LOCK1, CELL_LOCK2, CELL_VOID, CELL_GLASS, CELL_TRAP0, CELL_TRAP1)
CELL_CHAR_MOVE_OBSTACLES  = (*CELL_WALL_TYPES, CELL_GATE0, CELL_LOCK1, CELL_LOCK2, CELL_VOID, CELL_ODIRL, CELL_ODIRR, CELL_ODIRU, CELL_ODIRD, CELL_GLASS)

ACTOR_CHARS = {
	'heart':  '♥',
	'sword':  '⸸',
	'might':  '🖠',
	'key1':   '¹',
	'key2':   '²',
	'enemy':  '🕱',
	'barrel': '■',
	'mirror': '▬',
	'char':   '☻',
	'npc':    '☀',
}

ACTOR_ON_PLATE_CHARS = {
	'heart':  '♡',
	'sword':  '⸷',
	'might':  '🖞',
	'key1':   '₁',
	'key2':   '₂',
	'enemy':  '☠',
	'barrel': '□',
	'mirror': '▭',
	'char':   '☺',
	'npc':    '☼',
}

ACTOR_AND_PLATE_BY_CHAR = {v: (k, v != ACTOR_CHARS[k]) for k, v in {*ACTOR_CHARS.items(), *ACTOR_ON_PLATE_CHARS.items(),}}

MOVE_A = 'a'
MOVE_H = 'h'
MOVE_V = 'v'
MOVE_L = 'l'
MOVE_R = 'r'
MOVE_U = 'u'
MOVE_D = 'd'
MOVE_N = 'n'

DIRECTION_L = 'l'
DIRECTION_R = 'r'
DIRECTION_U = 'u'
DIRECTION_D = 'd'

DIR_L = (-1, 0)
DIR_R = (+1, 0)
DIR_U = (0, -1)
DIR_D = (0, +1)

DIRS_BY_NAME = {
	DIRECTION_L: DIR_L,
	DIRECTION_R: DIR_R,
	DIRECTION_U: DIR_U,
	DIRECTION_D: DIR_D,
}
DIR_NAMES = {v: k for k, v in DIRS_BY_NAME.items()}
DIRS = *DIR_NAMES,

MOVE_TYPE_DIRS = {
	MOVE_A: [DIR_L, DIR_R, DIR_U, DIR_D],
	MOVE_H: [DIR_L, DIR_R],
	MOVE_V: [DIR_U, DIR_D],
	MOVE_L: [DIR_L],
	MOVE_R: [DIR_R],
	MOVE_U: [DIR_U],
	MOVE_D: [DIR_D],
	MOVE_N: [],
}
MOVE_TYPES = *MOVE_TYPE_DIRS,

CART_CHARS = [
	# regular
	{
		MOVE_A: '✣',
		MOVE_H: '⇿',
		MOVE_V: '⇳',
		MOVE_L: '⇦',
		MOVE_R: '⇨',
		MOVE_U: '⇧',
		MOVE_D: '⇩',
		MOVE_N: '◍',
	},
	# mirror
	{
		MOVE_A: '✢',
		MOVE_H: '⇔',
		MOVE_V: '⇕',
		MOVE_L: '⇐',
		MOVE_R: '⇒',
		MOVE_U: '⇑',
		MOVE_D: '⇓',
		MOVE_N: '◌',
	},
]

LIFT_CHARS = [
	# regular
	{
		MOVE_A: '✥',
		MOVE_H: '↔',
		MOVE_V: '↕',
		MOVE_L: '←',
		MOVE_R: '→',
		MOVE_U: '↑',
		MOVE_D: '↓',
		MOVE_N: '◉',
	},
	# mirror
	{
		MOVE_A: '✤',
		MOVE_H: '⇆',
		MOVE_V: '⇅',
		MOVE_L: '⇇',
		MOVE_R: '⇉',
		MOVE_U: '⇈',
		MOVE_D: '⇊',
		MOVE_N: '◎',
	},
]

CART_MOVE_TYPES_BY_CHAR = {v: k for d in CART_CHARS for k, v in d.items()}
LIFT_MOVE_TYPES_BY_CHAR = {v: k for d in LIFT_CHARS for k, v in d.items()}
MOVE_TYPES_BY_CHAR = {**CART_MOVE_TYPES_BY_CHAR, **LIFT_MOVE_TYPES_BY_CHAR}

MIRROR_CHARS = tuple(v for d in (CART_CHARS[1], LIFT_CHARS[1]) for k, v in d.items())
MIRROR_ORIENTATION_CHARS = [ '|', '/', '-', '\\' ]

IMAGES_DIR_PREFIX = DATA_DIR + '/images/'
DEFAULT_IMAGE_PREFIX = 'default/'
MAPS_DIR_PREFIX = DATA_DIR + '/maps/'
