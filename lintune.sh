#!/bin/bash
# LinTune Launcher
# Launch the LinTune GUI application

cd "$(dirname "$0")"
python -m src.lintune "$@"

