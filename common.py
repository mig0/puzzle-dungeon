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

