import re
import yaml
import inspect
import subprocess
from traceback import extract_stack
from datetime import datetime

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

def get_time_str(secs):
	sec = int(secs)
	min = sec / 60
	sec = sec % 60
	return "%d:%02d" % (min, sec) if min < 60 else "%d:%02d:%02d" % (min / 60, min % 60, sec)

def get_current_time_str(num_digits=0):
	return datetime.now().strftime("%H:%M:%S.%f")[:num_digits - 6 or None if 1 <= num_digits <= 6 else -7]

def open_read(filename, descr=None):
	filename_descr = "%sfile %s" % (descr + " " if descr else "", filename)
	try:
		return open(filename, "r", encoding="utf-8", errors="replace")
	except FileNotFoundError:
		die("Requested %s not found" % filename_descr)
	except PermissionError:
		die("No read permissions for %s" % filename_descr)
	except Exception as e:
		die("Can't open %s (%s)" % (filename_descr, e))

def get_pgzero_game_from_stack():
	for frame_info in inspect.stack():
		frame = frame_info.frame
		func_name = frame.f_code.co_name
		if func_name == 'mainloop' and 'self' in frame.f_locals:
			self_obj = frame.f_locals['self']
			if type(self_obj).__name__ == 'PGZeroGame':
					return self_obj
	die("PGZeroGame not found in stack", True)

def markdown_to_html(text):
	markdown_to_html_cmd = "pandoc -f markdown -t html --columns 100"
	try:
		result = subprocess.run(
			markdown_to_html_cmd.split(),
			input=text,
			capture_output=True,
			text=True,
		)
		return result.stdout
	except Exception as e:
		if hasattr(e, "stderr"):
			warn(e.stderr)
		warn("markdown_to_html: Error executing '%s'" % markdown_to_html_cmd)
		die(e)

def load_tabbed_yaml(path):
	'''
	Load a YAML-like config that uses TAB indentation.
	This function converts leading tabs to 8 spaces per tab, then safe-loads YAML.
	Then it converts lists to tuples recursively.
	'''
	with open(path, 'r', encoding='utf-8') as f:
		text = f.read()

	def _tabs_to_spaces(m):
		return ' ' * 8 * len(m.group(1))
	text = re.sub(r'(^\t+)', _tabs_to_spaces, text, flags=re.MULTILINE)

	data = yaml.safe_load(text)

	def _normalize(obj):
		if isinstance(obj, dict):
			return {k: _normalize(v) for k, v in obj.items()}
		if isinstance(obj, list):
			return tuple(_normalize(x) for x in obj)
		return obj

	return _normalize(data)

