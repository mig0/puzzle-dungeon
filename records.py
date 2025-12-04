import os
from celltools import cmp

class RecordsParseError(Exception):
	pass

def _parse_cost_str(cost_str):
	# cost_str must be 'NUM/NUM'
	if "/" not in cost_str:
		raise RecordsParseError(f"Invalid cost str: {cost_str}")
	a, b = cost_str.split("/", 1)
	return (int(a), int(b))

class CollectionRecords:
	"""
	Read file of lines: level_id<TAB>cost
	  or just: cost

	Where cost is:
	  "A/B"   → both push-optimal and move-optimal
	  "A/B C/D"  → first is push-optimal, second is move-optimal

	Interface:
	  - by_moves=False → use push-optimal record list
	  - by_moves=True  → use move-optimal record list

	Properties:
	  - record_strs      → list of "A/B", depending on by_moves
	  - push_record_strs → list of "A/B"
	  - move_record_strs → list of "A/B"
	  - result_strs      → list of "A/B"
	  - push_records → list of cost (num_moves, num_shifts)
	  - move_records → list of cost (num_moves, num_shifts)
	  - results      → list of cost (num_moves, num_shifts)
	  - next_result_idx
	  - level_ids

	Methods:
	  - cmp_level_result("X/Y")  → compare result vs stored record:
		 return -1 (better), 0 (equal), 1 (worse), or None (no data)
	  - update_file([...])       → write improved results back to file
	"""

	def __init__(self, filename, by_moves=False, def_level_ids=False):
		self.filename = filename
		self.by_moves = by_moves
		self.def_level_ids = def_level_ids

		self.push_records = []  # list of (moves, pushes)
		self.move_records = []  # list of (moves, pushes)
		self.level_ids = []     # keep original left column for rewrite
		self.results = []       # keep reported results
		self.next_result_idx = 0  # counter for iterative interface

		self._read_file()

	@property
	def records(self):
		return self.move_records if self.by_moves else self.push_records

	def _append_record(self, cost1, cost2=None):
		if cost2 is None:
			cost2 = cost1
		self.push_records.append(cost1)
		self.move_records.append(cost2)

	def _read_file(self):
		if not os.path.exists(self.filename):
			raise RecordsParseError(f"Records file not found: {self.filename}")

		with open(self.filename, "r", encoding="utf-8") as file:
			for ln, line in enumerate(file):
				line_no = ln + 1
				line = line.strip()
				if not line:
					continue

				if "\t" in line:
					level_id, cost_str = line.split("\t", 1)
				else:
					level_id, cost_str = f"Level {line_no}" if self.def_level_ids else None, line
				self.level_ids.append(level_id)

				# cost_str may be "A/B" or "A/B C/D"
				parts = cost_str.split()
				if len(parts) == 1:
					self._append_record(_parse_cost_str(parts[0]))
				elif len(parts) == 2:
					self._append_record(_parse_cost_str(parts[0]), _parse_cost_str(parts[1]))
				else:
					raise RecordsParseError(f"Invalid cost format at line {line_no}: {cost_str}")

	def get_cost_strs(self, costs):
		return [f"{a}/{b}" for (a, b) in costs]

	@property
	def push_record_strs(self):
		return self.get_cost_strs(self.push_records)

	@property
	def move_record_strs(self):
		return self.get_cost_strs(self.move_records)

	@property
	def record_strs(self):
		return self.get_cost_strs(self.records)

	@property
	def result_strs(self):
		return self.get_cost_strs(self.results)

	@property
	def record_str_at_result(self):
		record_strs = self.record_strs
		return None if self.next_result_idx >= len(record_strs) else record_strs[self.next_result_idx]

	def cmp_costs(self, cost1, cost2):
		(m1, s1), (m2, s2) = cost1, cost2
		return cmp((m1, s1), (m2, s2)) if self.by_moves else cmp((s1, m1), (s2, m2))

	def cmp_level_result(self, result_str):
		"""
		Assume next sequential level.

		On out-of-range → return None.
		"""

		level_idx = self.next_result_idx

		if level_idx < 0 or level_idx >= len(self.records):
			return None

		result = _parse_cost_str(result_str) if result_str else None
		record = self.records[level_idx]

		self.results.append(result)
		self.next_result_idx += 1

		return self.cmp_costs(result, record) if result else None

	def update_file(self, result_strs=None):
		"""
		results: list of strings "X/Y", same ordering as file.
		Update file only if some actual is better than stored record.
		We update both push and move records depending on by_moves flag.
		"""

		if result_strs is None:
			result_strs = self.result_strs

		updated = False

		for i, result_str in enumerate(result_strs):
			if i >= len(self.records):
				break

			result = _parse_cost_str(result_str)

			if i >= len(self.move_records):
				self._append_record(result)
				updated = True
			elif self.by_moves:
				if result < self.move_records[i]:
					self.move_records[i] = result
					updated = True
			else:
				if result < self.push_records[i]:
					self.push_records[i] = result
					updated = True

		if updated:
			self._rewrite_file()

		return updated

	def _rewrite_file(self):
		"""
		Rewrite using the stored push_records and move_records.
		If both equal at a line → write single "A/B".
		Else write "A/B C/D".
		"""

		lines = []
		for level_id, cost1, cost2 in zip(self.level_ids, self.push_records, self.move_records):
			if cost1 == cost2:
				cost_str = f"{cost1[0]}/{cost1[1]}"
			else:
				cost_str = f"{cost1[0]}/{cost1[1]} {cost2[0]}/{cost2[1]}"
			lines.append(f"{level_id}\t{cost_str}" if level_id else cost_str)

		with open(self.filename, "w", encoding="utf-8") as f:
			f.write("\n".join(lines) + "\n")

if __name__ == "__main__":
	import sys
	assert len(sys.argv) == 2, "Usage: python records.py filename-to-rewrite"
	records = CollectionRecords(sys.argv[1])
	records._rewrite_file()
