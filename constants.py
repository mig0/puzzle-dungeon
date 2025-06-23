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
CELL_DIR_L  = '←'
CELL_DIR_R  = '→'
CELL_DIR_U  = '↑'
CELL_DIR_D  = '↓'

CELL_CURSOR = '▉'
CELL_SPECIAL0 = '0'
CELL_INTERNAL1 = '1'
CELL_OUTER_WALL = '▒'

CELL_WALL_TYPES = (CELL_WALL, CELL_OUTER_WALL)
CELL_FLOOR_TYPES_RANDGEN = (CELL_CRACK, CELL_BONES, CELL_ROCKS)
CELL_FLOOR_TYPES_FREQUENT = (*CELL_FLOOR_TYPES_RANDGEN, *((CELL_FLOOR,) * EMPTY_FLOOR_FREQUENCY))
CELL_FLOOR_TYPES = (*CELL_FLOOR_TYPES_RANDGEN, CELL_FLOOR)
CELL_FLOOR_EXTENSIONS = (*CELL_FLOOR_TYPES_RANDGEN, CELL_PLATE, CELL_START, CELL_FINISH, CELL_PORTAL, CELL_GATE0, CELL_GATE1, CELL_LOCK1, CELL_LOCK2, CELL_DIR_L, CELL_DIR_R, CELL_DIR_U, CELL_DIR_D)
CELL_ENEMY_PLACE_OBSTACLES = (*CELL_WALL_TYPES, CELL_PORTAL, CELL_START, CELL_FINISH, CELL_GATE0, CELL_GATE1, CELL_SAND, CELL_LOCK1, CELL_LOCK2, CELL_VOID)
CELL_CHAR_PLACE_OBSTACLES = (*CELL_WALL_TYPES, CELL_PLATE, CELL_PORTAL, CELL_GATE0, CELL_GATE1, CELL_SAND, CELL_LOCK1, CELL_LOCK2, CELL_VOID)
CELL_CHAR_MOVE_OBSTACLES  = (*CELL_WALL_TYPES, CELL_GATE0, CELL_LOCK1, CELL_LOCK2, CELL_VOID, CELL_DIR_L, CELL_DIR_R, CELL_DIR_U, CELL_DIR_D)

ACTOR_CHARS = {
	'heart':  '♥',
	'sword':  '⸸',
	'might':  '🖠',
	'key1':   '¹',
	'key2':   '²',
	'enemy':  '🕱',
	'barrel': '■',
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

MOVE_TYPE_DIRECTIONS = {
	MOVE_A: [(-1, 0), (+1, 0), (0, -1), (0, +1)],
	MOVE_H: [(-1, 0), (+1, 0)],
	MOVE_V: [(0, -1), (0, +1)],
	MOVE_L: [(-1, 0)],
	MOVE_R: [(+1, 0)],
	MOVE_U: [(0, -1)],
	MOVE_D: [(0, +1)],
	MOVE_N: [],
}
MOVE_TYPES = *MOVE_TYPE_DIRECTIONS,

LIFT_CHARS = {
	MOVE_A: '✥',
	MOVE_H: '↔',
	MOVE_V: '↕',
	MOVE_L: '←',
	MOVE_R: '→',
	MOVE_U: '↑',
	MOVE_D: '↓',
	MOVE_N: '◉',
}

LIFT_MOVE_TYPES_BY_CHAR = {v: k for k, v in LIFT_CHARS.items()}

IMAGES_DIR_PREFIX = DATA_DIR + '/images/'
DEFAULT_IMAGE_PREFIX = 'default/'
MAPS_DIR_PREFIX = DATA_DIR + '/maps/'
