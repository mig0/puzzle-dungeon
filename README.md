# Puzzle Dungeon

## About Game

Puzzle Dungeon is a Free Software cell-based puzzle game packed with
features and diverse challenges. It includes implementations of classic
games like Sokoban, StoneAge, Atomix, The Minotaur and Theseus, Memory
and Fifteen — along with completely new puzzle types.

See the list of all [puzzles](#puzzles) for details.

The game is multiplatform. It uses pygame and pgzero, and should run well
on GNU/Linux, Windows, and other operating systems.

## Features

- **Procedurally Generated Puzzles**:
  Most levels are generated automatically, offering a new experience
  every time. Pre-created maps are also supported, including classic
  collections. Players can reload the same level if stuck - whether it’s
  newly generated or pre-created.

- **Variety of Challenges**:
  Some puzzles are time-limited, others require strict adherence to
  rules, and many involve finding a path to the finish. Some levels even
  feature enemy encounters.

- **Customizable Themes**:
  The game includes 13 themes, well suited for different puzzle types.

- **Multilingual Support**:
  The game is primarily in English, with partial translations available
  in several other languages.

- **Versatile Controls**:
  Players can use a keyboard, mouse, or PlayStation controller.

- **Audio Options**:
  Background music and sound effects can be toggled on or off.

## Themes

* default
* classic
* ancient1, ancient2
* modern1, modern2
* minecraft
* moss
* stoneage1, stoneage2, stoneage3, stoneage4, stoneage5

## Static cells

* floor – empty cell, sometimes textured with cracks, bones, or rocks
* wall – blocks all access
* glass – like a wall, but passable for things like a beam
* plate – can be pressed or weighted down
* gate0 / gate1 – closed and open gates
* trap1 / trap0 – active and inactive traps
* start – if present, the character appears here at the beginning
* finish – if present, this cell must be reached to complete the level or room
* portal – teleports to an arbitrary cell or another portal
* lock1, lock2 – can be opened with key1 and key2 respectively
* odirl, odirr, odiru, odird – one-way blocked cells (from left, right, up, down)
* sand – allows one-time access; turns into void after stepping off
* void – inaccessible to the character; lifts are required to move across void
* beamgn, beamcl – beam generator and collector (for mirror puzzles)

## Actors

* character – that's you
* enemy – you fight it
* barrel – you push it
* cart – you slide it across the floor
* lift – you ride it to move across void
* mirror – can be attached to barrel, cart, or lift

## Drops from enemies or floor collectibles

* heart (extra health)
* sword (extra attack)
* might (extra power)
* key1, key2

## Keyboard bindings

|key|action
|--|--
|n|Next level
|p|Prev level
|r|Restart level
|Ctrl-N|Next level collection
|Ctrl-P|Prev level collection
|Ctrl-R|Curr level collection
|F1-F10|Set different themes
|Shift F1-F10|Set more themes
|F11|Set fullscreen on/off
|F12|Set mouse visible off/on
|l|Show title and goal
|m|Turn on/off music
|s|Turn on/off sound
|u|Undo move
|a|Toggle move animation
|w|Win the level (cheating)
|Space|Press cell, force teleport and more
|Enter|Activate cursor
|Esc|Exit to the main screen
|KP-Enter|Find solution, then replay it
|RShift-E|Set language to English
|RShift-R|Set language to Russian
|RShift-H|Set language to Hebrew
|RShift-L|Enabled/disabled show title and goal
|RShift-D|Print current map
|Home|    Simulate mouse button 1
|End|     Simulate mouse button 3
|Insert|  Simulate mouse button 2
|Delete|  Simulate mouse button 6
|PageUp|  Simulate mouse button 4
|PageDown|Simulate mouse button 5
|Ctrl-Escape|Display Pygame Console if available
|Shift-Delete|Reset all mirrors

## Source code

The [Puzzle Dungeon source code](https://github.com/mig0/puzzle-dungeon.git)
is available on GitHub and can be cloned using:

```bash
git clone https://github.com/mig0/puzzle-dungeon.git
```

## How to run

See [download](download.html) page for instructions how to download the
latest game package.

You need python3-pygame, [python3-]pgzero and python3-bitarray. These may be installed using:

```bash
pip install pgzero bitarray
```

No installation is needed to quickly run the game, just unzip the
package, or checkout the source code from github, then run:

```bash
./dungeon
```

On Windows, run __dungeon.bat__.

On Unix systems, you may optionally install it using "make install".

## Puzzles

### Atomix Puzzle

Atomix is a puzzle game where you construct complete molecules, ranging
from simple to highly complex, by arranging isolated atoms scattered
among walls and other obstacles.

When you push an atom in a direction, it moves until it collides with an
object that halts its motion - this could be a wall or another atom. This
mechanic makes Atomix challenging and engaging, as careful planning is
required to organize your molecule correctly.

There are also bonus levels where the colored numbered atoms are used
instead of the chemical atoms. The player must guess the correct number
structure and arrange these atoms into it.

Goal: Build a complete molecule from atoms. Press Enter to select atoms.

### Barrel Puzzle (Sokoban)

This is a classic game with straightforward yet challenging rules. You
guide the "warehouse keeper" ("Sokoban" in Japanese) to push barrels into
designated slots. A barrel can only be pushed in one of four directions,
provided there is empty space behind it in that direction.

The objective is to place all barrels onto the plates in the room.
Sometimes, barrels must be temporarily moved off plates to enable access
for others. Limited space and the potential for unsolvable positions make
this puzzle both strategic and addictive.

Each level introduces a unique layout of walls, floors, barrels, and
plates, requiring new strategies and solutions.

Goal: Push all barrels onto the designated plates.

### Color Puzzle

This simple yet intriguing puzzle is designed to demonstrate the
potential of Puzzle mechanics. Some floor cells are assigned colors, and
the number of colors and their areas are configurable. Plates on the
floor can be pressed to alter the colors of the eight surrounding cells.

Pressing a plate rotates the colors in sequence. For instance, if there
are five colors (1 - red, 2 - green, 3 - blue, 4 - yellow, 5 - purple)
and neighboring cells are colors 1, 3, and 5, pressing the plate changes
them to 2, 4, and 1, respectively.

Goal: Turn all colored cells green by pressing the plates.

### Fifteen Puzzle

The 15 Puzzle, popularized by Sam Lloyd, is a sliding puzzle. It consists
of 15 numbered tiles, arranged within a 4×4 frame containing one empty
cell. Tiles in the same row or column as the empty cell can be slid
horizontally or vertically.

The frame can be of size n×n or even n×m, then the puzzle may be called
the 2ⁿ-1 puzzle or the n×m sliding puzzle rather than 15 Puzzle.

The objective is to rearrange the tiles into numerical order (left to
right, top to bottom). Starting from a shuffled configuration (after
numerous random legal moves), players must use strategic sliding to
return the tiles to their original positions.

No shortest solution is required, the puzzle can be solved using any
valid sequence of moves.

Goal: Restore the numbered tiles to their original positions.

### Gate Puzzle

In this puzzle, you navigate a maze filled with plates and gates. Gates
can either be open or closed, blocking or allowing progress. Plates are
scattered throughout the maze and serve as triggers for the gates.

Each plate toggles the state of one or more attached gates. Pressing a
plate may open previously closed gates while closing others, requiring
careful planning and exploration.

Press Space on keyboard (or "X" on PS controller) to activate the plate.

Goal: Reach the finish by pressing plates to open a path.

### Hero Puzzle

This puzzle challenges the hero to build their power and defeat enemies.

Similar to Hero Wars bonus levels but with more complexity, the hero
starts with a configured power level. Power can be increased or decreased
using power potions that apply four distinct arithmetic operations.

To solve the puzzle, the player must strategically navigate the map,
defeating all enemies and collecting items in the correct order.

In the default mode, players collect keys available in each floor after
defeating enemies and gathering potions. Floors can be completed in any
order, but all must be finished. In the "strict_floors" mode, players
must complete a floor before moving to the next and cannot revisit
previous floors.

Goal: Collect all keys (if applicable) and defeat all enemies.

### Lock Puzzle

In this puzzle, the maze contains keys and locks of two distinct types.
Closed locks block your progress, and keys are scattered throughout the
maze. Each key can open any lock of the corresponding type, but once
used, a key disappears, and the lock remains permanently open.

The maze includes branching paths, some of which lead to dead ends. These
branches may still hold valuable keys or locks, requiring exploration and
strategy to navigate effectively. The number and type of keys are
perfectly matched to the number and type of locks, so every key must be
used wisely.

Goal: Reach the finish by collecting and using keys to unlock the path.

### Memory Puzzle

This puzzle tests your memory skills within a grid of cells. The puzzle
area consists of an even number of cells, each containing a hidden value.
All values are randomly shuffled, and pairs of equivalent numbers are
scattered across the grid in a way that their locations are unknown to
the player. Your task is to find and match these pairs.

You select two cells at a time to reveal their values. The first selected
cell stays revealed until the second cell is chosen. If the two revealed
cells match, they are removed from the puzzle. If they do not match, they
are hidden again, and you must remember their positions for future
attempts.

A visual variation replaces numbers with distinct colors for matching,
offering a more aesthetic challenge. The puzzle can be navigated and
manipulated using various controls: arrow keys and Space for keyboard
users, a PlayStation controller for similar precise navigation, or a
mouse for point-and-click simplicity.

Goal: Clear the puzzle area by matching and removing all pairs of values.

### Minotaur Puzzle

This puzzle is based on the classic Theseus and the Minotaur game.
The maze consists of floor and wall cells, along with a single finish
cell. Two actors navigate the maze: the player character and the
Minotaur.

The player moves one step per turn in any of the four cardinal directions
(or skips a move by pressing a Space), while the Minotaur moves up to two
steps per turn according to specific rules. The Minotaur always tries to
reach the player by prioritizing horizontal movement first - if it is not
aligned with the player - before making a vertical move. If a move is
blocked by a wall, the Minotaur skips that step.

Each level is designed to be challenging. A direct path to the finish
usually results in the player being caught, forcing the player to find an
alternative, more strategic route to outmaneuver the Minotaur and reach
the finish safely.

Goal: Reach the finish without being caught by the Minotaur.

### Mirror Puzzle

You control how beams of light travel from a beam generator to a beam
collector, using mirrors attached to movable or static objects. These
mirrors reflect the beam in different ways, and may have limited or
flipped activeness. Your objective is to arrange mirrors and possibly
move or reconfigure them so that at least one part of the beam reaches
the collector.

The beam is emitted from the generator in four directions: left, right,
up, and down. Each direction of the beam proceeds cell by cell until it
is reflected, redirected, or terminates. The beam continues through empty
floor cells, void cells, glass, sand, open gates, trap cells, portals,
and also through barrels, enemies, the character, and mirrors. It is
terminated by walls and locks. If it enters a portal, it instantly
appears at the paired portal in the same direction. Portals do not
reflect or bypass; they relocate the beam to the peer.

Mirrors are defined by their orientation, activeness and their carrier
object. There are four mirror orientations:

• Diagonal 1 (/): reflects left ↔ down and right ↔ up

• Diagonal 2 (\): reflects left ↔ up and right ↔ down

• Horizontal (-): reverses vertical direction (up ↔ down)

• Vertical   (|): reverses horizontal direction (left ↔ right)

Mirrors are active or inactive. An inactive mirror does not affect the
beam at all - it continues straight. An active mirror reflects the beam
according to the list above. Mirrors can also have flipped
activeness: such mirrors are active the first time they are hit by a
beam, but become inactive for that beam on subsequent hits (or vice
versa).

Each mirror is attached to one of three types of carriers:

• Barrels: pushable by the character, move one cell per push on floor.

• Carts: move on floor, one cell per player instruction, in 0, 1, 2, or 4
directions depending on movement type.

• Lifts: move across void, stopping at the first obstacle, by player
instruction, with the same direction types as carts.

Goal: Deliver at least one part of the beam using mirrors.

### Portal Puzzle

In this puzzle, there are 9 halls arranged in a 3x3 grid. Each hall has
portals located in its corners as the only means of exit. Depending on
the puzzle variation, a hall may have 2, 3, or 4 portals. Each portal
transports the character to one of the 9 halls, with the destination
being pre-determined randomly at the start of the puzzle and remaining
consistent throughout.

The first hall, located in the top-left corner, serves as the starting
point. The central hall is unique; it contains the finish in one corner
and an additional portal in the opposite corner that leads back to the
starting hall. This return portal is added for fun, allowing players to
revisit the challenge and experiment with different portal choices.

The other 8 halls are structurally identical, each containing the same
number of portals in corresponding corners. Success requires strategic
navigation and exploration to determine the paths that lead to the
central hall and ultimately to the finish.

Goal: Reach the finish by navigating through the portals.

### RotatePic Puzzle

This puzzle involves restoring a large image that has been divided into
square mini-image cells. Each cell is randomly rotated by 0, 90, 180, or
270 degrees at the start. Your task is to rotate all mini-image cells to
return them to their correct orientation and recreate the original image.

The puzzle can be navigated and manipulated using various controls. With
the keyboard, you can use the arrow keys to navigate to a cell and Space
or PageDown (or PageUp) to rotate it clockwise (or counter-clockwise).
The cells may be similarly navigated and rotated with PlayStation
controller. For mouse users, clicking on a cell rotates it clockwise or
anti-clockwise depending on the mouse button used.

Goal: Rotate all mini-image cells to restore the original image.

### StoneAge Puzzle

This puzzle is an accurate replication of the classic DOS game Stone Age,
released in 1992. The puzzle area consists of various elements, including
a start cell, a finish cell, floors, walls, sands, paired portals, keys,
locks, void cells, and directional lifts. Each element adds unique
mechanics to the challenge.

The character can freely travel through floor cells. Sand cells are
traversable once and transform into void cells upon exit, requiring
careful planning. Portals and directional lifts allow access to otherwise
unreachable areas, while keys of two distinct types can be collected and
used to unlock corresponding locks. Directional lifts are the only way to
cross void cells.

Strategic use of these mechanics is essential to navigate through the
puzzle and access the finish cell. The combination of diverse elements
makes this puzzle both challenging and nostalgic for fans of the original
game.

Goal: Reach the finish by utilizing the environment and its mechanics.

### SwitchBox Puzzle

This puzzle is an extension of the Gate Puzzle and the Barrel Puzzle,
introducing complex interactions between gates, plates, and barrels.
The maze contains colored plates that control the behavior of gates and
barrels. Each plate, when pressed by the player or a barrel, activates
all gates and/or barrels of the same color.

Gates are initially closed and block access to parts of the maze,
including the finish. Plates open corresponding gates when pressed.
Barrels can be pushed onto plates or through opened gates. Gates stay
open as long as the corresponding plate is weighted by either the player
or a barrel. If the player pushes a barrel through a gate while keeping
the plate pressed (by standing on it), the gate remains open during the
movement. Gates only close when no one remains on the plate or on the
gate itself.

Additionally, plates may phase barrels - that is, they can switch all
barrels of the same color into a semi-transparent "phased" state when
activated. While in this state, a phased barrel becomes passable: the
player and non-phased barrels can move through it as if it were empty
space. Despite this, a phased barrel still counts as pressing any plate
it rests on, which adds a new layer of strategic planning to the puzzle.

These dynamic mechanics require careful sequencing of movements and
consideration of gate, plate, and barrel interactions to navigate toward
the finish.

Goal: Open all gates using barrels and reach the finish.

### Trivial Puzzle

This puzzle serves as a demonstration of Puzzle API. It is minimalistic
and relies mostly on default settings, with the only significant
modification being the inclusion of a finish cell. If enemies are
present, they can be avoided.

Goal: Simply reach the finish.

## License

This is Free Software, distributed under GNU General Public License version 3 or later.

## Developers

The game **Puzzle Dungeon** is developed by Mikhael Goikhman and his son
Daniel Goikhman. The project began as a fun and educational way to teach
and learn programming from scratch. It continues to evolve with the same
passion, highlighting programming as a lifelong skill and an exciting
creative endeavor.

The development team welcomes contributions from other developers.

## Contact Us

If you would like to contribute as a developer, artist or mathematician
to develop puzzle algorithms, please drop a note to migo00 at gmail.

Have fun with Puzzle Dungeon!

