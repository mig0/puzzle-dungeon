import os
import sys
import shlex
import argparse
from config import DEBUG_LEVEL

sys.argv[0] = 'dungeon'

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', type=int, help="debug level for extra output (default: %d)" % DEBUG_LEVEL, default=DEBUG_LEVEL)

cmdargs_str = os.environ.get("CMD_ARGS", "").strip()
# printf "%q" generates '' for no args
if cmdargs_str == "''":
	cmdargs_str = ""

cmdargs = parser.parse_args(shlex.split(cmdargs_str))
