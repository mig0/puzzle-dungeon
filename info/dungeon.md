# Puzzle Dungeon GUI Launcher - dungeon

## Overview

`dungeon` is the graphical user interface launcher for Puzzle Dungeon.
It allows playing many kinds of [puzzles](puzzles/) either sequentially
or in a user-defined order. The GUI integrates the Main Screen and level
gameplay into a single application.

## Usage

The GUI accepts command-line arguments that control which levels are
loaded and how they are played. Run `dungeon -h` or `dungeon --help`
from the command line to see the full usage.

Running the GUI without any option starts the Main Screen with
interactive level selection that can also be reached by pressing *Esc* in
any level.

## Level Selection

The following arguments may be used to construct a cumulative custom
level collection:

- Collection IDs  
  → `stoneage/original`
- Level IDs  
  → `atomix/original.5`
- Map files (Sokoban map files and internal maps are auto-detected)  
  → `microcosmos.txt`
- Clipboard input (map or URL supported)  
  → `clipboard:`
- Standard input (map or URL supported)  
  → `stdin:` *or* `-`
- Map files via URL  
  → `https://gamefaqs.gamespot.com/sg1000/916324-soukoban/faqs/50888`
- LetsLogic collection IDs  
  → `letslogic:30` *or* `"letslogic:Micro Cosmos"`
- LetsLogic level IDs (after loading their collection)  
  → `letslogic:/2376`

Multiple level ranges such as `2-10` or `15` are supported. They restrict
the custom collection to the given level numbers starting from 1.

## Custom Level Configuration

The following options change the defaults of all subsequently specified custom
levels, all options must preceede the level and range arguments:

- `-b`, `--bg-image` BG_IMAGE  
  Use the specified background image for custom levels.
- `-c`, `--cloud-mode`  
  Apply cloud mode to custom levels.
- `-m`, `--music` MUSIC  
  Use the specified music file for custom levels.
- `-P`, `--puzzle-type` PUZZLE_TYPE  
  Force the specified puzzle type for custom levels.
- `-t`, `--theme` THEME  
  Use the specified theme for custom levels.
- `-r`, `--reverse-barrel-mode`  
  Apply reverse barrel mode to BarrelPuzzle (Sokoban) custom levels.

## Listing Supported Collections

- `-C`, `--list-collections`  
  List all internal collections.
- `-L`, `--list-ll-collections`  
  List all LetsLogic collections.
- `-n`, `--use-numeric`  
  Use numeric IDs instead of named IDs when listing internal collections.

## Starting Level Control

- `-s LEVEL-ID`, `--start LEVEL-ID`  
  Start directly from a specific internal level or collection.

You may also use the keys *n*, *p*, *r*, *Ctrl-N*, *Ctrl-P*, and *Ctrl-R*
to navigate through internal levels and collections during gameplay.

## Audio Control

- `-M`, `--no-music`  
  Start the GUI without music.
- `-S`, `--no-sound`
  Start the GUI without sound effects.

By default, the GUI starts with both music and sound enabled. Music and
sound may still be toggled at runtime using the *m* and *s* keys.

## Debugging and Profiling

- `-d SELECTOR`, `--debug SELECTOR`  
  Enable debug features.

- `-p`, `--run-profiler`  
  Run with the built-in profiler enabled.

These options are primary intended for developers. However, advanced
users may also use special debug flags to control, for example,
[Sokoban Solver](sokobansolver.html#special-debug-flags) behaviour in
BarrelPuzzle levels.

## Example

`dungeon -S -t jewel -b bg/chemistry-2.webp atomix.1 minotaur.3 stoneage/005.map letslogic:8 1-5`

This command starts the GUI without sound effects (but with music), and
loads 4 custom levels:

- the first level from the internal AtomixPuzzle bonus collection,
- the third level from the internal MinotaurPuzzle collection,
- the fifth map from the internal StoneAgePuzzle collection,
- the first 2 levels from LetsLogic collection 8 (Original and Extra
  Thinking Rabbit Sokoban collection).

You may also add your own or stock music file, for example `-m film.mp3`.

Adding flags such as `-c` (`--cloud-mode`) or `-r` (`--reverse-barrel-mode`)
before the custom levels in the example above may significantly alter the
behaviour of these levels where applicable, use these options with care.
