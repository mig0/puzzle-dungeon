INF = 10 ** 12

class Hungarian:
	def __init__(self, n_rows, n_cols=None):
		if n_cols is None:
			n_cols = n_rows
		if n_rows <= 0 or n_cols <= 0:
			raise ValueError("Number of rows and number of columns must be positive")
		if n_rows > n_cols:
			raise ValueError("Hungarian requires n_rows ≤ n_cols (swap roles if needed)")

		# n - number of rows
		self.n = n = n_rows
		# m - number of columns
		self.m = m = n_cols
		# result assignment array (0-based): a[i] = column idx for row i
		self.a = [-1] * n
		# u: row potentials, size n+1 (1-based for rows)
		self.u = [0] * (n + 1)
		# v: column potentials, size m+1 (1-based for cols)
		self.v = [0] * (m + 1)
		# p: for j in 0..m, p[j] is the current row assigned to column j
		self.p = [0] * (m + 1)
		# way: for columns
		self.way = [0] * (m + 1)
		# minv and used for columns
		self.minv = [INF] * (m + 1)
		self.used = [False] * (m + 1)

		# user-set cost matrix (0-based)
		# costs[i][j] = integer cost from row i to column j
		self.costs = [[0] * m for _ in range(n)]

	def assign(self):
		"""
		Perform assignment using costs matrix n×m (n_rows × n_cols; 0-based).

		Returns: min_total_cost; assignment_list_of_length_n is available as hungarian.a
		"""

		# local aliases (faster)
		n = self.n
		m = self.m
		a = self.a
		u = self.u
		v = self.v
		p = self.p
		way = self.way
		minv = self.minv
		used = self.used
		costs = self.costs  # user fills: costs[0..n-1][0..m-1]

		# validation of costs shape
		if len(costs) != n:
			raise ValueError("Input costs must have %d rows" % n)
		for row in costs:
			if len(row) != m:
				raise ValueError("Each costs row must have %d columns" % m)

		# reset potentials
		for i in range(n + 1):
			u[i] = 0
		for j in range(m + 1):
			v[j] = 0
			p[j] = 0

		# main loop: assign each row i = 1..n
		for i in range(1, n + 1):
			p[0] = i
			j0 = 0

			# reset row search structures for columns
			for j in range(m + 1):
				minv[j] = INF
				used[j] = False
				way[j] = 0

			while True:
				used[j0] = True
				i0 = p[j0]  # current row to try, 1..n
				delta = INF
				j1 = 0

				# scan all columns
				for j in range(1, m + 1):
					if not used[j]:
						# costs are 0-based: costs[i0-1][j-1]
						cur = costs[i0 - 1][j - 1] - u[i0] - v[j]
						if cur < minv[j]:
							minv[j] = cur
							way[j] = j0
						if minv[j] < delta:
							delta = minv[j]
							j1 = j

				# defensive check: if no candidate found -> stuck
				if j1 == 0:
					# produce diagnostic snapshot and raise to avoid infinite loop
					diag = {
						'i': i, 'i0': i0, 'j0': j0, 'minv': minv[1:],
						'costs_row': costs[i0 - 1][:],
						'u_i0': u[i0], 'v': v[1:],
					}
					raise AssertionError("Hungarian stuck: no j1 found. diag=%r" % diag)

				# update potentials
				for j in range(m + 1):
					if used[j]:
						u[p[j]] += delta
						v[j] -= delta
					else:
						minv[j] -= delta

				j0 = j1
				if p[j0] == 0:
					# found an augmenting path to a free column j0
					break

			# augmenting: update matching along the path
			while True:
				j1 = way[j0]
				p[j0] = p[j1]
				j0 = j1
				if j0 == 0:
					break

		# build 0-based assigment: p[j] is row i (1..n) assigned to column j (1..m)
		for j in range(1, m + 1):
			if p[j] > 0:
				a[p[j] - 1] = j - 1
		total_cost = sum(costs[i][a[i]] for i in range(n))

		# for square matrix everything is simplier
#		for j in range(n):
#			a[p[j + 1] - 1] = j
#		total_cost = -v[0]

		return total_cost
