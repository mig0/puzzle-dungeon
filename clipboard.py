import os
import pygame

class Clipboard():
	SCRAP_TEXT = "text/plain" if os.environ.get('OS') == 'Windows_NT' else "text/plain;charset=utf-8"

	def __init__(self):
		self._initialized = False

	def initialize_if_needed(self):
		if self._initialized:
			return
		if not pygame.display.get_init():
			# bogus init for non-GUI to make the first clipboard operation work
			pygame.display.set_mode((1, 1))
			pygame.time.Clock().tick(40)
			pygame.event.get()
		pygame.scrap.init()
		self._initialized = True

	def put(self, text):
		self.initialize_if_needed()
		pygame.scrap.put(self.SCRAP_TEXT, text.encode('utf-8'))

	def get(self):
		self.initialize_if_needed()
		data = pygame.scrap.get(self.SCRAP_TEXT)
		return data.decode('utf-8') if data is not None else None

clipboard = Clipboard()
