import sys
import os
import re

USE_COLORS = not os.environ.get('NO_COLOR') and (sys.stdout.isatty() or os.environ.get('MSYSTEM'))

COLOR_NONE      = ""
COLOR_BOLD      = "1"
COLOR_DIM       = "2"
COLOR_ITALIC    = "3"
COLOR_UNDERLINE = "4"
COLOR_BLINK     = "5"
COLOR_STRIKETHR = "9"

COLOR_BLACK     = "30"
COLOR_RED       = "31"
COLOR_GREEN     = "32"
COLOR_YELLOW    = "33"
COLOR_BLUE      = "34"
COLOR_MAGENTA   = "35"
COLOR_CYAN      = "36"
COLOR_WHITE     = "37"

COLOR_BBLACK    = "90"
COLOR_BRED      = "91"
COLOR_BGREEN    = "92"
COLOR_BYELLOW   = "93"
COLOR_BBLUE     = "94"
COLOR_BMAGENTA  = "95"
COLOR_BCYAN     = "96"
COLOR_BWHITE    = "97"

COLOR_F_BLACK   = "38;5;0"
COLOR_F_VULCAN  = "38;5;238"
COLOR_F_GRAY    = "38;5;8"
COLOR_F_SILVER  = "38;5;7"
COLOR_F_WHITE   = "38;5;231"
COLOR_F_GREEN   = "38;5;82"
COLOR_F_LIME    = "38;5;154"
COLOR_F_YELLOW  = "38;5;226"
COLOR_F_ORANGE  = "38;5;208"
COLOR_F_RED     = "38;5;196"
COLOR_F_VIOLET  = "38;5;129"
COLOR_F_PURPLE  = "38;5;93"
COLOR_F_ORCHID  = "38;5;105"
COLOR_F_BLUE    = "38;5;20"
COLOR_F_MALIBU  = "38;5;38"
COLOR_F_AQUA    = "38;5;51"
COLOR_F_PEARL   = "38;5;49"

COLOR_B_BLACK   = "48;5;0"
COLOR_B_VULCAN  = "48;5;238"
COLOR_B_GRAY    = "48;5;8"
COLOR_B_SILVER  = "48;5;7"
COLOR_B_WHITE   = "48;5;231"
COLOR_B_GREEN   = "48;5;82"
COLOR_B_LIME    = "48;5;154"
COLOR_B_YELLOW  = "48;5;226"
COLOR_B_ORANGE  = "48;5;208"
COLOR_B_RED     = "48;5;196"
COLOR_B_VIOLET  = "48;5;129"
COLOR_B_PURPLE  = "48;5;93"
COLOR_B_ORCHID  = "48;5;105"
COLOR_B_BLUE    = "48;5;20"
COLOR_B_MALIBU  = "48;5;38"
COLOR_B_AQUA    = "48;5;51"
COLOR_B_PEARL   = "48;5;49"

_MATCHING_PAIRS = (("(", ")"), ("[", "]"), ("{", "}"), ("'", "'"), ('"', '"'))
_MATCHING_PAITS_DICT = dict(_MATCHING_PAIRS)

def colorize(str, color):
	return "\033[%sm%s\033[0m" % (color, str) if USE_COLORS else str

def _split_top_level(s, sep):
	# split string by sep, but ignore separators inside matching pairs
	out = []
	buf = []
	level = 0

	pairs = _MATCHING_PAITS_DICT
	opening = set(pairs.keys())
	closing = set(pairs.values())

	for ch in s:
		if level > 0 and ch in closing:
			level -= 1
		elif ch in opening:
			level += 1

		if ch == sep and level == 0:
			out.append("".join(buf))
			buf = []
		else:
			buf.append(ch)

	out.append("".join(buf))
	return out

def _is_dict_like(s):
	if ":" not in s:
		return False

	parts = _split_top_level(s, ",")
	if len(parts) == 1 and re.search(r'^\d+:\d\d(:\d\d)?$', parts[0]):
		return False

	for p in parts:
		p = p.strip()
		if not p:
			return False

		kv = _split_top_level(p, ":")
		if len(kv) != 2:
			return False

		for item in kv[0].strip(), kv[1].strip():
			if " " in item and not ((len(item) >= 2) and ((item[0], item[-1]) in _MATCHING_PAIRS)):
				return False

	return True

def colorize_auto(s):
	if type(s) != str:
		s = str(s)
	if not USE_COLORS:
		return s
	if s == 'OK' or s == 'found':
		return colorize(s, COLOR_GREEN)
	elif s == 'NEW RECORD':
		return colorize(s, COLOR_BGREEN)
	elif s == 'WORSE' or s == 'not found':
		return colorize(s, COLOR_RED)
	elif s == 'N/A':
		return colorize(s, COLOR_YELLOW)
	elif _is_dict_like(s):
		colored_items = []
		for item in _split_top_level(s, ","):
			item = item.strip()
			if not item:
				return s
			kv = _split_top_level(item, ":")
			if len(kv) != 2:
				return s

			ckey = colorize(kv[0].strip(), COLOR_CYAN)
			cval = colorize(kv[1].strip(), COLOR_YELLOW)

			colored_items.append(f"{ckey}: {cval}")

		return ", ".join(colored_items)
	elif re.search(r'\d', s):
		s = re.sub(r'\b\d+:\d\d(:\d\d)?\b', lambda match: colorize(match.group(0), COLOR_BOLD), s)
		s = re.sub(r'\b(?<!:)\d+(\.\d+)?\b', lambda match: colorize(match.group(0), COLOR_CYAN), s)
	return s
