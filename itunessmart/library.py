"""
Module for iTunes Library and library file `iTunes Music Library.xml`
"""

import time
import datetime
import base64
from typing import BinaryIO, Tuple, Dict

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


class Library(dict):
    pass


class LibraryException(Exception):
    pass


def generatePersistentIDMapping(library: Library) -> Dict[str, str]:
    """Create a mapping from playlist id to playlist name. Necessary for converting rules concerning other playlists to xsp.
    :param dict library: the result of readiTunesLibrary()
    :return: persistentIDMapping
    :rtype: dict
    """
    persistentIDMapping = {}
    for playlist in library['Playlists']:
        if 'Playlist Persistent ID' in playlist and "Name" in playlist:
            persistentIDMapping[playlist['Playlist Persistent ID']] = playlist["Name"]
    return persistentIDMapping


def readiTunesLibrary(libraryFileStream: BinaryIO) -> Library:
    """Read itunes library file `iTunes Music Library.xml` and return dict
    :param stream libraryFileStream: file `iTunes Music Library.xml`
    :return: iTunes library content
    :rtype: Library
    """
    parser = ET.iterparse(libraryFileStream, events=('start', 'end'))
    _, plist = next(parser)

    if plist.tag != "plist":
        raise LibraryException("Root element is not <plist> element")
    if plist.attrib['version'] != "1.0":
        raise LibraryException("<plist> version is not 1.0")

    current = Library()
    current_islist = False  # current can be dict or list
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
            # else:
            #     pass
        elif event == "end":
            # elif elem.tag == 'key':
            #     pass
            if elem.tag == 'dict' or elem.tag == 'array':
                current = parent.pop()
                current_islist = isinstance(current, list)
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
                    except ValueError:
                        elem.text = 0
                    except OverflowError as e:
                        t = datetime.datetime.strptime(elem.text, "%Y-%m-%dT%H:%M:%SZ").timetuple()
                        if t.tm_year < 1971:
                            d = 1980 - t.tm_year
                            t2 = time.struct_time([t.tm_year + d, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec, t.tm_wday, t.tm_yday, t.tm_isdst])
                            elem.text = int(time.mktime(t2)) - d * 31557600
                        elif t.tm_year > 2030:
                            d = t.tm_year - 2040
                            t2 = time.struct_time([t.tm_year - d, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec, t.tm_wday, t.tm_yday, t.tm_isdst])
                            elem.text = int(time.mktime(t2)) + d * 31557600
                        else:
                            raise e

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


class Node:
    def __init__(self, data):
        if isinstance(data, str):
            data = {'Name': data}
        self.data = data
        self.children = []
        self.parent = None

    def __str__(self):
        return "%s" % (str(self.data['Name']) if 'Name' in self.data else "Node:Unkown name")

    def __repr__(self):
        return "%s #%s" % (str(self.data['Name']) if 'Name' in self.data else "Node:Unkown name", str(self.data['Playlist Persistent ID']) if 'Playlist Persistent ID' in self.data else "")


def createPlaylistTree(library: Library) -> Tuple[Node, dict]:
    """ Create playlist tree
    :param Library library: the result of readiTunesLibrary()
    :return: Return the tree and a mapping from PersistentId to playlist: (rootNode, playlistByPersistentId_dict)
    :rtype: tuple
    """

    nodesByPersistentId = {}
    playlistByPersistentId = {}  # Map PlaylistPersistentId to Playlist data
    otherPlaylists = []  # Playlists without PersistendId
    childPlaylists = []  # This is a list of playlists, that have a Parent Persistent ID

    for playlist in library['Playlists']:
        # Clean up tracks array
        if 'Playlist Items' in playlist:
            playlist['Playlist Items'] = [[dictionary[x] for x in dictionary][0] for dictionary in playlist['Playlist Items']]

        if 'Playlist Persistent ID' not in playlist:
            otherPlaylists.append(playlist)
            continue
        playlistByPersistentId[playlist['Playlist Persistent ID']] = playlist
        if "Parent Persistent ID" in playlist:
            childPlaylists.append(playlist)

    for playlist in childPlaylists:
        node = Node(playlist)
        nodesByPersistentId[playlist['Playlist Persistent ID']] = node

        if playlist["Parent Persistent ID"] in nodesByPersistentId:
            parentNode = nodesByPersistentId[playlist["Parent Persistent ID"]]
        else:
            parentNode = Node(playlistByPersistentId[playlist["Parent Persistent ID"]])
            nodesByPersistentId[parentNode.data['Playlist Persistent ID']] = parentNode

        node.parent = parentNode
        parentNode.children.append(node)

    parentNodes = [(nodesByPersistentId[PerId] if PerId in nodesByPersistentId else Node(playlistByPersistentId[PerId])) for PerId in playlistByPersistentId if not playlistByPersistentId[PerId] in childPlaylists]

    root = Node("root")
    root.children = parentNodes + [Node(playlist) for playlist in otherPlaylists]
    root.children.sort(key=lambda node: node.data['Name'] if "Name" in node.data else "")

    return root, playlistByPersistentId
