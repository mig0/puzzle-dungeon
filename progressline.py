"""
Usage (see also tests/progressline):

from progressline import ProgressLine

progress = ProgressLine()
progress.put("Formatting disk started")
progress.put("Verifying disk table")
progress.put("Verifying disk sector integrity")
progress.put("Formatting disk in progress: 10% done")
progress.put("Formatting disk in progress: 100% done")
progress.put("Verifying disk sector integrity")
progress.put("")
print("Disk successfully formatted")
"""

class ProgressLine:
	def __init__(self, is_enabled=True, same_line=True, max_len=None):
		if max_len is None:
			import shutil
			max_len = shutil.get_terminal_size().columns
		self.is_enabled = is_enabled
		self.max_len = max_len
		self.last_progress_line = None
		self.same_line = same_line
		self.endl = "" if same_line else "\n"
		self.ELLIPSES = '…'  # or: ' … '

	def put(self, line=""):
		if not self.is_enabled:
			return
		line_len = len(line)
		if line_len > self.max_len:
			e_len = len(self.ELLIPSES)
			mid = (self.max_len - e_len) // 2
			line = line[0:mid] + self.ELLIPSES + line[line_len - self.max_len + mid + e_len:line_len]

		if self.last_progress_line is not None and self.same_line:
			last_line_len = len(self.last_progress_line)
			remove_len = last_line_len - line_len if last_line_len > line_len else 0
			print("\b \b" * remove_len, end="")
			print("\b" * (last_line_len - remove_len), end="")

		print(line, end=self.endl, flush=True)
		self.last_progress_line = line

