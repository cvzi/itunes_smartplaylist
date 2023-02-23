#! /usr/bin/env python3

# Export smart playlists from "iTunes Music Library.xml" to text files

import os
import sys
# import json
import traceback
# import base64
import re


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

def repl(match, playlist):
    if match.group('ID') in playlistsByPersistentId:
        return 'PlaylistName' + match.group('op') + '"' + playlistsByPersistentId[match.group('ID')]['Name'] + '"'
    else:
        print("No playlist with Persistent ID %r (mentinoned in playlist %r)" % (match.group('ID'), playlist['Name']))
        return match.group(0)


if __name__ == "__main__":

    if len(sys.argv)>1:
        iTunesLibraryFile = sys.argv[1];
    else:
        home = os.path.expanduser("~")
        folder = os.path.join(home, "Music/iTunes")
        iTunesLibraryFile = os.path.join(folder, "iTunes Music Library.xml")

    print("Reading %s . . . " % iTunesLibraryFile)
    with open(iTunesLibraryFile, "rb") as fs:

        # Read XML file
        library = itunessmart.readiTunesLibrary(fs)

    # Create tree from XML data
    treeRoot, playlistsByPersistentId = itunessmart.createPlaylistTree(library)

#    # Print the paylist tree
#    try:
#        from asciitree.asciitree_py3 import draw_tree
#        printUni(draw_tree(treeRoot))
#    except (UnicodeEncodeError, KeyError, TypeError) as e:
#        pass
#
#    # Print all smart playlists
#    for playlist in library['Playlists']:
#        if 'Smart Criteria' in playlist and playlist['Smart Criteria']:
#            try:
#                print(playlist['Name'])
#            except (KeyError, TypeError) as e:
#                pass

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
                parser.update_data_bytes(playlist['Smart Info'], playlist['Smart Criteria'])
                filename = ("".join(x for x in playlist['Name'] if x.isalnum())) + ".txt"
                res[playlist['Name']] = parser.result.queryTree
                text_output = parser.result.output

                # Replace 'PlaylistPersistentID is <ID>' with 'PlaylistName is "<Name>"'
                text_output = re.sub(r'PlaylistPersistentID(?P<op>[is not]+)(?P<ID>[0-9A-F]{2,16})', lambda m: repl(m, playlist), text_output)

                with open(os.path.join(outputDirectory, filename), "w") as fs:
                    fs.write(playlist['Name'])
                    fs.write("\r\n\r\n")
                    fs.write(text_output)
                    # fs.write(parser.result.query)
                    # fs.write(json.dumps(parser.result.queryTree, indent=2))
                    # fs.write(parser.result.ignore)
                    # fs.write("\r\n")
                    # fs.write(base64.standard_b64encode(playlist['Smart Info']).decode("utf-8"))
                    # fs.write("\r\n")
                    # fs.write(base64.standard_b64encode(playlist['Smart Criteria']).decode("utf-8"))
            except itunessmart.EmptyPlaylistException as e:
                print("`%s` is empty." % playlist['Name'])
            except itunessmart.PlaylistException as e:
                print("Skipped `%s`: %s" % (playlist['Name'], str(e)))
            except Exception as e:
                try:
                    print("Failed to decode playlist:")
                    print(traceback.format_exc())
                    print(playlist['Name'])
                except (UnicodeEncodeError, KeyError, TypeError) as e:
                    print(playlist)
