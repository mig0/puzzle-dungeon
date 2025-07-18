from levels import levels

levels = sorted(levels, key=lambda level: level["n"])
level_idx = -1

def is_level_unset():
	return level_idx == -1

def is_last_special_level(offset=0):
	return level_idx + offset == len(levels)

def is_level_out_of_range(offset=0):
	return level_idx + offset < 0 or level_idx + offset > len(levels)

def set_level(offset):
	global level_idx

	level_idx += offset
	return None if level_idx < 0 or level_idx >= len(levels) else levels[level_idx]

def reset_level():
	global level_idx

	level_idx = -1

def get_prev_level_offset(offset=0):
	if level_idx + offset > 0:
		offset -= 1
	return offset

def get_next_level_offset(offset=0):
	if level_idx + offset < len(levels):
		offset += 1
	return offset

def level_to_group_n(offset=0):
	if is_last_special_level(offset):
		return 999999999
	return int(levels[level_idx + offset]["n"])

def get_curr_level_group_offset(offset=0):
	# 1.1 -> 1.1; 1.9 -> 1.1; 2.2 -> 2.1; 3.1 -> 3.1
	curr_group_n = level_to_group_n(offset)

	while True:
		offset -= 1
		if level_idx + offset < 0:
			return offset + 1
		if level_to_group_n(offset) < curr_group_n:
			return offset + 1

def get_prev_level_group_offset(offset=0):
	# 1.1 -> 1.1; 1.9 -> 1.1; 2.2 -> 1.1; 3.1 -> 2.1
	offset = get_curr_level_group_offset(offset)

	offset = get_prev_level_offset(offset)

	offset = get_curr_level_group_offset(offset)

	return offset

def get_next_level_group_offset(offset=0):
	# 1.1 -> 2.1; 1.9 -> 2.1; 2.2 -> 3.1; 3.1 -> 4.1
	curr_group_n = level_to_group_n(offset)

	while True:
		offset = get_next_level_offset(offset)
		if level_idx + offset >= len(levels) or level_to_group_n(offset) > curr_group_n:
			return offset

