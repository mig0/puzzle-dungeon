import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

class Clipboard():
	SCRAP_TEXT = "text/plain" if os.environ.get('OS') == 'Windows_NT' else "text/plain;charset=utf-8"

	def __init__(self):
		self._initialized = False
		self._persistent = True

	def initialize_if_needed(self):
		if self._initialized:
			return
		if not pygame.display.get_init():
			# bogus init for non-GUI to make the clipboard operation work
			pygame.display.set_mode((1, 1))
			pygame.time.Clock().tick(40)
			pygame.event.get()
			self._persistent = False
		pygame.scrap.init()
		self._initialized = True

	def deinitialize_if_needed(self):
		if self._persistent:
			return
		pygame.display.quit()
		self.__init__()

	def put(self, text):
		self.initialize_if_needed()
		pygame.scrap.put(self.SCRAP_TEXT, text.encode('utf-8'))
		self.deinitialize_if_needed()

	def get(self):
		self.initialize_if_needed()
		data = pygame.scrap.get(self.SCRAP_TEXT)
		self.deinitialize_if_needed()
		return data.decode('utf-8') if data is not None else None

clipboard = Clipboard()
