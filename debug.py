from constants import DEBUG_LEVEL

def debug(level, str, depth=None):
	if DEBUG_LEVEL < level:
		return
	if depth is not None:
		print(" " * depth, end="")
	print(str)

