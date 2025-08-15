import os
from filetools import get_dir_names
from config import DATA_DIR

PUZZLE_INFO_DIR = DATA_DIR + "/info/puzzles"

class PuzzleInfo:
	def die(self, error):
		print("PuzzleInfo for %s: %s" % (self.name, error))
		quit()

	def __init__(self, name):
		self.name = name
		self.filename = "%s/%s.txt" % (PUZZLE_INFO_DIR, name)
		if not os.path.isfile(self.filename):
			self.die("No required file %s found" % self.filename)

		file = open(self.filename, "r", encoding="utf-8")

		self.title = file.readline().rstrip("\n")
		if self.title == "\n" or file.readline() != "\n":
			self.die("Invalid format: first line must be title, second line empty")

		self.description = ""
		self.goal = "Unspecified Goal"

		while line := file.readline():
			line = line.strip()
			if line.startswith("Goal:"):
				self.goal = line[5:].strip()
			else:
				self.description += line + "\n"

		# clean up description, trim and leave 2 endlines at most
		self.description = self.description.strip()
		while '\n\n\n' in self.description:
			self.description = self.description.replace("\n\n\n", "\n\n")

		file.close()

	def get_hypertext(self):
		return "### %s\n\n%s\n\nGoal: %s\n\n" % \
			(self.title, self.description, self.goal)

	def get_html(self):
		return '<h1>%s</h1>\n\n<!--VIDEOS-->\n<!--SCREENSHOTS-->\n<p>%s\n</p>\n\n<p class="goal">%s</p>' % \
			(self.title, "\n</p>\n\n<p>".join(self.description.split("\n\n")), self.goal)

def get_all_puzzle_infos():
	all_names = get_dir_names(PUZZLE_INFO_DIR, ".txt")
	return (PuzzleInfo(name) for name in all_names)
