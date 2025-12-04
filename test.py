import contextlib
import inspect
import sys
import io
from profiler import profiler
from colorize import *

@contextlib.contextmanager
def suppress_output():
	_saved_out = sys.stdout
	_saved_err = sys.stderr
	sys.stdout = io.StringIO()
	sys.stderr = io.StringIO()
	try:
		yield
	finally:
		sys.stdout = _saved_out
		sys.stderr = _saved_err

class TestSuite:
	def __init__(self, name, assert_on_fail=None, verbose_on_pass=None, run_profiler=None, show_code=None):
		# default to the command line flags, but keep explicit values
		args = sys.argv[1:]

		self.reset()
		self.name = name
		self.last_function = None
		self.assert_on_fail  = '-a' in args if assert_on_fail  is None else assert_on_fail
		self.verbose_on_pass = '-v' in args if verbose_on_pass is None else verbose_on_pass
		self.run_profiler    = '-p' in args if run_profiler    is None else run_profiler
		self.show_code       = '-c' in args if show_code       is None else show_code
		if self.run_profiler:
			profiler.start()

	def reset(self):
		self.num_total = 0
		self.num_passed = 0

	def print_function_once(self):
		function = inspect.stack()[-2].function
		if function != self.last_function:
			print("# %s" % colorize(function, COLOR_CYAN))
			self.last_function = function

	def print_cond_code_str(self):
		if not self.show_code:
			return
		print("→ %s" % colorize(self._extract_cond_code_str(1), COLOR_DIM))

	def ok(self, cond, error=None, negate=False):
		if self.verbose_on_pass:
			self.print_function_once()

		self.num_total += 1
		if error is None:
			error = self._extract_cond_code_str()
		if callable(cond):
			cond, error = self._call(cond, error)

		if negate:
			cond = not cond

		if cond:
			self.num_passed += 1
			if self.verbose_on_pass:
				self.print_cond_code_str()
				print("%d - %s" % (self.num_total, colorize("PASS", COLOR_GREEN)))
		else:
			if not self.verbose_on_pass:
				self.print_function_once()
			self.print_cond_code_str()
			print("%d - %s: %s" % (self.num_total, colorize("FAIL", COLOR_RED), error))
			if self.assert_on_fail:
				assert False, error

	def catch(self, cond, descr=None):
		if descr is None:
			descr = self._extract_cond_code_str()
		_, exc_str = self._call(cond)
		self.ok(exc_str, "Expected to catch exception in: %s" % descr)

	def no_catch(self, cond, descr=None):
		if descr is None:
			descr = self._extract_cond_code_str()
		_, exc_str = self._call(cond)
		self.ok(not exc_str, "Unexpected %s was caught in: %s" % (exc_str, descr))

	def eq(self, value1, value2):
		self.ok(value1 == value2, "Got %s, but expected %s" % (str(value1), str(value2)))

	def ne(self, value1, value2):
		self.ok(value1 != value2, "Expected %s to be different" % str(value1))

	def gt(self, value1, value2):
		self.ok(value1 > value2, "Expected %s to be greater than %s" % (str(value1), str(value2)))

	def lt(self, value1, value2):
		self.ok(value1 < value2, "Expected %s to be lesser than %s" % (str(value1), str(value2)))

	def ge(self, value1, value2):
		self.ok(value1 >= value2, "Expected %s to be greater-equal than %s" % (str(value1), str(value2)))

	def le(self, value1, value2):
		self.ok(value1 <= value2, "Expected %s to be lesser-equal than %s" % (str(value1), str(value2)))

	def is_cell(self, cell):
		self.ok(type(cell) == tuple and len(cell) == 2 and all(type(i) == int for i in cell), "Got %s, but expected cell" % str(cell))

	def is_in(self, elem, mapping):
		self.ok(elem in mapping, "Elem %s is not in %s, unexpected" % (str(elem), type(mapping).__name__))

	def not_in(self, elem, mapping):
		self.ok(elem not in mapping, "Elem %s is in %s, unexpected" % (str(elem), type(mapping).__name__))

	def is_instance(self, item, type0):
		self.ok(isinstance(item, type0), "Item %s is not instance of %s, unexpected" % (str(item), type0.__name__))

	def not_instance(self, item, type0):
		self.ok(not isinstance(item, type0), "Item %s is instance of %s, unexpected" % (str(item), type0.__name__))

	def has_attr(self, obj, name):
		self.ok(hasattr(obj, name), "Object %s has no attr '%s', unexpected" % (str(obj), name))

	def no_attr(self, obj, name):
		self.ok(not hasattr(obj, name), "Object %s has attr '%s', unexpected" % (str(obj), name))

	def len(self, collection, l):
		if hasattr(collection, '__len__'):
			self.ok(len(collection) == l, "Collection len is %d, but expected %d" % (len(collection), l))
		else:
			self.ok(False, "No collection %s, but expected len %d", (str(collection), l))

	def none(self, value):
		self.ok(value is None, "Expected None value")

	def not_none(self, value):
		self.ok(value is not None, "Expected non None value")

	def finalize(self):
		if self.num_total == self.num_passed:
			print("All %s %s tests passed" % (colorize(self.num_total, COLOR_GREEN), self.name))
		else:
			print("Only %s of %d %s tests passed" % (colorize(self.num_passed, COLOR_YELLOW if self.num_passed else COLOR_RED), self.num_total, self.name))
		self.reset()
		if self.run_profiler:
			profiler.stop()

	def _call(self, callable_cond, error=""):
		assert callable(callable_cond)
		exc_str = None
		cond = None
		with suppress_output():
			try:
				cond = callable_cond()
			except SystemExit as e:
				cond = False
				exc_str = "SystemExit"
			except Exception as e:
				cond = False
				exc_str = f"{e.__class__.__name__} '{e}'"
		if error and exc_str:
			error = f"{error}; also {exc_str} is thrown"
		return cond, error or exc_str

	def _extract_cond_code_str(self, n_extra_frames=0):
		frame = inspect.currentframe().f_back.f_back
		for _ in range(n_extra_frames):
			frame = frame.f_back
		filename = frame.f_code.co_filename
		lineno = frame.f_lineno

		code_str = "Condition in file %s line %d" % (filename, lineno)
		try:
			import linecache
			line = linecache.getline(filename, lineno).strip()
			# expect something like: test.ok(something), match parentheses
			idx = line.find('(')
			if idx >= 0:
				code_str = line[idx + len('('):]
				par, end = 1, 0
				for i, ch in enumerate(code_str):
					if ch == '(':
						par += 1
					elif ch == ')':
						par -= 1
						if par == 0:
							end = i
							break
				code_str = code_str[:end].strip()
		except Exception:
			pass
		return code_str
