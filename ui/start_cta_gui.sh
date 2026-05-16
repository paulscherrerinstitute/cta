#!/bin/bash

# Colors to match python parser
BLUE="\033[1;34m"
GREEN="\033[1;32m"
RESET="\033[0m"

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
    exit 1
fi

# Check CTA installation 
#----------------------------------------------------
if ! python -c "import cta_lib; import PyQt5" >/dev/null 2>&1; then
    echo "ERROR: CTA Python environment or PyQt5 not detected."
    exit 1
fi

# Dev mode, PYTHONPATH gives priority to local folder
#----------------------------------------------------
if [ "$DEV_MODE" -eq 1 ]; then
    export PYTHONPATH="$(dirname "$BASEDIR")/lib:$PYTHONPATH"
fi

if [ $# -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
	echo -e "${BLUE}Wrapper options:${RESET}"
	echo -e "  ${GREEN}--dev${RESET}	Use Local development cta_lib instead of installed package"
	echo 
	exec python "$BASEDIR/cta_gui.py" --help
fi

exec python "$BASEDIR/cta_gui.py" "$@"
