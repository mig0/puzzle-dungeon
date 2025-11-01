from constants import DEFAULT_DEBUG_LVL
from common import warn, get_current_time_str

# features
DBG_SOLV  = "solv"
DBG_SOLV2 = "solv+"
DBG_SOLV3 = "solv++"

class Debug:
	def __init__(self):
		self.lvl = DEFAULT_DEBUG_LVL
		self.show_time = False
		self.time_digits = 3
		self.features = set()

	def enable(self, feature):
		self.features.add(feature)

	def has(self, feature):
		return feature in self.features

	def configure(self, args):
		for item in args:
			if item.startswith("time"):
				if len(item) == 4:
					self.show_time = True
				elif item[4] == '=' and item[5:].isdigit():
					self.show_time = True
					self.time_digits = int(item[5:])
				else:
					warn("Ignoring unsupported format for debug configure item '%s'" % item)
				continue
			try:
				self.lvl = int(item)
			except ValueError:
				self.enable(item)
				while item.endswith('+'):
					item = item[0:-1]
					self.enable(item)

	def __call__(self, *args):
		# optimize common case
		if len(args) >= 2 and isinstance(args[0], int) and self.lvl < args[0]:
			return

		*selectors, msg = args

		lvl = 0
		depth = None
		features = []

		# find level (int), depth (list of 1 int) and features (strings)
		for sel in selectors:
			if isinstance(sel, int) and sel >= 0:
				lvl = sel
			elif isinstance(sel, list) and len(sel) == 1 and isinstance(sel[0], int):
				depth = sel[0]
			elif isinstance(sel, str):
				features.append(sel)
			else:
				raise TypeError("debug selector must be int, list(int) or str")

		# check conditions
		if (lvl <= self.lvl) and (not features or self.features.intersection(features)):
			if callable(msg):
				msg = msg()  # evaluate lazily
			if isinstance(msg, dict):
				msg = ["%s=%s" % (k, v) for k, v in msg.items()]
			for msg in msg if isinstance(msg, (list, tuple)) else [msg]:
				print("%s%s%s" % (
					"[%s] " % get_current_time_str(self.time_digits) if self.show_time else "",
					" " * depth if depth else "", msg))

class ProgressLine:
	def __init__(self, is_enabled=True, max_len=80):
		self.is_progress_line_enabled = is_enabled
		self.max_progress_line_len = max_len
		self.last_progress_line = None

	def put(self, line=""):
		if not self.is_progress_line_enabled:
			return
		line_len = len(line)
		if line_len > self.max_progress_line_len:
			mid = self.max_progress_line_len // 2 - 2
			line = line[0:mid] + ' … ' + line[line_len - self.max_progress_line_len + mid + 3:line_len]

		if self.last_progress_line is not None:
			last_line_len = len(self.last_progress_line)
			remove_len = last_line_len - line_len if last_line_len > line_len else 0
			print("\b \b" * remove_len, end="")
			print("\b" * (last_line_len - remove_len), end="")

		print(line, end="", flush=True)
		self.last_progress_line = line

debug = Debug()
