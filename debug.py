from constants import DEFAULT_DEBUG_LVL
from common import warn, get_current_time_str
from colorize import colorize_auto

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
		self._set_has_any()

	def _set_has_any(self):
		self.has_any = self.lvl > 0 or self.features

	def enable(self, feature):
		self.features.add(feature)

	def has(self, feature):
		return feature in self.features

	def configure(self, args):
		for item in args:
			if isinstance(item, int):
				item = str(item)
			if type(item) != str:
				warn("Ignoring non string item (%s) in configure" % str(item))
				continue
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
		self._set_has_any()

	def __call__(self, *args):
		if not self.has_any:
			return
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
					" " * depth if depth else "", colorize_auto(msg)))

debug = Debug()
