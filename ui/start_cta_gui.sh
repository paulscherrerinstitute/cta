#!/bin/bash

# Colors to match python parser
BLUE="\033[1;34m"
GREEN="\033[1;32m"
RESET="\033[0m"

# CTA GUI directory
#----------------------------------------------------
CTA_GUI_DIR="/sf/controls/bin"

# Conda environment with cta_lib and its dependencies
#----------------------------------------------------
CONDA_ENV="/sf/controls/applications/cta_lib"
PYTHON="$CONDA_ENV/bin/python"

DEV_MODE=0

if [ "$1" = "--dev" ]; then
	DEV_MODE=1
	PYTHON=python
	shift
fi

# Check python installation 
#----------------------------------------------------
if ! command -v "$PYTHON" >/dev/null 2>&1; then
	echo "ERROR: Python not found in $PYTHON"
	exit 1
fi

# Check CTA installation 
#----------------------------------------------------
if ! "$PYTHON" -c "import cta_lib; import PyQt5" >/dev/null 2>&1; then
	echo "ERROR: CTA Python environment or PyQt5 not detected."
	exit 1
fi

# Dev mode, PYTHONPATH gives priority to local folder
#----------------------------------------------------
if [ "$DEV_MODE" -eq 1 ]; then
	# Find real absolute path of the python file 
	CTA_GUI_DIR="$(dirname "$(readlink -f "$0")")"
	export PYTHONPATH="$(dirname "$CTA_GUI_DIR")/lib:$PYTHONPATH"
fi

if [ $# -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
	echo -e "${BLUE}Wrapper options:${RESET}"
	echo -e "  ${GREEN}--dev${RESET}	Use local cta_lib source tree and current Python environment"
	echo 
	exec "$PYTHON" "$CTA_GUI_DIR/cta_gui.py" --help
fi

exec "$PYTHON" "cta_gui.py" "$@"
