from time import time
from config import STATUS_MESSAGE_FADE_DURATION, STATUS_MESSAGE_REST_DURATION
from game import game

BEAT_TIME = 5

status_messages = []
current_status_message = None
current_status_end_time = None

MIN_PRIORITY = 0
DEF_PRIORITY = 5
MAX_PRIORITY = 10

class StatusMessage:
	def __init__(self, msg, source, priority, duration):
		self.msg = msg
		self.source = source
		self.priority = priority
		self.duration = duration
		self.num_shown = 0

	def match(self, source, priority):
		return self.source == source and self.priority == priority

	def get_weight(self):
		return self.priority + self.num_shown

	def get_duration(self, max_duration):
		if self.duration is None:
			duration = max_duration
		else:
			duration = min(max_duration, self.duration)
			if self.duration - duration < BEAT_TIME:
				duration = self.duration
		return duration

	def __repr__(self):
		return 'StatusMessage("%s", s="%s", p=%d, d=%s)' % (self.msg, self.source, self.priority, self.duration)

def get_fade_text_factor(current_time, fade_out_time, fade_duration=2, rest_duration=0):
	if current_time > fade_out_time + rest_duration:
		return None
	if current_time > fade_out_time:
		return 0
	if current_time > fade_out_time - fade_duration:
		return (fade_out_time - current_time) / fade_duration
	return 1

def set_status_message(msg=None, source='main', priority=None, duration=None):
	global current_status_message, current_status_end_time

	if priority is None:
		priority = DEF_PRIORITY

	priority = min(max(priority, MIN_PRIORITY), MAX_PRIORITY)
	duration = duration or None

	current_time = time()
	was_changed = True
	sm = next((_ for _ in status_messages if _.match(source, priority)), None)

	if sm:
		if msg is None:
			status_messages.remove(sm)
		elif msg != sm.msg or duration != sm.duration:
			sm.msg = msg
			sm.duration = duration
			if current_status_message == sm:
				sm.num_shown -= 1
		else:
			was_changed = False
	elif msg is not None:
		status_messages.append(StatusMessage(msg, source, priority, duration))
	else:
		was_changed = False

	if was_changed:
		if current_status_message:
			remaining_time = current_status_end_time - current_time
			if current_status_message.duration is not None:
				current_status_message.duration += remaining_time
			current_status_message.num_shown -= remaining_time // BEAT_TIME
		current_status_message = None
		current_status_end_time = None

def get_new_current_message_and_duration():
	if not status_messages:
		return None, 0

	cand_status_messages = (
		list(sm for sm in status_messages if sm.priority == MIN_PRIORITY) or
		list(sm for sm in status_messages if sm.priority != MAX_PRIORITY) or
		status_messages
	)

	cand_status_messages = sorted(cand_status_messages, key=lambda sm: sm.get_weight())

	sm = cand_status_messages[0]

	if len(cand_status_messages) == 1:
		duration = sm.get_duration(1000)
	else:
		weight_diff = int(cand_status_messages[1].get_weight() - sm.get_weight())
		duration = sm.get_duration(BEAT_TIME * (weight_diff + 1))

	return sm, duration

def draw_status_message(POS_STATUS_Y):
	global current_status_message, current_status_end_time

	current_time = time()
	alpha = 1
	if current_status_message:
		if True:
			alpha = get_fade_text_factor(current_time, current_status_end_time, STATUS_MESSAGE_FADE_DURATION, STATUS_MESSAGE_REST_DURATION)
		if alpha is None:
			if current_status_message.duration is not None and current_status_message.duration <= 0:
				status_messages.remove(current_status_message)
			current_status_message = None
			current_status_end_time = None
			alpha = 1

	if not current_status_message:
		current_status_message, duration = get_new_current_message_and_duration()
		if current_status_message is None:
			return

		if current_status_message.duration is not None:
			current_status_message.duration -= duration

		current_status_end_time = current_time + duration

		current_status_message.num_shown += duration // BEAT_TIME

	game.screen.draw.text(current_status_message.msg, midleft=(20, POS_STATUS_Y), color="#FFF0A0", gcolor="#A09060", owidth=1.2, ocolor="#303020", alpha=alpha, fontsize=26)

def reset_status_messages():
	status_messages.clear()

