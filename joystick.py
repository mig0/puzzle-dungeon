from debug import debug
import pygame
from pgzero.constants import keys

DBG_JREG = "jreg"
DBG_JPRS = "jprs"

class HidPlaystationConfig:
	# PS4: Sony Interactive Entertainment Wireless Controller
	# PS5: Sony Interactive Entertainment DualSense Wireless Controller

	BUTTON_NAMES = {
		0:  'ACTIVATE',
		1:  'CANCEL',
		2:  'INTERACT',
		3:  'SELECT',
		4:  'LSHIFT',
		5:  'RSHIFT',
		6:  'LCTRL',
		7:  'RCTRL',
		8:  'SHARE',
		9:  'OPTIONS',
		10: 'SYSTEM',
		11:  None,
		12:  None,
	}

	MODIFIER_BUTTONS = {
		'LSHIFT': 4,
		'RSHIFT': 5,
	}

	MODIFIER_AXES = {
		'LCTRL': 2,
		'RCTRL': 5,
	}

	# these are used for motion unless modifier is pressed
	BUTTON_NAMES_REQUIRING_MODIFIER = [
		'PLAY',
		'STOP',
		'PREV',
		'NEXT',
	]

	STICK_AXES = {
		'LEFT_X':  0,
		'LEFT_Y':  1,
		'RIGHT_X': 2,
		'RIGHT_Y': 3,
	}

	HAT_STICKS = {
	#	'LEFT_X':  [0, 0, 1],
	#	'LEFT_Y':  [0, 1, -1],
	}

	HAT_BUTTONS = {
		'PREV': [0, 0, -1],
		'PLAY': [0, 1, 1],
		'NEXT': [0, 0, 1],
		'STOP': [0, 1, -1],
	}

	MODIFIER_AXIS_SENSITIVITY = 0.2
	STICK_AXIS_SENSITIVITY = 0.5

	@classmethod
	def is_detected(cls, joystick):
		return joystick.get_numaxes() == 6 and joystick.get_numballs() == 0 and joystick.get_numbuttons() == 13 and joystick.get_numhats() == 1

class NohidPlaystationConfig(HidPlaystationConfig):
	BUTTON_NAMES = {
		0:  'SELECT',
		1:  'ACTIVATE',
		2:  'CANCEL',
		3:  'INTERACT',
		4:  'LSHIFT',
		5:  'RSHIFT',
		6:  'LCTRL',
		7:  'RCTRL',
		8:  'SHARE',
		9:  'OPTIONS',
		10:  None,
		11:  None,
		12: 'SYSTEM',
		13:  None,  # 'PAD', then 'MIC' on PS5
	}

	MODIFIER_AXES = {
		'LCTRL': 3,
		'RCTRL': 4,
	}

	@classmethod
	def is_detected(cls, joystick):
		return joystick.get_numaxes() == 6 and joystick.get_numballs() == 0 and joystick.get_numbuttons() in (14, 15) and joystick.get_numhats() == 1

class OldPlaystationConfig(HidPlaystationConfig):
	BUTTON_NAMES = {
		0:  'ACTIVATE',
		1:  'CANCEL',
		2:  'INTERACT',
		3:  'SELECT',
		4:  'SHARE',
		5:  'SYSTEM',
		6:  'OPTIONS',
		7:  None,
		8:  None,
		9:  'LSHIFT',
		10: 'RSHIFT',
		11: 'PLAY',
		12: 'STOP',
		13: 'PREV',
		14: 'NEXT',
	}

	MODIFIER_BUTTONS = {
		'LSHIFT': 9,
		'RSHIFT': 10,
	}

	MODIFIER_AXES = {
		'LCTRL': 4,
		'RCTRL': 5,
	}

	HAT_STICKS = {
	}

	HAT_BUTTONS = {
	}

	@classmethod
	def is_detected(cls, joystick):
		return joystick.get_numaxes() == 6 and joystick.get_numballs() == 0 and joystick.get_numbuttons() in (14, 15) and joystick.get_numhats() == 0

SUPPORTED_JOYSTICK_CONFIGS = (
	HidPlaystationConfig,
	NohidPlaystationConfig,
	OldPlaystationConfig,
)

joysticks = []

class Joystick():
	def __init__(self, joystick, config):
		self.joystick = joystick
		self.config = config

		names = list(self.config.BUTTON_NAMES.values()) + [*self.config.MODIFIER_AXES, *self.config.STICK_AXES, *self.config.HAT_STICKS, *self.config.HAT_BUTTONS]
		self.is_pressed = dict((name, False) for name in names)
		self.hidden_press = dict((button_name, False) for button_name in self.config.BUTTON_NAMES_REQUIRING_MODIFIER)

	@classmethod
	def find(cls, joystick):
		for j in joysticks:
			if j.joystick == joystick:
				return j
		return None

	@classmethod
	def register(cls, joystick):
		if cls.find(joystick) is not None:
			return
		config = next((config for config in SUPPORTED_JOYSTICK_CONFIGS if config.is_detected(joystick)), None)
		if not config:
			debug(DBG_JREG, "Unsupported joystick: %s" % joystick.get_name())
			return
		debug(DBG_JREG, "Registered joystick: %s, %s" % (joystick.get_name(), config.__name__))
		joystick.init()
		joystick = Joystick(joystick, config)
		joysticks.append(joystick)

	@classmethod
	def unregister(cls, joystick):
		debug(DBG_JREG, "Unregistered joystick: %s" % joystick.get_name())
		joystick.quit()
		joystick = Joystick.find(joystick)
		if joystick is not None:
			joysticks.remove(joystick)

	def _is_button_pressed(self, button):
		return self.joystick.get_button(button)

	def _is_modifier_axis_pressed(self, axis):
		return self.joystick.get_axis(axis) > -1 + self.config.MODIFIER_AXIS_SENSITIVITY

	def _is_stick_axis_pressed(self, axis):
		value = self.joystick.get_axis(axis)
		return 1 if value > +self.config.STICK_AXIS_SENSITIVITY else -1 if value < -self.config.STICK_AXIS_SENSITIVITY else False

	def _is_hat_xy_stick_pressed(self, hat, xy, factor):
		value = self.joystick.get_hat(hat)[xy]
		return value * factor if value else False

	def _is_hat_xy_button_pressed(self, hat, xy, value0):
		value = self.joystick.get_hat(hat)[xy]
		return value == value0

	def capture_pressed_state(self):
		self.old_is_pressed = self.is_pressed.copy()
		for button, button_name in self.config.BUTTON_NAMES.items():
			self.is_pressed[button_name] = self._is_button_pressed(button)
		for modifier, axis in self.config.MODIFIER_AXES.items():
			self.is_pressed[modifier] = self._is_modifier_axis_pressed(axis)
		for stick, axis in self.config.STICK_AXES.items():
			self.is_pressed[stick] = self._is_stick_axis_pressed(axis)
		for stick, hat_info in self.config.HAT_STICKS.items():
			self.is_pressed[stick] = self._is_hat_xy_stick_pressed(*hat_info)
		for button_name, hat_info in self.config.HAT_BUTTONS.items():
			self.is_pressed[button_name] = self._is_hat_xy_button_pressed(*hat_info)

	def is_any_modifier_pressed(self, modifiers=('LCTRL', 'RCTRL', 'LSHIFT', 'RSHIFT')):
		for name in modifiers:
			if self.is_pressed[name]:
				return True
		return False

	def was_pressed(self, name):
		return not self.old_is_pressed[name] and self.is_pressed[name]

	def was_released(self, name):
		return self.old_is_pressed[name] and not self.is_pressed[name]

	def when_stick_pressed(self, stick, ret1, ret2):
		if self.is_pressed[stick] == False:
			return None
		return ret1 if self.is_pressed[stick] == -1 else ret2

def scan_active_joysticks():
	dead_joysticks = [ j.joystick for j in joysticks ]
	for i in range(pygame.joystick.get_count()):
		joystick = pygame.joystick.Joystick(i)
		Joystick.register(joystick)
		if joystick in dead_joysticks:
			dead_joysticks.remove(joystick)

	for joystick in dead_joysticks:
		Joystick.unregister(joystick)

def scan_joysticks_and_state():
	scan_active_joysticks()

	for joystick in joysticks:
		joystick.capture_pressed_state()

PRESSED_NAME_KEYS = {
	'ACTIVATE': keys.SPACE,
	'CANCEL':   keys.ESCAPE,
	'INTERACT': keys.RETURN,
	'SELECT':   keys.M,
	'LSHIFT':   keys.LSHIFT,
	'RSHIFT':   keys.RSHIFT,
	'PREV':     keys.P,
	'NEXT':     keys.N,
	'PLAY':     keys.R,
	'STOP':     keys.Q,
	'LCTRL':    keys.LCTRL,
	'RCTRL':    keys.RCTRL,
	'SHARE':    None,
	'OPTIONS':  None,
	'SYSTEM':   None,
}

def emulate_joysticks_press_key(keyboard):
	if not joysticks:
		return False

	pressed_names  = set()
	released_names = set()
	for joystick in joysticks:
		for button_name in list(joystick.config.BUTTON_NAMES.values()) + list(joystick.config.HAT_BUTTONS.keys()):
			may_hide_press = button_name in joystick.config.BUTTON_NAMES_REQUIRING_MODIFIER
			if joystick.was_pressed(button_name):
				if may_hide_press and not joystick.is_any_modifier_pressed():
					joystick.hidden_press[button_name] = True
				else:
					pressed_names.add(button_name)
			if joystick.was_released(button_name):
				if may_hide_press and joystick.hidden_press[button_name]:
					joystick.hidden_press[button_name] = False
				else:
					released_names.add(button_name)

		for modifier, axis in joystick.config.MODIFIER_AXES.items():
			if joystick.was_pressed(modifier):
				pressed_names.add(modifier)
			if joystick.was_released(modifier):
				released_names.add(modifier)

	for name in pressed_names:
		keyboard._press(PRESSED_NAME_KEYS[name])
	for name in released_names:
		keyboard._release(PRESSED_NAME_KEYS[name])

	if pressed_names or released_names:
		debug(DBG_JPRS, "Pressed: %s, Released: %s", (pressed_names or {}, released_names or {}))

	return pressed_names or released_names

ARROW_KEY_BUTTON_PAIRS = (
	('r', 'NEXT'),
	('l', 'PREV'),
	('u', 'PLAY'),
	('d', 'STOP'),
)

def get_joysticks_arrow_keys():
	arrow_keys = []
	if not joysticks:
		return arrow_keys

	def add_arrow_key(arrow_key):
		if arrow_key is not None and arrow_key not in arrow_keys:
			arrow_keys.append(arrow_key)

	for joystick in joysticks:
		for arrow_key, button_name in ARROW_KEY_BUTTON_PAIRS:
			if joystick.is_pressed[button_name] and not joystick.is_any_modifier_pressed():
				add_arrow_key(arrow_key)

		add_arrow_key(joystick.when_stick_pressed('LEFT_X', 'l', 'r'))
		add_arrow_key(joystick.when_stick_pressed('LEFT_Y', 'u', 'd'))

	return arrow_keys
