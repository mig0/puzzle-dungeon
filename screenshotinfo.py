import os
import re
from filetools import get_dir_names
from config import DATA_DIR

SCREENSHOTS_SUBDIR   = "screenshots"
HTML_SCREENSHOTS_DIR = DATA_DIR + "/html/" + SCREENSHOTS_SUBDIR
INFO_SCREENSHOTS_DIR = DATA_DIR + "/info/" + SCREENSHOTS_SUBDIR

FILE_EXT = '.webp'
HTML_EXT = '.html'
INFO_EXT = '.txt'

class ScreenshotInfo:
	def __init__(self, name):
		self.name = name
		self.filename      = "%s/%s%s" % (HTML_SCREENSHOTS_DIR, name, FILE_EXT)
		self.info_filename = "%s/%s%s" % (INFO_SCREENSHOTS_DIR, name, INFO_EXT)
		self.img_filename  = "%s/%s%s" % (SCREENSHOTS_SUBDIR,   name, FILE_EXT)
		self.html_filename = "%s/%s%s" % (SCREENSHOTS_SUBDIR,   name, HTML_EXT)
		self.puzzle = None
		self.theme = None
		self.title = "Unknown Title"
		self.description = ""
		self.main_idx = None
		self.is_front = False

		if not os.path.isfile(self.info_filename):
			print("WARNING: No required file %s found" % self.info_filename)
			return

		file = open(self.info_filename, "r")

		is_header = True

		while line := file.readline():
			line = line.strip()
			if not is_header:
				self.description += line + '\n'
			elif line == "":
				is_header = False
			elif line.startswith("Puzzle: "):
				self.puzzle = line[8:]
			elif line.startswith("Theme: "):
				self.theme = line[7:]
			elif line.startswith("Title: "):
				self.title = line[7:]
			elif line.startswith("Main: "):
				value = line[6:].strip().lower()
				self.main_idx = int(value) if value.isdigit() else 10 if value == "true" else None
			elif line.startswith("Front: "):
				value = line[7:].strip().lower()
				self.is_front = value != "false" and value != "0"
			else:
				print("%s: Invalid line: [%s]\n\tIgnoring this line" % (self.info_filename, line))
				continue

		# clean up description, trim and leave 2 endlines at most
		self.description = self.description.strip()
		self.description = re.sub("\n{3,}", "\n\n", self.description)

		file.close()

	def get_hypertext(self):
		return "## %s\n\nFilename: %s\n\nPuzzle: %s\n\nTheme: %s\n\n%s\n" % (self.title, self.filename, self.puzzle, self.theme, self.description)

	def get_html(self):
		extra_html = ''
		if self.puzzle:
			extra_html += '<p class="screenshot-property"><b>Puzzle</b>: <a href="puzzles/%s.html">%s</a></p>\n' % (self.puzzle, self.puzzle)
		if self.theme:
			extra_html += '<p class="screenshot-property"><b>Theme</b>: <a href="themes/%s.html">%s</a></p>\n' % (self.theme, self.theme)

		description_html = "\n</p>\n\n<p>".join(self.description.split("\n\n"))
		description_html = re.sub(r'\[(.*)\]\((.*)\)', r'<a href="%s/\2.html">\1</a>' % SCREENSHOTS_SUBDIR, description_html)

		return '<h1>%s</h1>\n\n%s<p>\n%s\n</p>\n<div class="screenshot-image"><img class="screenshot-img" src="%s"></div>\n' % (
			self.title, extra_html, description_html, self.img_filename)

	def get_html_for_index(self):
		return '<div class="screenshot"><div class="screenshot-title">%s</div><a href="%s"><img src="%s"></a></div>' % (
			self.title, self.html_filename, self.img_filename)

def get_all_screenshot_infos():
	all_names = get_dir_names(HTML_SCREENSHOTS_DIR, FILE_EXT)
	return tuple(ScreenshotInfo(name) for name in all_names)

def get_all_puzzle_screenshot_infos(puzzle):
	return tuple(info for info in get_all_screenshot_infos() if info.puzzle == puzzle)

def get_all_theme_screenshot_infos(theme):
	return tuple(info for info in get_all_screenshot_infos() if info.theme == theme)

def get_main_screenshot_infos():
	return sorted((info for info in get_all_screenshot_infos() if info.main_idx is not None), key=lambda info: info.main_idx)

def get_front_puzzle_screenshot_info(puzzle):
	infos = get_all_puzzle_screenshot_infos(puzzle)
	return sorted(infos, key=lambda info: 0 if info.is_front else info.main_idx or 1000)[0] if infos else None

def get_css_class_for_screenshots(objs):
	n = len(objs)
	return "screenshots-%d-per-row" % max(5, min(2, n))
