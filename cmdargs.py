import os
import sys
import shlex
import argparse
from config import DEBUG_LEVEL

sys.argv[0] = 'dungeon'

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', type=int, help="debug level for extra output (default: %d)" % DEBUG_LEVEL, default=DEBUG_LEVEL)
parser.add_argument('-l', '--level', type=str, help="start with given level")
parser.add_argument('-c', '--collection', type=str, help="start with given collection")
parser.add_argument('-C', '--list-collections', help="list all collections", action='store_true')
parser.add_argument('-n', '--use-numeric', help="use numeric ids to list collections", action='store_true')
parser.add_argument('-r', '--reverse-barrel-mode', '--reverse', help="apply reverse-barrel-mode", action='store_true')

cmdargs_str = os.environ.get("CMD_ARGS", "").strip()
# printf "%q" generates '' for no args
if cmdargs_str == "''":
	cmdargs_str = ""

cmdargs = parser.parse_args(shlex.split(cmdargs_str))
