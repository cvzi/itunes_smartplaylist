#! /usr/bin/env python3

# Find music files that exist on the hard drive but are not present in the
# library file.

import os
import sys
import shutil
# import json
import traceback
import urllib.parse
# import base64


try:
    import itunessmart
except ImportError:
    include = os.path.relpath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, include)
    import itunessmart
    print(
        "Imported itunessmart from %s" %
        os.path.abspath(
            os.path.join(
                include,
                "itunessmart")))


def printUni(s):
    sys.stdout.buffer.write(str(s).encode("UTF-8"))
    sys.stdout.buffer.write(b"\n")


if __name__ == "__main__":

    harddriveFolder = 'C:\\iTunes\\Music'
    move = False
    moveFolder = 'C:\\iTunes\\Music\\superfluos'

    home = os.path.expanduser("~")
    folder = os.path.join(home, "Music/iTunes")
    iTunesLibraryFile = os.path.join(folder, "iTunes Music Library.xml")

    # Read XML file
    print("Reading %s . . . " % iTunesLibraryFile)
    with open(iTunesLibraryFile, "rb") as fs:
        library = itunessmart.readiTunesLibrary(fs)

    print("Done!")

    # Find all files in library file
    libraryfiles = []
    for tid in library['Tracks']:
        track = library['Tracks'][tid]
        if track and 'Location' in track and track['Location']:
            loc = urllib.parse.unquote(track['Location'])
            if 'localhost/' in loc:
                loc = loc.split('localhost/')[1]
            loc = os.path.abspath(loc)
            libraryfiles.append(loc.lower())

    print(len(libraryfiles), 'files in library')

    # Walk files on harddrive
    superfluos = []
    walk = os.walk(harddriveFolder)
    n = 0
    for root, dirs, files in walk:
        for name in files:
            filename = os.path.join(root, name)
            if 'itlp' in filename:
                continue
            nameLower = name.lower()
            if nameLower.endswith(('.mp3', '.aac', '.m4a')):
                n += 1
                if filename.lower() not in libraryfiles:
                    superfluos.append(filename)

    print(n, 'files on harddrive')

    print(len(superfluos), 'superfluos files:')

    for f in superfluos:
        artist = os.path.basename(os.path.dirname(os.path.dirname(f)))
        if artist == 'images' or artist.endswith('itlp'):
            continue

        print(f)
        if move:
            newloc = os.path.join(moveFolder, artist)
            if not os.path.isdir(newloc):
                os.mkdirs(newloc)
            shutil.move(f, newloc)
            print('Moved', f)
