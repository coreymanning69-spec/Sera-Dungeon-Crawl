#!/bin/bash
cd "$(dirname "$0")"

if command -v python3 &>/dev/null; then
    python3 play.py
elif command -v python &>/dev/null; then
    python play.py
else
    echo ""
    echo "  ERROR: Python not found!"
    echo ""
    echo "  Install Python 3 to play SERA."
    echo "  Ubuntu/Debian: sudo apt install python3"
    echo "  Mac: brew install python3"
    echo ""
fi
