#! /usr/bin/env python3

# Export smart playlists from "iTunes Music Library.xml" to xsp files for Kodi

import os
import traceback
import sys

# If we are running from a wheel, add the wheel to sys.path
if __package__ == '':
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)


try:
    import itunessmart
except ImportError:
    include = os.path.relpath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, include)
    import itunessmart



def printWithoutException(s):
    try:
        print(s)
    except UnicodeEncodeError:
        try:
            print(str(s).encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
        except UnicodeEncodeError:
            print(str(s).encode('ascii', errors='replace').decode('ascii'))
    

if __name__ == "__main__":

    EXPORT_NESTED_RULES_AS_SUBPLAYLIST = True


    home = os.path.expanduser("~")
    folder = os.path.join(home,"Music/iTunes");
    iTunesLibraryFile = os.path.join(folder,"iTunes Music Library.xml")

    print("# Reading %s . . . " % iTunesLibraryFile)
    with open(iTunesLibraryFile, "rb") as fs:
        # Read XML file 
        library = itunessmart.readiTunesLibrary(fs)
        persistentIDMapping = itunessmart.generatePersistentIDMapping(library)
        
        
    print("# Library loaded!")
    
    userinput = input("# Do you want to convert a (single) or (all) playlists? ")
    export_all = True
    if userinput.lower() in ("single", "1", "one"):
        export_all = False
    
    userinput = input("# Do you want to export nested rules to sub-playlists? (yes/no) ")
    if userinput.lower() in ("n","no", "0"):
        EXPORT_NESTED_RULES_AS_SUBPLAYLIST = False
        
    # Decode and export all smart playlists

    parser = itunessmart.Parser()

    outputDirectory = os.path.abspath("out")

    if not os.path.exists(outputDirectory):
        os.makedirs(outputDirectory)
    
    if export_all:
        print("# Converting playlists to %s" % outputDirectory)
    
    res = []
    for playlist in library['Playlists']:
        if 'Name' in playlist and 'Smart Criteria' in playlist and 'Smart Info' in playlist and playlist['Smart Criteria']:
            try:
                parser.update_data_bytes(playlist['Smart Info'],playlist['Smart Criteria'])
            except Exception as e:
                try:
                    print("! Failed to decode playlist:")
                    print(traceback.format_exc())
                    printWithoutException(playlist['Name'])
                except:
                    printWithoutException(playlist)
            
            if not parser.result:
                continue
            
            try:
                res.append((playlist['Name'], parser.result))
                if export_all:
                    itunessmart.createXSPFile(directory=outputDirectory, name=playlist['Name'], smartPlaylist=parser.result, createSubplaylists=EXPORT_NESTED_RULES_AS_SUBPLAYLIST, persistentIDMapping=persistentIDMapping)
            except itunessmart.EmptyPlaylistException as e:
                printWithoutException("! `%s` is empty." % playlist['Name'])
            except itunessmart.PlaylistException as e:
                printWithoutException("! Skipped `%s`: %s" % (playlist['Name'], str(e)))
            except Exception as e:
                try:
                    print("! Failed to convert playlist:")
                    print(traceback.format_exc())
                    printWithoutException(playlist['Name'])
                except:
                    printWithoutException(playlist)
                    
                    
                    
    if not export_all:
        i = 1
        for p_name,_ in res:
            printWithoutException("# %02d: %s" % (i, p_name))
            i +=1 
        
        while True:
            i = input("# Please give the number of the playlist (0 to exit): ")
            if i in ("0",""):
                break
            
            i = int(i)
            p_name, p_result = res[i-1]
            printWithoutException("# Converting Playlist: %s" % p_name)
            try:
                itunessmart.createXSPFile(directory=outputDirectory, name=p_name, smartPlaylist=p_result, createSubplaylists=EXPORT_NESTED_RULES_AS_SUBPLAYLIST, persistentIDMapping=persistentIDMapping)
            except itunessmart.EmptyPlaylistException as e:
                printWithoutException("! `%s` is empty." % p_name)
            except itunessmart.PlaylistException as e:
                printWithoutException("! Skipped `%s`: %s" % (p_name, str(e)))
            except Exception as e:
                try:
                    print("! Failed to convert playlist:")
                    print(traceback.format_exc())
                    printWithoutException(p_name)
                except:
                    print(p_result)
                    
                    
        
    print("# All done!")
    userdata = os.path.expandvars(r"%appdata%\kodi\userdata\playlists\music") if os.path.exists(os.path.expandvars(r"%appdata%\kodi\userdata")) else os.path.expanduser(r"~/Library/Application Support/Kodi/userdata/playlists/music")
    print("# You may copy the .xsp files to %s" % userdata)

