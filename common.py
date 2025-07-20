import inspect
from traceback import extract_stack

def warn(error, with_trace=False):
	print(error)
	if with_trace:
		for fs in extract_stack():
			if fs.name in ("warn", "die"):
				continue
			print("%s:%d in %s\n  %s" % (fs.filename, fs.lineno, fs.name, fs.line))

def die(error, with_trace=False):
	warn(error, with_trace)
	quit()

def get_pgzero_game_from_stack():
	for frame_info in inspect.stack():
		frame = frame_info.frame
		func_name = frame.f_code.co_name
		if func_name == 'mainloop' and 'self' in frame.f_locals:
			self_obj = frame.f_locals['self']
			if type(self_obj).__name__ == 'PGZeroGame':
					return self_obj
	die("PGZeroGame not found in stack", True)

