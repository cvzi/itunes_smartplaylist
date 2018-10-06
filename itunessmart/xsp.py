"""
Module to convert from a parser result to a XSP playlist
"""
import logging
import hashlib
import unicodedata
import re
import html
import os.path
from typing import Callable, List, Tuple

from itunessmart.xsp_structure import *
from itunessmart.parse import SmartPlaylist

__all__ = ["createXSPFile", "createXSP", "PlaylistException", "EmptyPlaylistException"]
    
class PlaylistException(Exception):
    pass

class EmptyPlaylistException(PlaylistException):
    pass

def createXSPFile(directory: str, name: str, smartPlaylist: SmartPlaylist, createSubplaylists: bool = True, persistentIDMapping: dict = None, friendlyFilename: Callable[[str], str] = None) -> List[str]:
    """ Create XSP playlist file(s) from the parser result queryTree, returns a list of filenames of the generates files
    :param str directory: the output directory
    :param str name: the new name of the playlist
    :param SmartPlaylist smartPlaylist: the result of the parser
    :param bool createSubplaylists: if true subplaylists are created for nested rules/query, if false nestes rules are ommited
    :param persistentIDMapping: Optional, necessary for rules containing other playlists
    :param function friendlyFilename: Optional, function to create a filename from the playlist name: e.g. friendlyFilename = lambda name: name.strip()
    :return: list filenames
    :rtype: list
    """
    
    if friendlyFilename is None:
        def friendlyFilename(name):
            filename = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode("utf-8")
            filename = re.sub('[^\w\s-]', '', filename).strip()
            return filename

    r = []
    for playlistname, content in createXSP(name=name, smartPlaylist=smartPlaylist, createSubplaylists=createSubplaylists, persistentIDMapping=persistentIDMapping):
        filename = friendlyFilename(playlistname) + ".xsp"
        filepath = os.path.join(directory, filename)
        with open(filepath, "wb") as f:
            f.write(content.encode("utf-8"))
        logging.info(filename)
        r.append(filename)
    
    return r

def createXSP(name: str, smartPlaylist: SmartPlaylist, createSubplaylists: bool = True, persistentIDMapping: dict = None, subPlaylistPrefix: str = "zzzsub_") -> List[Tuple[str, str]]:
    """ Create XSP playlist(s) from the parser result queryTree, returns a list of tuples (playlist_name, xml_content)
    :param str name: the new name of the playlist
    :param SmartPlaylist smartPlaylist: the result of the parser
    :param bool createSubplaylists: if true subplaylists are created for nested rules/query, if false nestes rules are ommited
    :param persistentIDMapping: Optional, necessary for rules containing other playlists
    :param subPlaylistPrefix: Prefix for name of sub playlists (prefix is followed by the md5 hash of the subplaylist xml)
    :return: list of tuples: (playlist_name, xml_content)
    :rtype: list
    """
    
    if persistentIDMapping is None:
        persistentIDMapping = {}
        
    queryTree = smartPlaylist.queryTree
    fulltree = queryTree["fulltree"]
    
    if not fulltree:
        raise EmptyPlaylistException("Playlist is empty", name)
    
    if "and" in fulltree:
        globalmatch = "and"
    else:
        globalmatch = "or"
    
    f = _minimize(_combineRules(fulltree, persistentIDMapping, createSubplaylists))
    
    if f:
        y = _convertRule(f, depth=0, docs = [])
        if len(y) == 3:
            # Complete doc
            globalmatch, rules, subplaylists = y
        else:
            # Only one rule
            globalmatch = "and"
            rules = y
            subplaylists = []
            
    else:
        raise PlaylistException("Playlist is incompatible. All of the rules are incompatible with XSP format", name)
        
        
    limit = ('    <limit>%d</limit>' % queryTree['number']) if 'number' in queryTree else ''
    order = ""
    if 'order' in queryTree:
        if queryTree['order'] == "RANDOM()":
            order = '    <order>random</order>'
        elif queryTree['order'] in xsp_sorting:
            order = '    <order direction="%s">%s</order>' % xsp_sorting[queryTree['order']]
    
    meta = limit + '\n' + order
    
    r = []
    if createSubplaylists and subplaylists:
        for sub_globalmatch, sub_rules in subplaylists:
            sub_name = subPlaylistPrefix + hashlib.md5(sub_rules.encode('utf-8')).hexdigest()
            subdocument = xml_doc.format(dec=xml_dec, name=_escapeHTML(sub_name), globalmatch=xsp_operators[sub_globalmatch], rules=sub_rules, meta="")
            rules += "\n" + xml_rule.format(field="playlist", operator="is", values=xml_value.format(value=_escapeHTML(sub_name)))
            r.append((sub_name, subdocument))
    
    
    document = xml_doc.format(dec=xml_dec, name=_escapeHTML(name), globalmatch=xsp_operators[globalmatch], rules=rules, meta=meta)
    
    r.append((name, document))
    
    
    return r

def _combineRules(obj, persistentIDMapping, createSubplaylists):
    """Remove incompatible rules and combine similar rules"""
    if "and" in obj or "or" in obj:
        result = []
        for operator in obj:
            t = (operator, [])
            for x in obj[operator]:
                y = _combineRules(x, persistentIDMapping, createSubplaylists)
                if y:

                    # combine with existing rule
                    combined = False
                    if operator is "or" and type(y) == dict:
                        for r in t[1]:
                            if type(r) == dict and r["field"] == y["field"] and r["operator"] == y["operator"]:
                                if type(r["value"]) != list:
                                    r["value"] = [r["value"]]
                                r["value"].append(y["value"])
                                combined = True
                                break
                    if not combined:
                        t[1].append(y)
                    
            if len(t[1]) > 1:
                result.append((operator, t[1]))
            elif len(t[1]) == 1 and t[1] is not None:
                result.append(t[1][0])
            else:
                pass
        return result
    else:
        if not obj["field"] in xsp_allowed_fields:
            return None
        if not obj["operator"] in xsp_allowed_operators:
            return None
            
        if obj["field"] == "PlaylistPersistentID":
            if obj["value"] in persistentIDMapping:
                # Replace PersistentID with playlistname
                obj["value"] = persistentIDMapping[obj["value"]]
                if not createSubplaylists:
                    try:
                        logging.warning("# Playlist dependency ignored: Depends on '%s'" % obj["value"])
                    except:
                        logging.warning("# Playlist dependency ignored.")
            else:
                return None
            
        return obj
    
def _minimize(obj):
    """Remove lists with only one entry"""
    if type(obj) is list:
        if len(obj) == 1:
            return _minimize(obj[0])
        else:
            result = []
            for x in obj:
                y = _minimize(obj)
                if y:
                    result.append(y)
            return result
    else:
        return obj

"""
def flat(obj, depth=0):
    # Remove everything except first level
    if depth > 1:
        return

    if type(obj) is tuple:
        return (obj[0], flat(obj[1], depth+1))

    if type(obj) is list:
        result = []
        for x in obj:
            y = flat(x, depth)
            if y:
                result.append(y)
        return result
    
    if type(obj) is dict:
        return obj 
"""

def _escapeHTML(x):
    t = type(x)
    if t is str:
        return html.escape(x, quote=False)
    if t is int or t is float:
        return x
    
    return [_escapeHTML(i) for i in x]

def _convertRule(obj, depth, docs):
    """Create XML rules"""
    
    if type(obj) is tuple:
        if not obj[1]:
            return ""
        operator = obj[0]
        rules = []
        for x in obj[1]:
            y = _convertRule(obj=x, depth=depth+1, docs=docs)
            if y:
                rules.append(y)
        if depth > 0:
            docs.append((operator, "\n".join(rules)))
            return ""
        else:
            return operator, "\n".join(rules), docs
        
    elif type(obj) is dict:
        if "value_date" in obj:
            obj["value"] = obj["value_date"]
        if type(obj["value"]) is not list:
            obj["value"] = [obj["value"]]
        values = []
        for value in obj["value"]:
            values.append(xml_value.format(value=_escapeHTML(value)))
        values = "\n".join(values) 
        return xml_rule.format(field=xsp_fields[obj["field"]], operator=xsp_operators[obj["operator"]], values=values)
    
    elif type(obj) is list:
        rules = []
        for x in obj:
            y = _convertRule(obj=x, depth=depth, docs=docs)
            if y:
                rules.append(y)
        return "\n".join(rules)
    
    else:
        raise PlaylistException("Unknown obj type", repr(obj))


