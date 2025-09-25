from . import *

MAX_SETUPS_TO_TRY = 10000
MAX_GOOD_SETUPS_TO_TRY = 20
MAX_GENERATE_TIME = 7

CAR_TYPE_DIRS = {
	0: ((0, -1), (0, 1)),
	1: ((-1, 0), (1, 0)),
}

class Car:
	def __init__(self, cell, type, exit_dir=None):
		self.cell = cell
		self.type = type
		self.exit_dir = exit_dir

	def is_target(self):
		return self.exit_dir is not None

	def get_dirs(self):
		return CAR_TYPE_DIRS[self.type]

	def move(self, dir, undo=False):
		self.cell = apply_diff(self.cell, dir, undo)

class CarPark:
	def __init__(self, size, cars=None):
		self.size = size
		self.cars = cars or []

	def add(self, car):
		self.cars.append(car)

	def get_car_cells(self):
		return tuple(car.cell for car in self.cars)

	def get_car_on_cell(self, cell, exclude_car=None):
		return next((car for car in self.cars if car != exclude_car and car.cell == cell), None)

	def is_free(self, cell, exclude_car=None):
		return not self.get_car_on_cell(cell, exclude_car)

	def is_inside(self, cell):
		return 0 <= cell[0] < self.size[0] and 0 <= cell[1] < self.size[1]

	def is_car_valid(self, car):
		return self.is_inside(car.cell) and self.is_free(car.cell, car)

	def make_free_cell(self, cell, moves=None, visited_car_cells=None):
		if not moves:
			moves = []
			visited_car_cells = []
		if self.is_free(cell):
			return moves

		car_cells = self.get_car_cells()
		if car_cells in visited_car_cells:
			return None
		visited_car_cells.append(car_cells)

		for car in self.cars:
			for dir in car.get_dirs():
				moves.append(dir)
				car.move(dir)
				if self.is_car_valid(car) and self.make_free_cell(cell, moves, visited_car_cells):
					return moves
				car.move(dir, True)
				moves.pop(-1)

		return None

	def scramble(self, num_moves):
		return []

class TrafficPuzzle(Puzzle):
	def has_gate(self):
		return True

	def is_goal_to_be_solved(self):
		return True

	def on_set_room(self):
		self.set_area_from_config(default_size=DEFAULT_TRAFFIC_PUZZLE_SIZE, align_to_center=True)

	def generate_random_nonsolvable_room(self):
		num_targets_left = self.num_targets
		color_idx = 0
		self.exit_color_idxs = {}
		for _ in range(self.area.num_cells - self.num_free_cells):
			cell = self.get_random_matching_cell_in_area([CELL_VOID], [lift.c for lift in lifts])
			lift_type = MOVE_V if randint(0, 1) == 0 else MOVE_H
			create_lift(cell, lift_type)
			lift = lifts[-1]
			if num_targets_left > 0:
				exit_cell = (self.area.x1 - 1, lift.cy) if lift_type == MOVE_H else (lift.cx, self.area.y1 - 1)
				if exit_cell not in self.exit_color_idxs:
					self.exit_color_idxs[exit_cell] = color_idx
					color_idx = (color_idx + 1) % len(EXTENDED_COLOR_RGB_VALUES)
				lift.color = EXTENDED_COLOR_RGB_VALUES[self.exit_color_idxs[exit_cell]]
				num_targets_left -= 1

	def generate_random_setup(self):
		carpark = CarPark(self.area.size)

		for _ in range(self.area.num_cells - self.num_free_cells - self.num_targets):
			while True:
				cell = (randint(0, self.area.size_x - 1), randint(0, self.area.size_y - 1))
				if carpark.is_free(cell):
					carpark.add(Car(cell, randint(0, 1)))
					break

		num_total_moves = 0
		target_dirs = {}
		for _ in range(self.num_targets):
			type = randint(0, 1)
			incr = randint(0, 1)
			i = randint(0, (self.area.size_x if type else self.area.size_y) - 1)
			if type and not incr:
				end_cell = (0, i)
			elif type and incr:
				end_cell = (self.area.size_x - 1, i)
			elif not type and not incr:
				end_cell = (i, 0)
			else:
				end_cell = (i, self.area.size_y - 1)

			moves = carpark.make_free_cell(end_cell)
			if moves == None:
				return None

			num_total_moves += len(moves) + 1
			carpark.add(Car(end_cell, type, CAR_TYPE_DIRS[type][incr]))

		moves = carpark.scramble(1000)
		num_total_moves += len(moves)

		return num_total_moves, carpark

	def generate_random_solvable_room(self):
		carpark = self.generate_best_random_setups(MAX_SETUPS_TO_TRY, MAX_GOOD_SETUPS_TO_TRY, MAX_GENERATE_TIME, self.generate_random_setup)

		if carpark:
			color_idx = 0
			self.exit_color_idxs = {}
			for car in carpark.cars:
				lift_type = MOVE_H if car.type else MOVE_V
				lift_cell = apply_diff(car.cell, self.area.cell11)
				create_lift(lift_cell, lift_type)
				if car.is_target():
					lift = lifts[-1]
					if car.exit_dir == (0, -1):
						exit_cell = (lift.cx, self.area.y1 - 1)
					elif car.exit_dir == (0, 1):
						exit_cell = (lift.cx, self.area.y2 + 1)
					elif car.exit_dir == (-1, 0):
						exit_cell = (self.area.x1 - 1, lift.cy)
					else:
						exit_cell = (self.area.x2 + 1, lift.cy)
					if exit_cell not in self.exit_color_idxs:
						self.exit_color_idxs[exit_cell] = color_idx
						color_idx = (color_idx + 1) % len(EXTENDED_COLOR_RGB_VALUES)
					lift.color = EXTENDED_COLOR_RGB_VALUES[self.exit_color_idxs[exit_cell]]
			return

		warn("Can't generate traffic level, making it random unsolvable")
		self.generate_random_nonsolvable_room()

	def generate_room(self):
		self.num_free_cells = self.parse_config_num("num_free_cells", 2)
		self.num_targets = self.parse_config_num("num_targets", 1)
		self.set_area_cells(CELL_VOID, add_border_walls=True)

		self.generate_random_solvable_room()

	def on_set_theme(self):
		self.color_void_images = []
		gray_void_image = make_grayscale_image(load_theme_cell_image('floor'))
		for color_idx in range(len(self.exit_color_idxs)):
			color = EXTENDED_COLOR_RGB_VALUES[color_idx % len(EXTENDED_COLOR_RGB_VALUES)]
			self.color_void_images.append(colorize_image(gray_void_image.copy(), color))

	def get_cell_image_to_draw(self, cell, cell_type):
		if cell in self.exit_color_idxs:
			return self.color_void_images[self.exit_color_idxs[cell]]
		return None
