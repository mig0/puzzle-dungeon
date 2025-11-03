import os
import sys
import shlex
import argparse
from debug import debug

sys.argv[0] = 'dungeon'

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', metavar='SELECTOR', action='append', default=[], help='debug level or feature (repeatable)')
parser.add_argument('-s', '--start', metavar='LEVEL-ID', type=str, help="start with given level or collection id")
parser.add_argument('-C', '--list-collections', help="list all collections", action='store_true')
parser.add_argument('-L', '--list-ll-collections', help="list all letslogic collections", action='store_true')
parser.add_argument('-n', '--use-numeric', help="use numeric ids to list collections", action='store_true')
parser.add_argument('-b', '--bg-image', type=str, help="use this bg image for custom levels")
parser.add_argument('-c', '--cloud-mode', help="apply cloud mode to custom levels", action='store_true')
parser.add_argument('-m', '--music', type=str, help="use this music for custom levels")
parser.add_argument('-p', '--puzzle-type', '--puzzle', type=str, help="use this puzzle type for custom levels")
parser.add_argument('-r', '--reverse-barrel-mode', '--reverse', help="apply reverse barrel mode to custom levels", action='store_true')
parser.add_argument('-t', '--theme', type=str, help="use this theme for custom levels")
parser.add_argument('-M', '--no-music', help="turn music off", action='store_true')
parser.add_argument('-S', '--no-sound', help="turn sound off", action='store_true')
parser.add_argument("args", nargs='*', help="level-id, collection-id or map-file for custom collection")

cmdargs_str = os.environ.get("CMD_ARGS", "").strip()
# printf "%q" generates '' for no args
if cmdargs_str == "''":
	cmdargs_str = ""

cmdargs = parser.parse_args(shlex.split(cmdargs_str))

debug.configure(cmdargs.debug)
