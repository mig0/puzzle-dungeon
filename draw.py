import pygame
from translate import _
from game import game
from cellactor import apply_diff
from sizetools import import_size_constants

def draw_central_flash(full=False, color=(0, 40, 40)):
	surface = pygame.Surface((MAP_W, MAP_H if full else 120))
	surface.set_alpha(50)
	surface.fill(color)
	game.screen.blit(surface, (0, POS_CENTER_Y - surface.get_height() / 2))

def draw_actor_hint(actor, hint, pos_diff, colors):
	game.screen.draw.text(str(hint), center=apply_diff(actor.pos, pos_diff), color=colors[0], gcolor=colors[1], owidth=1.2, ocolor=colors[2], alpha=0.8, fontsize=24)

# this function is intended to be called outside of draw(), so need display.flip
def draw_long_level_generation():
	game.screen.fill("#a8b6b7")
	game.screen.draw.text(_("Initializing level…"), center=(POS_CENTER_X, POS_CENTER_Y), color='#FFFFFF', gcolor="#88AA66", owidth=1.2, ocolor="#404030", alpha=1, fontsize=80)
	pygame.display.flip()

def draw_apply_sizes():
	import_size_constants()
