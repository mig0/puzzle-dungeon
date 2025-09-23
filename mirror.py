import pygame
from typing import Union
from cellactor import CellActor
from common import die
from game import game
from constants import MIRROR_INACTIVE_OPACITY, MIRROR_ORIENTATION_CHARS

class Mirror(CellActor):
	def __init__(self, image:Union[str, pygame.Surface]=None, host:CellActor=None, orientation=0, activeness:int=0):
		super().__init__(image)
		self.host = host
		self.orientation = orientation
		self.activeness = activeness
		self.fixed_orientation = False
		self.fixed_activeness = False

	def draw(self, cell=None, opacity=None):
		self.sync_rotation()
		if not self.is_active():
			opacity = MIRROR_INACTIVE_OPACITY * (self.opacity if opacity is None else opacity)
		super().draw(cell, opacity)
		if self.is_active_flip():
			pos = apply_diff(self.pos, (20, -20))
			tip = 'x'
			game.screen.draw.text(tip, center=pos, color="#60C0FF", gcolor="#0080A0", owidth=1.2, ocolor="#404030", alpha=1, fontsize=16)

	@property
	def host(self):
		return self._host

	@host.setter
	def host(self, host:CellActor):
		self._host = host
		host.mirror = self

	@property
	def orientation(self):
		return self._orientation % 4

	@orientation.setter
	def orientation(self, orientation):
		if type(orientation) == str and orientation in MIRROR_ORIENTATION_CHARS:
			orientation = MIRROR_ORIENTATION_CHARS.index(orientation)
		if not (type(orientation) == int and 0 <= orientation <= 7):
			die("Invalid mirror orientation (%s), fix the bug" % str(orientation))
		self._orientation = orientation

	def to_data(self):
		return self.c, self.orientation, self.activeness, self.fixed_orientation, self.fixed_activeness

	def from_data(self, data):
		self.c = data[0]
		self.orientation = data[1]
		self.activeness = data[2]
		self.fixed_orientation = data[3]
		self.fixed_activeness = data[4]

	def reset(self):
		if not self.fixed_orientation:
			self.orientation = 0
		if not self.fixed_activeness:
			self.activeness = 0

	def sync_rotation(self):
		self.angle = self._orientation * (-45)

	def rotate_mirror(self, incr):
		self.orientation = (self._orientation + incr) % 8

	def is_active(self, visited=False):
		return (self.activeness % 2 == 1) ^ (visited and self.is_active_flip())

	def toggle_active(self):
		self.activeness ^= 1

	def is_active_flip(self):
		return self.activeness // 2 == 1

	def toggle_active_flip(self):
		self.activeness ^= 2

