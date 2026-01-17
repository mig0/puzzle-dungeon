# Sokoban Solver in Puzzle Dungeon

## Overview

Puzzle Dungeon includes a full-featured Sokoban solver that is tightly
integrated with both the graphical game [dungeon](dungeon.html) and the
command-line tool [sokodun](sokodun.html).

The code is Free Software, and should run on GNU/Linux, Windows, MacOS.

The solver is implemented entirely in Python, follows classical search
theory, and its correctness and optimality are validated by comprehensive
automated tests.

It works well for small maps, and in some cases medium-sized maps. It
prioritizes correctness, flexibility, and clarity over raw performance,
although a considerable number of domain-specific and python-specific
optimizations are present.

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
  Optimality is not guaranteed, but solutions are often found faster.

- **Depth-First Search (DFS)**  
  Non-optimal and primarily useful for experimentation and debugging. May
  use less memory, but has its own artifacts. It is implemented as IDDFS
  with a depth step.

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
*(num_moves, num_shifts)*. This representation is used consistently for
path costs, lower-bound estimates, and solution costs.

## Solver Architecture

The **Position** (search node) represents a unique combination of the
character location and all barrel locations.

Barrel locations are stored in a **SuperPosition** object. A Position is
one character placement within its super-position. This allows multiple
character states to share properties of the same barrel configuration,
such as:

- solved / dead status,
- lower-bound path cost and solution estimation,
- precomputed matching data.

Other properties are stored per Position, including:

- parent pointer,
- edge-specific cost (own_nums),
- accumulated path cost (total_nums),
- child edge information (when needed for edge relaxation).

Each position has a single best parent at any time. If a better path to
an existing position is found, the position is reparented. For algorithms
that require edge relaxation (A*, BFS by moves), potential child edges
are stored to allow reparenting back when accumulated path cost improves.

## Heuristics and Lower Bounds

All search algorithms benefit from prepared domain-specific data:

- **Dead cells**  
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

Prepared data can be disabled for experimentation or benchmarking.

## Special Level Support

The solver supports several special Sokoban level classes:

- **Circular levels**  
  Levels where the initial position is already solved (all barrels start
  on plates). A solution must include at least one shift (push or pull),
  making these levels non-trivial.

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
  solution in forward (push) mode, if known.

## Deadlock Detection

The following types of deadlocks are detected:

- simple local deadlocks (for example, 2x2 patterns),
- dynamic match deadlocks (barrel-to-plate assignment via Hungarian),
- freeze deadlocks (barrels form zigzag between walls, block each other),
- corral freeze deadlock (corrals with no valid barrel pushes to open).

## Solver Design Highlights

- Support for a wide range of Sokoban level variants.
- Support for move-optimal and push-optimal solutions.
- Support for forward and reverse modes.
- Detection of multiple local and dynamic deadlock types.
- Explicit state graph with reopening support.
- Correct edge relaxation and state reparenting.
- Clear separation between algorithm, cost model, and heuristics.
- Unified solver core for GUI and CLI.
- Extensive regression tests.
- Optional return-first mode, trading optimality for speed.

## Incremental Solving and Budgeting

The solver implements a cooperative budget protocol:

- Control is yielded approximately once per second.
- Progress messages are emitted.
- Solving can resume from the interruption point.

This report-progress behavior is used by both the GUI and the
command-line tool and can be disabled.

## Special Debug Flags

Both the graphical game [dungeon](dungeon.html) and the command-line tool
[sokodun](sokodun.html) support the following *-d FEATURE* (or *--debug
FEATURE*) flags:

- *`prun`* - report prune, deadlock and solution counters every second
- *`nofd`* - disable detection of Freeze deadlocks
- *`nocd`* - disable detection of Corral Freeze deadlocks
- *`dlck`* - display all Match, Freeze and Corral Freeze deadlocks
- *`sevt`* - dump SokobanSolver event log (floody; redirect to *.sel file)
- *`solv`*, *`solv+`*, *`solv++`* - dump position processing log (floody)
- *`prevalid`* - dump prepared valid shift data per level
- *`precosts`*, *`precosts+`* - dump prepared costs data per level

These feature flags are handled by SokobanSolver itself, either changing
behaviour or writing relevant output to stdout. Multiple flags may be
specified using separate -d options.

There is no way to disable detection of Match (or Bipartite) deadlocks.
By design, the costs and valid shifts do not make sense for mismatched
board positions (for which there is no perfect barrel-to-plate matching).
So such Position object is just never created; this can't be disabled.

## GUI vs CLI, Keys and Options

|GUI key|CLI option|Action
|--|--|--------
|RCtrl-1|`-1`|Toggle return-first solution mode
|RCtrl-A|`-A`|Use A* algorithm
|RCtrl-B|`-B`|Use BFS algorithm
|RCtrl-D|`-D`|Use DFS algorithm
|RCtrl-G|`-G`|Use Greedy algorithm
|RCtrl-U|`-U`|Use UCS (Uniform Cost) algorithm
|RCtrl-0|`-0`|Disable periodic progress reporting
|RCtrl-\-|`-_`|Disable cost and valid shift preparation (debug only)
|KP_Enter|default|Find a push optimal solution
|Shift-KP_Enter|`-m`|Find a move optimal solution
|Backspace|*Ctrl-C* or N/A|Stop solving or playing a solution, or unset the solution
|RCtrl-Tab|N/A|Show the most recently created position while solving
|RCtrl-Backquote|N/A|Show the most recently detected deadlock while solving
|Alt-R|N/A|Reload level (guaranteed same map unlike plain *r*)
|Alt-E|N/A|Reload level with toggled reverse-barrel mode
|Alt-C|N/A|Load custom collection levels from the clipboard
|Alt-S|N/A|Load a solution from the clipboard

In both GUI and CLI modes, levels may be loaded from the clipboard or
standard input using `clipboard:` or `stdin:` or `-` arguments, and all
detected deadlocks may be dumped to standard output using `--debug dlck`
option (this can be pretty floody).

## Performance Notes

This is possibly the most complete Sokoban solver implemented in Python.

It may be much slower than some specialized solvers because:

- it is written in the high-level Python language,
- advanced corral based heuristics are not yet implemented.

A typical Sokoban level contains many millions of unique positions.
Currently the solver keeps all visited positions and never removes them
while solving. It would be much slower without this permanent cache.

There is no memory management yet. It will eventually fill all available
memory. The operating system may kill the process, but this can freeze
the computing unit. Therefore, remember to stop the process (by pressing
*Ctrl-C* in the CLI or any button like *Space* in the GUI), or limit it
by time ("-T 600" limits execution to 10 minutes in the CLI). Garbage
collection takes time, so please be patient after using lots of memory.

You can run the solver on large levels to observe where it gets stuck,
but do not leave it running for too long. It is recomended to always
start with return-first Greedy mode (specify "sokodun -1" or press
*RCtrl-1* in the GUI). Once it finds a return-first solution in
reasonable time, you may attempt to solve it using BFS, A* or USC (*-B*,
*-A*, *-U* with optional *-m* in the CLI, or *RCtrl-{B,A,U}* followed by
*KP_Enter* or *Shift-KP_Enter* in the GUI) to find a push-optimal or
move-optimal solution.

If the solution does not progress quickly for Greedy or A*, this can mean
some non-trivial deadlock was not detected, and expanding a deadlocked
position is costy. Press *RCtrl-Backquote* in the GUI to see the last
discovered dynamic deadlock. Press *RCtrl-Tab* (any number of times) to
see the last created position; if it contains an undetected deadlock,
this can explain long processing times.

Despite performance limitations, this Sokoban solver is well suited for
Puzzle Dungeon gameplay, testing, and provides a solid foundation for
tooling, research, and further optimization.

## Validity of Solutions

There are comprehensive tests. If you discover any anomaly, like a
non-optimal solution for a letslogic level using BFS or A*, or a
"Solution not found" result, please report such exotic cases. They can
then be fixed, added to tests, and prevented from recurring.

If the minimal solution depth (number of pushes) is determined to be
larger than 500, the solution is currently reported immediately as "not
found". This limitation may be removed in the future.

Enjoy!
