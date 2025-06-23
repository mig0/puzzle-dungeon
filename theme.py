import os
import pygame
from debug import debug
from common import die
from constants import DEFAULT_IMAGE_PREFIX, IMAGES_DIR_PREFIX
from cellactor import CellActor, create_actor

theme_prefix = None

def set_theme_name(theme_name):
	global theme_prefix
	theme_prefix = theme_name + '/'

def load_theme_cell_image(image_name):
	return pygame.image.load(IMAGES_DIR_PREFIX + get_theme_image_name(image_name) + '.png').convert_alpha()

def get_theme_image_name(image_name):
	for full_image_name in (theme_prefix + image_name, DEFAULT_IMAGE_PREFIX + image_name):
		if os.path.isfile(IMAGES_DIR_PREFIX + full_image_name + '.png'):
			debug(2, "Found image %s" % full_image_name)
			return full_image_name

	die("Unable to find image %s in neither %s nor %s" % (image_name, theme_prefix, DEFAULT_IMAGE_PREFIX))

def load_actor_theme_image(actor, name):
	actor.image = get_theme_image_name(name)

def reload_actor_theme_image(actor):
	if actor.image:
		load_actor_theme_image(actor, os.path.basename(actor.image))

def create_theme_image(image_name):
	return CellActor(get_theme_image_name(image_name))

def create_theme_actor(image_name, cell):
	return create_actor(get_theme_image_name(image_name), cell)

