import pygame

class Clipboard():
	SCRAP_UTF8 = "text/plain;charset=utf-8"

	def __init__(self):
		self._initialized = False

	def initialize_if_needed(self):
		if self._initialized:
			return
		pygame.scrap.init()
		self._initialized = True

	def put(self, text):
		self.initialize_if_needed()
		pygame.scrap.put(self.SCRAP_UTF8, text.encode('utf-8'))

	def get(self):
		self.initialize_if_needed()
		data = pygame.scrap.get(self.SCRAP_UTF8)
		return data.decode('utf-8') if data is not None else None

clipboard = Clipboard()
