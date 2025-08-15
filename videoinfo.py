import os
import re
from filetools import get_dir_names
from common import markdown_to_html
from config import DATA_DIR

VIDEOS_SUBDIR   = "videos"
HTML_VIDEOS_DIR = DATA_DIR + "/html/" + VIDEOS_SUBDIR
INFO_VIDEOS_DIR = DATA_DIR + "/info/" + VIDEOS_SUBDIR

FILE_EXT = '.webm'
HTML_EXT = '.html'
INFO_EXT = '.txt'

class VideoInfo:
	def __init__(self, name):
		self.name = name
		self.filename      = "%s/%s%s" % (HTML_VIDEOS_DIR, name, FILE_EXT)
		self.info_filename = "%s/%s%s" % (INFO_VIDEOS_DIR, name, INFO_EXT)
		self.vid_filename  = "%s/%s%s" % (VIDEOS_SUBDIR,   name, FILE_EXT)
		self.html_filename = "%s/%s%s" % (VIDEOS_SUBDIR,   name, HTML_EXT)
		self.puzzles = []
		self.themes = []
		self.title = "Unknown Title"
		self.description = ""
		self.main_idx = None
		self.is_front = False

		if not os.path.isfile(self.info_filename):
			print("WARNING: No required file %s found" % self.info_filename)
			return

		file = open(self.info_filename, "r", encoding="utf-8")

		is_header = True

		while line := file.readline():
			line = line.strip()
			if not is_header:
				self.description += line + '\n'
			elif line == "":
				is_header = False
			elif line.startswith("Puzzles: "):
				self.puzzles = (line[9:].replace(',', ' ')).split()
			elif line.startswith("Themes: "):
				self.themes = (line[8:].replace(',', ' ')).split()
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
		return "## %s\n\nFilename: %s\n\nPuzzles: %s\n\nThemes: %s\n\n%s\n" % (
			self.title, self.filename, ", ".join(self.puzzles), ", ".join(self.themes), self.description)

	def get_html(self):
		extra_html = ''
		if self.puzzles:
			puzzle_link_htmls = ['<a href="puzzles/%s.html">%s</a>' % (puzzle, puzzle) for puzzle in self.puzzles]
			extra_html += '<p class="media-property"><b>Puzzles</b>: %s</p>\n' % ", ".join(puzzle_link_htmls)
		if self.themes:
			theme_link_htmls = ['<a href="themes/%s.html">%s</a>' % (theme, theme) for theme in self.themes]
			extra_html += '<p class="media-property"><b>Themes</b>: %s</p>\n' % ", ".join(theme_link_htmls)

		description_html = markdown_to_html(self.description)
		description_html = re.sub(r'(<a href=")([^/.]+)(")', r'\1%s/\2.html\3' % VIDEOS_SUBDIR, description_html)

		return '<h1>%s</h1>\n\n%s\n%s\n<div class="media-container"><video class="media" controls><source src="%s"></video></div>\n' % (
			self.title, extra_html, description_html, self.vid_filename)

	def get_html_for_index(self):
		return '<div class="media"><div class="media-title">%s</div><a href="%s"><video><source src="%s"></video></a></div>' % (
			self.title, self.html_filename, self.vid_filename)

def get_all_video_infos():
	all_names = get_dir_names(HTML_VIDEOS_DIR, FILE_EXT)
	return tuple(VideoInfo(name) for name in all_names)

def get_all_puzzle_video_infos(puzzle):
	return tuple(info for info in get_all_video_infos() if puzzle in info.puzzles)

def get_all_theme_video_infos(theme):
	return tuple(info for info in get_all_video_infos() if theme in info.themes)

def get_main_video_infos():
	return sorted((info for info in get_all_video_infos() if info.main_idx is not None), key=lambda info: info.main_idx)

def get_front_puzzle_video_info(puzzle):
	infos = get_all_puzzle_video_infos(puzzle)
	return sorted(infos, key=lambda info: 0 if info.is_front else info.main_idx or 1000)[0] if infos else None
