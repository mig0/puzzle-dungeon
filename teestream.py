import sys
import contextlib

class TeeStream:
	def __init__(self, *streams):
		self.streams = streams

	def write(self, data):
		for s in self.streams:
			s.write(data)

	def flush(self):
		for s in self.streams:
			s.flush()

@contextlib.contextmanager
def stdout_redirected_to(*streams):
	original = sys.stdout
	sys.stdout = TeeStream(*streams)
	try:
		yield
	finally:
		sys.stdout = original

