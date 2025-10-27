import sys
from common import warn

try:
	import cProfile
	import pstats
	from io import StringIO
	_HAS_PROFILER = True
except ImportError:
	_HAS_PROFILER = False

class Profiler:
	def __init__(self):
		self._profiler = None

	def start(self):
		if not _HAS_PROFILER or self._profiler:
			return
		self._profiler = cProfile.Profile()
		self._profiler.enable()

	# sort_by: "pcalls", "calls"/"ncalls", "time"/"tottime", "cumtime"/"cumulative", "filename"/"module", "line", "name", "nfl", "stdname"
	def stop(self, sort_by='time', num_lines=40, filename=None):
		if not _HAS_PROFILER or not self._profiler:
			return
		self._profiler.disable()
		stream = StringIO()
		pstats.Stats(self._profiler, stream=stream).strip_dirs().sort_stats(sort_by).print_stats(num_lines)  #.print_callers()
		output = stream.getvalue()
		if filename:
			try:
				with open(filename, 'w') as file:
					file.write(output)
			except Exception as e:
				warn("Profiler: cannot write to %s: %s" % (filename, e))
		else:
			print(output)
		self._profiler = None
		self._output = None

	def toggle(self):
		if self.is_active():
			self.stop()
		else:
			self.start()

	def is_active(self):
		return bool(self._profiler)

profiler = Profiler()

# run any module under profiler
if __name__ == '__main__':
	import runpy
	if len(sys.argv) < 2:
		print("Usage: python profiler.py <module_or_script> [args...]")
		sys.exit(1)
	profiler.start()
	runpy.run_path(sys.argv[1], run_name='__main__')
	profiler.stop()
