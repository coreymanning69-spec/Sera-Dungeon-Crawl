#!/usr/bin/env python3
"""Export pixel-style UI mockups to filesystem."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sera.ui import export_pixel_ui_mockups


def main():
    written = export_pixel_ui_mockups("docs/pixel-ui")
    print("Exported UI mockups:")
    for path in written:
        print(f" - {path}")


if __name__ == "__main__":
    main()
