# Sokoban Solver in Puzzle Dungeon

## Overview

Puzzle Dungeon includes a full-featured Sokoban solver that is nicely
integrated with both the graphical game [dungeon](dungeon.html) and the
command-line tool [sokodun](sokodun.html).

The solver is implemented entirely in Python, follows classical search
theory, and its correctness and optimality are confirmed by comprehensive
automated tests.

The solver is designed primarily for small maps, and in some cases
medium-sized maps. It prioritizes correctness, flexibility, and clarity
over raw performance, although a considerable number of domain-specific
and python-specific optimizations are present.

## Supported Search Algorithms

The solver supports multiple classical graph search algorithms,
selectable at runtime:

- **Breadth-First Search (BFS)**  
  Explores all positions by increasing depth (number of pushes).

- **Uniform Cost Search (UCS)**  
  Explores positions in order of increasing total cost for the selected
  metric, without using heuristics. The first solution found is optimal.

- **A\***  
  Uses admissible heuristics (cost so far plus a lower-bound estimate of
  remaining cost) to guide the search and find optimal solutions.

- **Greedy Best-First Search**  
  Uses the same heuristics as A* but prioritizes estimated remaining cost.
  Optimality is not guaranteed, but solutions are often found quicker.

- **Depth-First Search (DFS)**  
  Non-optimal and primarily useful for experimentation and debugging.
  May use less memory, but has own artifacts. It is actually IDDFS with
  depth step.

The optimality of BFS, UCS, and A* is confirmed by comprehensive tests
across different level classes.

## Solution Types and Cost Metrics

The solver supports two solution types:

- **Move-optimal solutions**  
  Minimize the number of character moves, with shifts (pushes or pulls)
  as a secondary metric.

- **Push-optimal solutions**  
  Minimize the number of shifts (pushes or pulls), with moves as a
  secondary metric.

All costs are represented uniformly as a **lexicographic pair**
__(num_moves, num_shifts)__. This applies consistently to path costs,
lower-bound estimates, and solution costs.

## Solver Architecture

The **Position** (search node) represents a unique combination of the
character location and all barrel locations.

Barrel locations are stored in a **SuperPosition** object. A Position is
one character placement within its super-position. This allows multiple
character states to share properties of the same barrel configuration,
like:

- solved / dead status,
- lower-bound path cost and solution estimation,
- precomputed matching data.

Other properties are stored per Position, including:

- parent pointer,
- edge-specific costs (own_nums),
- accumulated path cost (total_nums),
- child edge information (when needed for edge relaxation).

Each position has a single best parent at any time. If a better path to
an existing position is found, the position is reparented. For algorithms
that require edge relaxation (A*, BFS by moves), potential child edges
are stored to allow reparenting back when accumulated path cost improves.

## Heuristics and Lower Bounds

All search algorithms benefit from prepared domain-specific data:

- **Dead-cell detection**  
  Cells where a barrel can never participate in a solution are detected
  upfront and excluded.

- **Precomputed costs**  
  - Lower-bound costs from every non-dead cell to every goal cell.
  - Lower-bound costs from any initial barrel cell to all reachable cells.

- **Perfect matching of barrels to plates**  
  A lower bound for assigning barrels to goal cells is computed using the
  **Hungarian algorithm**.

The lower bound from a position to a solution uses perfect matching.
The lower bound from the initial position to intermediate positions
(currently used for pruning after a solution is found) is computed as a
sum of minimal barrel-to-target costs without matching.

For heuristic-based algorithms (A* and Greedy), the perfect matching is
used. The admissible heuristics preserves optimality for A*.

For UCS, optimality follows directly from cost-order exploration: the
first solution found is optimal.

For BFS:

- By shifts: optimality follows from fixed-depth exploration.
- By moves: optimality is ensured via sorting and edge relaxation.

Preparation can be disabled for experimentation or benchmarking.

## Special Level Support

The solver supports several special Sokoban level classes:

- **Circular levels**  
  Levels where the initial position is already solved (all barrels
  start on plates). A solution must include at least one shift (push or
  pull), making these levels non-trivial.

- **Zero-Space Type-B (ZSB) levels**  
  Only a restricted but valid subset of moves is generated, resulting in
  significantly faster solving. See the forum discussion about
  [Zero-Space Type-B](https://groups.io/g/sokoban/topic/113333167).

- **Reverse Barrel Mode**  
  Storage cells are replaced with barrels, and the player pulls instead
  of pushing. Shifts become pulls at the grid level; the solver logic
  itself remains unchanged. The character position is currently
  unchanged, which makes some puzzles unsolvable in this mode. The proper
  fix is to change the initial character location according to the
  solution in forward (push) mode if known.

## Solver Design Highlights

- Explicit state graph with reopening support.
- Correct edge relaxation and state reparenting.
- Unified solver core for GUI and CLI.
- Extensive regression tests.
- Clear separation between algorithm, cost model, and heuristics.
- Optional return-first mode, trading optimality for speed.

## Incremental Solving and Budgeting

The solver implements a cooperative budget protocol:

- Control is yielded approximately once per second.
- Progress messages are emitted.
- Solving can resume from the interruption point.

This behavior is used by both the GUI and the command-line tool and can
be disabled.

## Performance Notes

This is possibly the most complete Sokoban solver implemented in Python.  

It is slower than some specialized solvers because:

- it is written in Python,
- corral pruning and some advanced heuristics are not yet implemented.

Despite this, it is well suited for Puzzle Dungeon gameplay, testing, and
provides a solid foundation for tooling, research, and further
optimization.
