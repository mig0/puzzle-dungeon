from constants import DEFAULT_DEBUG_LVL

debug_lvl = DEFAULT_DEBUG_LVL

def debug(lvl, str, depth=None):
	if debug_lvl < lvl:
		return
	if depth is not None:
		print(" " * depth, end="")
	print(str)

def get_debug_lvl():
	return debug_lvl

def set_debug_level(lvl):
	global debug_lvl
	debug_lvl = lvl
