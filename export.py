#! /usr/bin/env python3
#Python v3.4

# Export smart playlists from "iTunes Music Library.xml" to text files

import os
import sys
import base64
import json
import traceback

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from itunes_smartplaylist import SmartPlaylistParser


def printUni(s):
    sys.stdout.buffer.write(str(s).encode("UTF-8"))
    sys.stdout.buffer.write(b"\n")

    
class Node:
    def __init__(self,data):
        if type(data) is str:
            data = {'Name':data}
        self.data = data
        self.children = []
        self.parent = None
    def __str__(self):
        return "%s" % (str(self.data['Name']) if 'Name' in self.data else "Node:Unkown name")
    def __repr__(self):
        return "%s #%s" % (str(self.data['Name']) if 'Name' in self.data else "Node:Unkown name",str(self.data['Playlist Persistent ID']) if 'Playlist Persistent ID' in self.data else "")
    
def readLibraryFile(libraryFile):

    parser = ET.iterparse(libraryFile, events=('start','end'))
    _, plist = next(parser)

    assert plist.tag == "plist"
    assert plist.attrib['version'] == "1.0"
    
    current = {}
    current_islist = False # current can be dict or list
    key = "plist"
    data = current
    parent = [data]

    for event, elem in parser:
        if event == "start":
            if elem.tag == 'dict':
                if current_islist:
                    t = {}
                    current.append(t)
                    parent.append(current)
                    current = t
                else:
                    current[key] = {}
                    parent.append(current)
                    current = current[key]
                current_islist = False
            elif elem.tag == 'key':
                key = elem.text
            elif elem.tag == 'array':
                if current_islist:
                    t = []
                    current.append(t)
                    parent.append(current)
                    current = t
                else:
                    current[key] = []
                    parent.append(current)
                    current = current[key]
                current_islist = True
            else:
                pass
        elif event == "end":            
            if elem.tag == 'key':
                pass
            elif elem.tag == 'dict':
                current = parent.pop()
                current_islist = type(current) is list
            elif elem.tag == 'array':
                current = parent.pop()
                current_islist = type(current) is list
            else:
                if elem.tag == 'true':
                    elem.text = True
                elif elem.tag == 'false':
                    elem.text = False
                elif elem.tag == 'integer':
                    elem.text = int(elem.text)
                elif elem.tag == 'date':
                    try:
                        elem.text = int(time.mktime(datetime.datetime.strptime(elem.text, "%Y-%m-%dT%H:%M:%SZ").timetuple()))
                    except:
                        elem.text = 0
                elif elem.tag == 'data':
                    elem.text = base64.standard_b64decode("".join(elem.text.split()))

                
                if current_islist:
                    current.append(elem.text)
                else:
                    current[key] = elem.text
                    
            elem.clear()
    plist.clear()

    data = data['plist']
    return data

def createPlaylistTree(data):
    """ Create playlist tree"""
    
    nodesByPersistentId = {}
    playlistByPersistentId = {} # Map PlaylistPersistentId to Playlist data
    otherPlaylists = [] # Playlists without PersistendId
    childPlaylists = [] # This is a list of playlists, that have a Parent Persistent ID

    for playlist in data['Playlists']:
        # Clean up tracks array
        if 'Playlist Items' in playlist:
            playlist['Playlist Items'] = [[dictionary[x] for x in dictionary][0] for dictionary in playlist['Playlist Items']]

        
        if 'Playlist Persistent ID' not in playlist:
            otherPlaylists.append(playlist)
            continue
        playlistByPersistentId[playlist['Playlist Persistent ID']] = playlist
        if "Parent Persistent ID" in  playlist:
            childPlaylists.append(playlist)

    for playlist in childPlaylists:
        node = Node(playlist)
        nodesByPersistentId[ playlist['Playlist Persistent ID'] ] = node

        if playlist["Parent Persistent ID"] in nodesByPersistentId:
            parentNode = nodesByPersistentId[playlist["Parent Persistent ID"]]
        else:
            parentNode = Node(playlistByPersistentId[playlist["Parent Persistent ID"]])
            nodesByPersistentId[ parentNode.data['Playlist Persistent ID'] ] = parentNode
            
        node.parent = parentNode
        parentNode.children.append(node)

    parentNodes = [ (nodesByPersistentId[PerId] if PerId in nodesByPersistentId else Node(playlistByPersistentId[PerId])) for PerId in playlistByPersistentId if not playlistByPersistentId[PerId] in childPlaylists]    

    root = Node("root")
    root.children = parentNodes + [Node(playlist) for playlist in otherPlaylists]
    root.children.sort(key = lambda node: node.data['Name'] if "Name" in node.data else "")
    
    return root,playlistByPersistentId


if __name__ == "__main__":


    home = os.path.expanduser("~")
    folder = os.path.join(home,"Music/iTunes");
    iTunesLibraryFile = os.path.join(folder,"iTunes Music Library.xml")

    print("Reading %s . . . " % iTunesLibraryFile)
    with open(iTunesLibraryFile, "rb") as fs:

        # Read XML file 
        library = readLibraryFile(fs)

    """
    # Create tree from XML data
    treeRoot,playlistsByPersistentId = createPlaylistTree(library)

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

    parser = SmartPlaylistParser()

    outputDirectory = os.path.abspath("out")

    if not os.path.exists(outputDirectory):
        os.makedirs(outputDirectory)
    
    print("Exporting playlists to %s" % outputDirectory)
    
    for playlist in library['Playlists']:
        if 'Smart Criteria' in playlist and 'Smart Info' in playlist and playlist['Smart Criteria']:
            try:
                parser.data(playlist['Smart Info'],playlist['Smart Criteria'])
                parser.parse()
                filename = ("".join(x for x in playlist['Name'] if x.isalnum())) + ".txt"
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
                    print(playlist['Name'])
                    #print(traceback.format_exc())
                    print("Error: %s" % str(e))
                except:
                    pass

        
