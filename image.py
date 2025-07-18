import pygame
import pgzero
from constants import DATA_DIR
from sizetools import CELL_W, CELL_H
from cellactor import *

__all__ = [
	'load_image',
	'colorize_cell_image',
	'create_cell_subimage',
	'create_text_cell_image',
]

def load_image(image_name, size, do_crop=False):
	image = pygame.image.load(DATA_DIR + '/' + image_name).convert_alpha()
	if do_crop:
		# image=300x400 size=100x200 -> cropped=200x400
		# image=300x400 size=200x100 -> cropped=300x150
		w = image.get_width()
		h = image.get_height()
		if w * size[1] > h * size[0]:
			crop_w = size[0] * h // size[1]
			crop_h = h
			crop_x = (w - crop_w) // 2
			crop_y = 0
		else:
			crop_w = w
			crop_h = size[1] * w // size[0]
			crop_x = 0
			crop_y = (h - crop_h) // 2
		cropped_image = pygame.Surface((crop_w, crop_h), pygame.SRCALPHA, 32)
		cropped_image.blit(image, (-crop_x, -crop_y))
		image = cropped_image
	return pygame.transform.scale(image, size)

def colorize_cell_image(image, color, alpha=1):
	cell_surface = pygame.Surface((CELL_W, CELL_H), pygame.SRCALPHA, 32)
	cell_surface.fill((*color, alpha * 255))
	cell_surface.blit(image, (0, 0))
	return cell_surface

def create_cell_subimage(image, cell=(0, 0), starting_cell=(0, 0), area=None, rotate_angle=0):
	cell_surface = pygame.Surface((CELL_W, CELL_H), pygame.SRCALPHA, 32)
	cell = apply_diff(cell, starting_cell, subtract=True)
	cell_surface.blit(image, (-cell[0] * CELL_W, -cell[1] * CELL_H), area)
	if rotate_angle != 0:
		cell_surface = pygame.transform.rotate(cell_surface, rotate_angle)
	return cell_surface

def create_text_cell_image(text, color='#E0E0E0', gcolor="#408080", owidth=1.2, ocolor="#004040", alpha=1, fontsize=48):
	cell_surface = pygame.Surface((CELL_W, CELL_H), pygame.SRCALPHA, 32)
	pgzero.ptext.draw(text, surf=cell_surface, center=cell_to_pos((0, 0)), color=color, gcolor=gcolor, owidth=owidth, ocolor=ocolor, alpha=alpha, fontsize=fontsize)
	return cell_surface

