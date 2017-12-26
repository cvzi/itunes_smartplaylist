#! /usr/bin/env python3

# Export smart playlists from "iTunes Music Library.xml" to xsp files for Kodi

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
from xsp import createXSP_file, EmptyPlaylistException




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



if __name__ == "__main__":

    EXPORT_NESTED_RULES_AS_SUBPLAYLIST = True


    home = os.path.expanduser("~")
    folder = os.path.join(home,"Music/iTunes");
    iTunesLibraryFile = os.path.join(folder,"iTunes Music Library.xml")

    print("Reading %s . . . " % iTunesLibraryFile)
    with open(iTunesLibraryFile, "rb") as fs:

        # Read XML file 
        library = readLibraryFile(fs)
        persistentIDMapping = {}
        for playlist in library['Playlists']:
            if 'Playlist Persistent ID' in playlist and "Name" in playlist:
                persistentIDMapping[playlist['Playlist Persistent ID']] = playlist["Name"]
        
        
    print("Library loaded!")    
    
    userinput = input("Do you want to convert a (single) or (all) playlists? ")
    export_all = True
    if userinput.lower() in ("single", "1", "one"):
        export_all = False
    
    userinput = input("Do you want to export nested rules to sub-playlists? (yes/no) ")
    if userinput.lower() in ("n","no", "0"):
        EXPORT_NESTED_RULES_AS_SUBPLAYLIST = False
        
    # Decode and export all smart playlists

    parser = SmartPlaylistParser()

    outputDirectory = os.path.abspath("out")

    if not os.path.exists(outputDirectory):
        os.makedirs(outputDirectory)
    
    if export_all:
        print("Converting playlists to %s" % outputDirectory)
    
    res = []
    for playlist in library['Playlists']:
        if 'Name' in playlist and 'Smart Criteria' in playlist and 'Smart Info' in playlist and playlist['Smart Criteria']:
            try:
                parser.data(playlist['Smart Info'],playlist['Smart Criteria'])
                parser.parse()
            except Exception as e:
                try:
                    print("Failed to decode playlist:")
                    print(traceback.format_exc())
                    print(playlist['Name'])
                except:
                    print(playlist)
            
            try:
                res.append((playlist['Name'], parser.queryTree))
                if export_all:
                    createXSP_file(directory=outputDirectory, name=playlist['Name'], data=parser.queryTree, createSubplaylists=EXPORT_NESTED_RULES_AS_SUBPLAYLIST, persistentIDMapping=persistentIDMapping)
            except EmptyPlaylistException as e:
                print("%s is empty." % playlist['Name'])
            except Exception as e:
                try:
                    print("Failed to convert playlist:")
                    print(traceback.format_exc())
                    print(playlist['Name'])
                except:
                    print(playlist)
                    
                    
                    
    if not export_all:
        i = 1
        for pname,_ in res:
            print("%02d: %s" % (i, pname))
            i +=1 
            
        while True:
            i = input("Please give the number of the playlist (0 to exit): ")
            if i in ("0",""):
                break
            
            i = int(i)
            pname, ptree = res[i-1]
            print("Converting Playlist: %s" % pname)
            try:
                createXSP_file(directory=outputDirectory, name=pname, data=ptree, createSubplaylists=EXPORT_NESTED_RULES_AS_SUBPLAYLIST, persistentIDMapping=persistentIDMapping)
            except EmptyPlaylistException as e:
                print("%s is empty." % pname)
            except Exception as e:
                try:
                    print("Failed to convert playlist:")
                    print(traceback.format_exc())
                    print(pname)
                except:
                    print(ptree)
                    
                    
        
    print("All done!")
