#!/bin/bash
# Description
#   Builds the project
#
# Usage
#   $ scripts\build.bat

if [ ! -d "venv_nix" ]; then
    echo "No venv found"
    exit 1
fi

source "venv_nix/bin/activate"
if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment"
    exit 1
fi

if [ -z "$VIRTUAL_ENV" ]; then
    echo "Virtual environment not active"
    exit 1
fi

bash scripts/clean.sh
if [ $? -ne 0 ]; then
    echo "Failed to clean project"
    exit 1
fi

# Build exe
rm -f "dist/osu-norw-recorder" 2>/dev/null
pyinstaller -y "build.spec"
if [ $? -ne 0 ]; then
    echo "Failed to build exe"
    exit 1
fi

# Set binary metadata
ver_date=$(date +'%Y.%m.%d')
ver_time=$(printf "%05d" $((10000*$(date +'%H') + 100*$(date +'%M') + $(date +'%S'))))

setfattr -n user.version -v "${ver_date}.${ver_time}" dist/osu-note-recorder
setfattr -n user.description -v "An analysis tool for osu! beatmaps, replays, scores, and more!" dist/osu-note-recorder

echo "[ DONE ]"
exit 0
