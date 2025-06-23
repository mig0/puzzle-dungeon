from cellactor import Area, cell_distance
from flags import flags

# TODO: Consider to move all room related things from flags to here

room = Area()

def set_room(idx):
	room.size = flags.ROOM_SIZE(idx)
	room.size_x = flags.ROOM_SIZE_X[idx]
	room.size_y = flags.ROOM_SIZE_Y[idx]
	room.x1 = flags.ROOM_X1[idx]
	room.x2 = flags.ROOM_X2[idx]
	room.y1 = flags.ROOM_Y1[idx]
	room.y2 = flags.ROOM_Y2[idx]
	room.x_range = flags.ROOM_X_RANGE[idx]
	room.y_range = flags.ROOM_Y_RANGE[idx]
	room.idx = idx

def get_max_area_distance(area):
	return cell_distance((area.x1, area.y1), (area.x2, area.y2))

def get_max_room_distance():
	return get_max_area_distance(room)

def is_actor_in_room(actor):
	return actor.cx >= room.x1 and actor.cx <= room.x2 and actor.cy >= room.y1 and actor.cy <= room.y2

def get_actors_in_room(actors):
	return [actor for actor in actors if is_actor_in_room(actor)]

def is_cell_in_area(cell, x_range, y_range):
	return cell[0] in x_range and cell[1] in y_range

def is_cell_in_room(cell):
	return is_cell_in_area(cell, room.x_range, room.y_range)

