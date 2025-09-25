from constants import DEFAULT_DEBUG_LVL

# features
DBG_SOLV = "solv"
DBG_PATH = "path"

class Debug:
	def __init__(self):
		self.lvl = DEFAULT_DEBUG_LVL
		self.features = set()

	def enable_feature(self, feature):
		self.features.add(feature)

	def configure(self, args):
		for item in args:
			try:
				self.lvl = int(item)
			except ValueError:
				self.enable_feature(item)

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
			print("%s%s" % (" " * depth if depth else "", msg))

debug = Debug()
