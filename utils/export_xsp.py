#! /usr/bin/env python3

"""Export smart playlists from "iTunes Music Library.xml" to xsp files for Kodi"""

import sys
import os
include = os.path.relpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, include)
import itunessmart.__main__

if __name__ == "__main__":
    itunessmart.__main__.main(*sys.argv[1:])
