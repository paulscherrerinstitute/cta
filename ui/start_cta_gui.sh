#!/bin/bash

# Find real absolute path of the python file 
BASEDIR="$(dirname "$(readlink -f "$0")")"

DEV_MODE=0

if [ "$1" = "--dev" ]; then
    DEV_MODE=1
    shift
fi

# Check python installation 
#----------------------------------------------------
if ! command -v python >/dev/null 2>&1; then
    echo "ERROR: Python not found in PATH."
    echo "Please activate the CTA Python environment first."
    exit 1
fi

# Check CTA installation 
#----------------------------------------------------
if ! python -c "import cta_lib" >/dev/null 2>&1; then
    echo "ERROR: CTA Python environment not detected."
    echo "Please activate an environment providing cta_lib."
    exit 1
fi

# Dev mode, PYTHONPATH gives priority to local folder
#----------------------------------------------------
if [ "$DEV_MODE" -eq 1 ]; then
    export PYTHONPATH="$(dirname "$BASEDIR")/lib:$PYTHONPATH"
fi

if [ $# -eq 0 ]; then
	exec python "$BASEDIR/cta_gui.py" --help
fi

exec python "$BASEDIR/cta_gui.py" "$@"
