#! /usr/bin/env python3

# Export smart playlists from "iTunes Music Library.xml" to text files

import os
import sys
import json
import traceback


try:
    import itunessmart
except ImportError:
    include = os.path.relpath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, include)
    import itunessmart
    print("Imported itunessmart from %s" % os.path.abspath(os.path.join(include, "itunessmart")))


def printUni(s):
    sys.stdout.buffer.write(str(s).encode("UTF-8"))
    sys.stdout.buffer.write(b"\n")



if __name__ == "__main__":


    home = os.path.expanduser("~")
    folder = os.path.join(home,"Music/iTunes");
    iTunesLibraryFile = os.path.join(folder,"iTunes Music Library.xml")

    print("Reading %s . . . " % iTunesLibraryFile)
    with open(iTunesLibraryFile, "rb") as fs:

        # Read XML file 
        library = itunessmart.readiTunesLibrary(fs)

    """
    # Create tree from XML data
    treeRoot,playlistsByPersistentId = itunessmart.createPlaylistTree(library)

    # Print the paylist tree
    try:
        from asciitree.asciitree_py3 import draw_tree
        printUni(draw_tree(treeRoot))
    except:
        pass

    # Print all smart playlists
    for playlist in library['Playlists']:
        if 'Smart Criteria' in playlist and playlist['Smart Criteria']:
            try:
                print(playlist['Name'])
            except:
                pass
    """
        
    # Decode and export all smart playlists

    parser = itunessmart.Parser()

    outputDirectory = os.path.abspath("out")

    if not os.path.exists(outputDirectory):
        os.makedirs(outputDirectory)
    
    print("Exporting playlists to %s" % outputDirectory)

    res = {}
    for playlist in library['Playlists']:
        if 'Name' in playlist and 'Smart Criteria' in playlist and 'Smart Info' in playlist and playlist['Smart Criteria']:
            try:
                parser.update_data_base64(playlist['Smart Info'],playlist['Smart Criteria'])
                filename = ("".join(x for x in playlist['Name'] if x.isalnum())) + ".txt"
                res[playlist['Name']] = parser.queryTree
                with open(os.path.join(outputDirectory, filename), "w") as fs:
                    fs.write(playlist['Name'])
                    fs.write("\r\n\r\n")
                    fs.write(parser.output)
                    #fs.write(parser.query)
                    #fs.write(json.dumps(parser.queryTree, indent=2))
                    #fs.write(parser.ignore)
                    
            except Exception as e:                
                try:
                    print("Failed to decode playlist:")
                    print(traceback.format_exc())
                    print(playlist['Name'])
                except:
                    print(playlist)

    

        
