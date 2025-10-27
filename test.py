import inspect

class TestSuite:
	def __init__(self, name, assert_on_fail=False, verbose_on_pass=False):
		self.reset()
		self.name = name
		self.last_function = None
		self.assert_on_fail = assert_on_fail
		self.verbose_on_pass = verbose_on_pass

	def reset(self):
		self.num_total = 0
		self.num_passed = 0

	def print_function_once(self):
		function = inspect.stack()[-2].function
		if function != self.last_function:
			print("# %s" % function)
			self.last_function = function

	def ok(self, is_passed, error):
		if self.verbose_on_pass:
			self.print_function_once()
		self.num_total += 1
		if is_passed:
			self.num_passed += 1
			if self.verbose_on_pass:
				print("%d - PASS" % (self.num_total))
		else:
			if not self.verbose_on_pass:
				self.print_function_once()
			print("%d - FAIL: %s" % (self.num_total, error))
			if self.assert_on_fail:
				assert False, error

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
		self.ok(elem in mapping, "Elem %s not is in %s, unexpected" % (str(elem), type(mapping).__name__))

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
			print("All %d %s tests passed" % (self.num_total, self.name))
		else:
			print("Only %d of %d %s tests passed" % (self.num_passed, self.num_total, self.name))
		self.reset()
