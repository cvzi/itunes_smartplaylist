"""
Module to convert from a parser result to a XSP playlist
"""

import hashlib
import unicodedata
import re
import html
import os.path

from itunessmart.xsp_structure import *

__all__ = ["createXSPFile", "createXSP", "PlaylistException", "EmptyPlaylistException"]
    
class PlaylistException(Exception):
    pass

class EmptyPlaylistException(PlaylistException):
    pass

def createXSPFile(directory, name, queryTree, createSubplaylists=True, persistentIDMapping=None, friendlyFilename=None):
    """ Create XSP playlist file(s) from the parser result queryTree, returns a list of filenames of the generates files
    :param str directory: the output directory
    :param str name: the new name of the playlist
    :param dict queryTree: the result of the parser
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
    for name,content in createXSP(name, data, createSubplaylists, persistentIDMapping):
        filename = friendlyFilename(name) + ".xsp"
        filepath = os.path.join(directory, filename)
        with open(filepath, "wb") as f:
            f.write(content.encode("utf-8"))
        print(filename)
        r.append(filename)
    
    return r

def createXSP(name, queryTree, createSubplaylists=True, persistentIDMapping=None):
    """ Create XSP playlist(s) from the parser result queryTree, returns a list of tuples (playlist_name, xml_content)
    :param str name: the new name of the playlist
    :param dict queryTree: the result of the parser
    :param bool createSubplaylists: if true subplaylists are created for nested rules/query, if false nestes rules are ommited
    :param persistentIDMapping: Optional, necessary for rules containing other playlists
    :return: list of tuples: (playlist_name, xml_content)
    :rtype: list
    """
    
    if persistentIDMapping is None:
        persistentIDMapping = {}
        
        
    t = queryTree["fulltree"]
    
    if not t:
        raise EmptyPlaylistException("Playlist is empty", name)
    
    if "and" in t:
        globalmatch = "and"
    else:
        globalmatch = "or"
    
    
    f = _minimize(_combineRules(t, persistentIDMapping))

    if f:
        y = _convertRule(f)
        if len(y) == 3:
            # Complete doc
            globalmatch, rules, subplaylists = y
        else:
            # Only one rule
            globalmatch = "and"
            rules = y
            subplaylists = []
            
            
    else:
        raise PlaylistException("Playlist is completely incompatible", name)
        
    limit = ('    <limit>%d</limit>' % t['number']) if 'number' in t else ''
    order = ""
    if 'order' in t:
        if t["order"] == "RANDOM()":
            order = '    <order>random</order>'
        elif t["order"] in xsp_sorting:
            order = '    <order direction="%s">%s</order>' % xsp_sorting[t["order"]]
    
    meta = limit + '\n' + order
    
    r = []
    if createSubplaylists:
        for sub_globalmatch, sub_rules in subplaylists:
            sub_name = "zzzsub_"+hashlib.md5(sub_rules.encode('utf-8')).hexdigest()
            subdocument = xml_doc.format(dec=xml_dec, name=_escapeHTML(sub_name), globalmatch=xsp_operators[sub_globalmatch], rules=sub_rules, meta="")
            rules += "\n" + xml_rule.format(field="playlist", operator="is", values=xml_value.format(value=_escapeHTML(sub_name)))
            r.append((sub_name, subdocument))
    
    
    document = xml_doc.format(dec=xml_dec, name=_escapeHTML(name), globalmatch=xsp_operators[globalmatch], rules=rules, meta=meta)
    
    r.append((name, document))
    
    
    return r

def _combineRules(obj, persistentIDMapping=[]):
    """Remove incompatible rules and combine similar rules"""
    if "and" in obj or "or" in obj:
        result = []
        for operator in obj:
            t = (operator, [])
            for x in obj[operator]:
                y = _combineRules(x, persistentIDMapping)
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
                print("!!! Playlist depends on playlist '%s' !!!" % obj["value"])
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

def _convertRule(obj, depth=0, docs=[]):
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
        raise Exception("Unkown obj type")
    
if __name__ == '__main__':
    x = {'onlychecked': False, 'liveupdate': True, 'tree': {'and': [('MediaKind', "(MediaKind = 'Music')"), {'or': [('PlaylistPersistentID', "(PlaylistPersistentID = '11CCD9014365426D')"), ('Artist', "(lower(Artist) LIKE '%2pac%')"), ('Artist', "(lower(Artist) LIKE '%50 cent%')"), ('Artist', "(lower(Artist) LIKE '%7 days of funk%')"), ('Artist', "(lower(Artist) LIKE '%a3bandas%')"), ('Artist', "(lower(Artist) LIKE '%aceyalone%')"), ('Artist', "(lower(Artist) LIKE '%ace hood%')"), ('Artist', "(lower(Artist) LIKE '%aesop rock%')"), ('Artist', "(lower(Artist) LIKE '%advanced chemistry%')"), ('Artist', "(lower(Artist) LIKE '%armand hammer%')"), ('Artist', "(lower(Artist) LIKE '%aminé%')"), ('Artist', "(lower(Artist) LIKE '%apollo brown%')"), ('Artist', "(lower(Artist) LIKE '%ras kass%')"), ('Artist', "(lower(Artist) LIKE '%atmosphere%')"), ('Artist', "(lower(Artist) LIKE '%awon%')"), ('Artist', "(lower(Artist) LIKE '%a$ap%')"), ('Artist', "(lower(Artist) LIKE '%azealia banks%')"), ('Artist', "(lower(Artist) LIKE '%baby bash%')"), ('Artist', "(lower(Artist) LIKE '%barrie gledden, steve dymond, jason pedder, jason leggett%')"), ('Artist', "(lower(Artist) LIKE '%beastie boys%')"), ('Artist', "(lower(Artist) = 'beginner')"), ('Artist', "(lower(Artist) LIKE '%benevolent%')"), ('Artist', "(lower(Artist) LIKE '%big baby gandhi%')"), ('Artist', "(lower(Artist) LIKE '%big daddy kane%')"), ('Artist', "(lower(Artist) LIKE '%big narstie%')"), ('Artist', "(lower(Artist) LIKE '%big l%')"), ('Artist', "(lower(Artist) LIKE '%big pun%')"), ('Artist', "(lower(Artist) LIKE '%bigz%')"), ('Artist', "(lower(Artist) LIKE '%bike for three!%')"), ('Artist', "(lower(Artist) LIKE '%billy woods%')"), ('Artist', "(lower(Artist) LIKE '%binary star%')"), ('Artist', "(lower(Artist) LIKE '%biz markie%')"), ('Artist', "(lower(Artist) LIKE '%blackalicious%')"), ('Artist', "(lower(Artist) LIKE '%black milk%')"), ('Artist', "(lower(Artist) LIKE '%bliss n eso%')"), ('Artist', "(lower(Artist) LIKE '%b.o.b.%')"), ('Artist', "(lower(Artist) LIKE '%bone thugs-n-harmony%')"), ('Artist', "(lower(Artist) LIKE '%b real%')"), ('Artist', "(lower(Artist) LIKE '%cam'ron%')"), ('Artist', "(lower(Artist) LIKE '%canibus%')"), ('Artist', "(lower(Artist) LIKE '%capone%')"), ('Artist', "(lower(Artist) LIKE '%cardi b%')"), ('Artist', "(lower(Artist) LIKE '%chamillionaire%')"), ('Artist', "(lower(Artist) LIKE '%chance the rapper%')"), ('Artist', "(lower(Artist) LIKE '%chef'special%')"), ('Artist', "(lower(Artist) LIKE '%chiddy bang%')"), ('AlbumArtist', "(lower(AlbumArtist) = 'chip')"), ('Artist', "(lower(Artist) LIKE '%clipping%')"), ('Artist', "(lower(Artist) = 'common')"), ('Artist', "(lower(Artist) LIKE '%common sense%')"), ('Artist', "(lower(Artist) = 'cro')"), ('Artist', "(lower(Artist) LIKE '%cunninlynguists%')"), ('Artist', "(lower(Artist) LIKE '%cypress hill%')"), ('Artist', "(lower(Artist) LIKE '%danger doom%')"), ('Artist', "(lower(Artist) LIKE '%danny brown%')"), ('Artist', "(lower(Artist) LIKE '%death grips%')"), ('Artist', "(lower(Artist) LIKE '%dephlow%')"), ('Artist', "(lower(Artist) LIKE '%de la soul%')"), ('Artist', "(lower(Artist) LIKE '%dessa%')"), ('Artist', "(lower(Artist) LIKE '%die antwoord%')"), ('Artist', "(lower(Artist) LIKE '%digable planets%')"), ('Artist', "(lower(Artist) LIKE '%digital underground%')"), ('Artist', "(lower(Artist) LIKE '%divine nimbus%')"), ('Artist', "(lower(Artist) LIKE '%dilated peoples%')"), ('Artist', "(lower(Artist) LIKE '%dizzee rascal%')"), ('Artist', "(lower(Artist) LIKE '%dizzy wright%')"), ('Artist', "(lower(Artist) LIKE '%dj nasty%')"), ('Artist', "(lower(Artist) LIKE '%dj shadow%')"), ('Artist', "(lower(Artist) LIKE '%dmx%')"), ('Artist', "(lower(Artist) LIKE '%double o' ryderz%')"), ('Artist', "(lower(Artist) LIKE '%dominique young unique%')"), ('Artist', "(lower(Artist) LIKE '%dr. dre%')"), ('Artist', "(lower(Artist) LIKE '%dr. octagon%')"), ('Artist', "(lower(Artist) LIKE '%dr. yen lo%')"), ('Artist', "(lower(Artist) LIKE '%duenday%')"), ('Artist', "(lower(Artist) LIKE '%dzk%')"), ('Artist', "(lower(Artist) LIKE '%e-40%')"), ('Artist', "(lower(Artist) LIKE '%east side boyz%')"), ('Artist', "(lower(Artist) LIKE '%ed o.g. & da bulldogs%')"), ('Artist', "(lower(Artist) LIKE '%earl sweatshirt%')"), ('Artist', "(lower(Artist) LIKE '%eminem%')"), ('Artist', "(lower(Artist) LIKE '%emotionz%')"), ('Artist', "(lower(Artist) LIKE '%equipto%')"), ('Artist', "(lower(Artist) LIKE '%eve feat. gwen stefani%')"), {'and': [('Artist', "(lower(Artist) LIKE '%everlast%')"), ('Artist', "(lower(Artist) NOT LIKE '%santana%')")]}, ('Artist', "(lower(Artist) LIKE '%fat boys%')"), ('Artist', "(lower(Artist) LIKE '%fat joe%')"), ('Artist', "(lower(Artist) LIKE '%fatman scoop%')"), ('Artist', "(lower(Artist) LIKE '%the fearless four%')"), ('Artist', "(lower(Artist) LIKE '%fort minor%')"), ('Artist', "(lower(Artist) LIKE '%freak nasty%')"), ('Artist', "(lower(Artist) LIKE '%french montana%')"), ('Artist', "(lower(Artist) LIKE '%funky four + 1%')"), ('Artist', "(lower(Artist) LIKE '%the game%')"), ('Artist', "(lower(Artist) LIKE '%gang gang dance%')"), ('Artist', "(lower(Artist) LIKE '%gang starr%')"), ('Artist', "(lower(Artist) LIKE '%gavlyn%')"), ('Artist', "(lower(Artist) LIKE '%get 'em mamis%')"), ('Artist', "(lower(Artist) LIKE '%geto boys%')"), ('Artist', "(lower(Artist) LIKE '%ghostface killah%')"), ('Artist', "(lower(Artist) LIKE '%gnarls barkley%')"), {'and': [('Artist', "(lower(Artist) LIKE '%golden brahams%')"), ('Genre', "(lower(Genre) LIKE '%hip%')")]}, ('Artist', "(lower(Artist) LIKE '%gorillaz%')"), ('Artist', "(lower(Artist) LIKE '%g-side%')"), ('Artist', "(lower(Artist) LIKE '%grand analog%')"), ('Artist', "(lower(Artist) LIKE '%grandmaster flash%')"), ('Artist', "(lower(Artist) LIKE '%grieves%')"), ('Artist', "(lower(Artist) LIKE '%g-unit%')"), ('Artist', "(lower(Artist) LIKE '%gym class heroes%')"), ('Artist', "(lower(Artist) LIKE '%heavy d%')"), ('Artist', "(lower(Artist) LIKE '%the high and mighty%')"), ('Artist', "(lower(Artist) LIKE '%hilltop hoods%')"), ('Artist', "(lower(Artist) LIKE '%hoodie allen%')"), ('Artist', "(lower(Artist) LIKE '%hodgy%')"), ('Artist', "(lower(Artist) LIKE '%cønsept%')"), ('Artist', "(lower(Artist) LIKE '%house of pain%')"), ('Artist', "(lower(Artist) LIKE '%hudson mohawke%')"), ('Artist', "(lower(Artist) LIKE '%hush%')"), ('Artist', "(lower(Artist) LIKE '%iamsu%')"), ('Artist', "(lower(Artist) LIKE '%ice cube%')"), ('Artist', "(lower(Artist) LIKE '%iggy azalea%')"), ('Artist', "(lower(Artist) LIKE '%ill bill%')"), ('Artist', "(lower(Artist) LIKE '%immortal technique%')"), ('Artist', "(lower(Artist) LIKE '%injury reserve%')"), ('Artist', "(lower(Artist) LIKE '%the internet%')"), ('Artist', "(lower(Artist) LIKE '%ivy sole%')"), ('Artist', "(lower(Artist) LIKE '%jadakiss%')"), ('Artist', "(lower(Artist) LIKE '%jay-z%')"), ('Artist', "(lower(Artist) LIKE '%jazz spastiks & junclassic%')"), ('Artist', "(lower(Artist) LIKE '%jazzy jeff & the fresh prince%')"), ('Artist', "(lower(Artist) LIKE '%jc subliminal%')"), ('Artist', "(lower(Artist) LIKE '%jimmy spicer%')"), {'and': [('Artist', "(lower(Artist) LIKE '%jinx%')"), ('Genre', "(lower(Genre) LIKE '%hip%')")]}, ('Artist', "(lower(Artist) LIKE '%j.j. fad%')"), ('Artist', "(lower(Artist) LIKE '%j-love%')"), ('Artist', "(lower(Artist) LIKE '%jon young%')"), ('Artist', "(lower(Artist) LIKE '%the juggaknots%')"), ('Artist', "(lower(Artist) LIKE '%kanye west%')"), ('Artist', "(lower(Artist) LIKE '%kendrick lamar%')"), ('Artist', "(lower(Artist) LIKE '%kerser%')"), ('Artist', "(lower(Artist) LIKE '%k.flay%')"), ('Artist', "(lower(Artist) LIKE '%kid cudi%')"), ('Artist', "(lower(Artist) LIKE '%kid n play%')"), ('Artist', "(lower(Artist) LIKE '%kill the vultures%')"), ('Artist', "(lower(Artist) LIKE '%the knux%')"), ('Artist', "(lower(Artist) LIKE '%kool keith%')"), ('Artist', "(lower(Artist) LIKE '%krs-one%')"), ('Artist', "(lower(Artist) LIKE '%kurdo%')"), ('Artist', "(lower(Artist) LIKE '%kurtis blow%')"), ('Artist', "(lower(Artist) LIKE '%lauryn hill%')"), ('Artist', "(lower(Artist) LIKE '%ll cool j%')"), ('Artist', "(lower(Artist) LIKE '%the lox%')"), ('Artist', "(lower(Artist) LIKE '%lupe fiasco%')"), ('Artist', "(lower(Artist) LIKE '%kanye west%')"), ('Artist', "(lower(Artist) LIKE '%the knux%')"), ('Artist', "(lower(Artist) LIKE '%lil wayne%')"), ('Artist', "(lower(Artist) LIKE '%lil jon%')"), ('Artist', "(lower(Artist) LIKE '%little simz%')"), ('Artist', "(lower(Artist) LIKE '%lloyd banks%')"), ('Artist', "(lower(Artist) LIKE '%l'orange%')"), ('Artist', "(lower(Artist) LIKE '%lucky luciano%')"), ('Artist', "(lower(Artist) LIKE '%lupe fiasco%')"), ('Artist', "(lower(Artist) LIKE '%lyrics born%')"), ('Artist', "(lower(Artist) LIKE '%macklemore & ryan lewis%')"), ('Artist', "(lower(Artist) LIKE '%madcon%')"), ('Artist', "(lower(Artist) LIKE '%malow mac%')"), ('Artist', "(lower(Artist) LIKE '%major lazer%')"), ('Artist', "(lower(Artist) LIKE '%machine gun kelly%')"), ('Artist', "(lower(Artist) LIKE '%mantra%')"), ('Artist', "(lower(Artist) LIKE '%marley marl%')"), ('Artist', "(lower(Artist) LIKE '%mattafix%')"), ('Artist', "(lower(Artist) LIKE '%¡mayday!%')"), ('Artist', "(lower(Artist) LIKE '%metro boomin%')"), ('Artist', "(lower(Artist) LIKE '%meridian dan%')"), ('Artist', "(lower(Artist) LIKE '%mgk%')"), ('Artist', "(lower(Artist) LIKE '%mims%')"), ('Artist', "(lower(Artist) LIKE '%mobb deep%')"), ('Artist', "(lower(Artist) LIKE '%more than lights%')"), ('Artist', "(lower(Artist) LIKE '%mount cyanide%')"), ('Artist', "(lower(Artist) LIKE '%mr. capone-e%')"), ('Artist', "(lower(Artist) LIKE '%mr. criminal%')"), ('Artist', "(lower(Artist) LIKE '%mr.dero & klumzy tung%')"), ('Artist', "(lower(Artist) LIKE '%mr. muthafuckin' exquire%')"), {'and': [('Artist', "(lower(Artist) LIKE '%nas%')"), ('Artist', "(lower(Artist) NOT LIKE '%nash%')"), ('Artist', "(lower(Artist) NOT LIKE '%nass%')"), ('Artist', "(lower(Artist) NOT LIKE '%nasty%')")]}, ('Artist', "(lower(Artist) LIKE '%nate dogg%')"), ('Artist', "(lower(Artist) LIKE '%naughty by nature%')"), ('Artist', "(lower(Artist) LIKE '%nelly%')"), ('Artist', "(lower(Artist) LIKE '%noname%')"), ('Artist', "(lower(Artist) LIKE '%the notorious b.i.g.%')"), ('Artist', "(lower(Artist) LIKE '%n.w.a.%')"), ('Artist', "(lower(Artist) LIKE '%o'neal mcknight%')"), ('Artist', "(lower(Artist) LIKE '%onyx%')"), ('Artist', "(lower(Artist) LIKE '%otayo dubb%')"), ('Artist', "(lower(Artist) LIKE '%pacewon%')"), ('Artist', "(lower(Artist) LIKE '%peebs the prophet%')"), ('Artist', "(lower(Artist) LIKE '%people under the stairs%')"), ('Artist', "(lower(Artist) LIKE '%pete rock%')"), ('Artist', "(lower(Artist) LIKE '%phife dawg%')"), ('Artist', "(lower(Artist) LIKE '%puff daddy%')"), ('Artist', "(lower(Artist) LIKE '%pregnant boy%')"), ('Artist', "(lower(Artist) = 'prez')"), ('Artist', "(lower(Artist) = 'priest')"), ('Artist', "(lower(Artist) LIKE '%princess nokia%')"), ('Artist', "(lower(Artist) LIKE '%proof%')"), ('Artist', "(lower(Artist) LIKE '%prop dylan%')"), ('Artist', "(lower(Artist) LIKE '%public enemy%')"), ('Artist', "(lower(Artist) LIKE '%queen latifah%')"), ('Artist', "(lower(Artist) LIKE '%qwel and maker%')"), ('Artist', "(lower(Artist) LIKE '%rakim%')"), ('Artist', "(lower(Artist) LIKE '%rebeca lane%')"), ('Artist', "(lower(Artist) LIKE '%rhymefest%')"), ('Artist', "(lower(Artist) LIKE '%riff raff%')"), ('Artist', "(lower(Artist) LIKE '%rizzle kicks%')"), ('Artist', "(lower(Artist) LIKE '%rob base & dj e-z rock%')"), ('Artist', "(lower(Artist) LIKE '%robyn%')"), ('Artist', "(lower(Artist) LIKE '%roc marciano%')"), ('Artist', "(lower(Artist) LIKE '%roll deep%')"), ('Artist', "(lower(Artist) LIKE '%the roots%')"), ('Artist', "(lower(Artist) LIKE '%run-d.m.c.%')"), ('Artist', "(lower(Artist) LIKE '%salt-n-pepa%')"), ('Artist', "(lower(Artist) LIKE '%salt'n'pepa%')"), ('Artist', "(lower(Artist) LIKE '%sara hebe%')"), ('Artist', "(lower(Artist) LIKE '%scarface%')"), ('Artist', "(lower(Artist) LIKE '%sirkle of sound%')"), ('Artist', "(lower(Artist) LIKE '%shirt%')"), ('Artist', "(lower(Artist) LIKE '%slick rick%')"), ('Artist', "(lower(Artist) LIKE '%snoop dogg%')"), ('Artist', "(lower(Artist) LIKE '%spit syndicate%')"), ('Artist', "(lower(Artist) LIKE '%stalley%')"), ('Artist', "(lower(Artist) LIKE '%styles of beyond%')"), ('Artist', "(lower(Artist) LIKE '%the sugar hill gang%')"), ('Artist', "(lower(Artist) LIKE '%the sugarhill gang%')"), ('Artist', "(lower(Artist) LIKE '%suni clay%')"), ('Artist', "(lower(Artist) LIKE '%supar novar%')"), ('Artist', "(lower(Artist) LIKE '%sweatshop union%')"), ('Artist', "(lower(Artist) LIKE '%swollen members%')"), ('Artist', "(lower(Artist) LIKE '%terror squad%')"), ('Artist', "(lower(Artist) LIKE '%three loco%')"), ('Artist', "(lower(Artist) LIKE '%tiff the gift%')"), ('Artist', "(lower(Artist) LIKE '%t.i.%')"), ('Artist', "(lower(Artist) LIKE '%tor cesay%')"), ('Artist', "(lower(Artist) LIKE '%tor cesay ft seanie t%')"), ('Artist', "(lower(Artist) LIKE '%t-ski valley%')"), ('Artist', "(lower(Artist) LIKE '%a tribe called quest%')"), ('Artist', "(lower(Artist) LIKE '%the treacherous three%')"), ('Artist', "(lower(Artist) LIKE '%tyler, the creator%')"), ('AlbumArtist', "(lower(AlbumArtist) = 'u-god')"), ('Artist', "(lower(Artist) LIKE '%ugly heroes%')"), ('Artist', "(lower(Artist) LIKE '%vanilla ice%')"), ('Artist', "(lower(Artist) LIKE '%vel the wonder%')"), ('Artist', "(lower(Artist) LIKE '%vel ft. the herbalistics%')"), ('Artist', "(lower(Artist) LIKE '%vince staples%')"), ('Artist', "(lower(Artist) LIKE '%warren g%')"), ('Artist', "(lower(Artist) LIKE '%watsky%')"), ('Artist', "(lower(Artist) LIKE '%wax%')"), ('Artist', "(lower(Artist) LIKE '%wu-tang clan%')"), ('Artist', "(lower(Artist) LIKE '%yfn lucci%')"), ('Artist', "(lower(Artist) LIKE '%young m.c.%')"), ('Album', "(lower(Album) = 'the southcoast soulshine ep')")]}]}, 'fulltree': {'and': [{'field': 'MediaKind', 'type': 'mediakind', 'operator': 'is', 'value': 'Music'}, {'or': [{'field': 'PlaylistPersistentID', 'type': 'playlist', 'operator': 'is', 'value': '11CCD9014365426D'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': '2Pac'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': '50 Cent'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': '7 Days of Funk'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'A3Bandas'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Aceyalone'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Ace Hood'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Aesop Rock'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Advanced Chemistry'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Armand Hammer'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Aminé'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Apollo Brown'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Ras Kass'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Atmosphere'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Awon'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'A$AP'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Azealia Banks'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Baby Bash'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Barrie Gledden, Steve Dymond, Jason Pedder, Jason Leggett'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Beastie Boys'}, {'field': 'Artist', 'type': 'string', 'operator': 'is', 'value': 'Beginner'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Benevolent'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Big Baby Gandhi'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Big Daddy Kane'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Big Narstie'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Big L'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Big Pun'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Bigz'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Bike For Three!'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Billy Woods'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Binary Star'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Biz Markie'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Blackalicious'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Black Milk'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Bliss n Eso'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'B.O.B.'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Bone thugs-n-harmony'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'B Real'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': "Cam'ron"}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Canibus'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Capone'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Cardi B'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Chamillionaire'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Chance The Rapper'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': "Chef'Special"}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Chiddy Bang'}, {'field': 'AlbumArtist', 'type': 'string', 'operator': 'is', 'value': 'Chip'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'clipping'}, {'field': 'Artist', 'type': 'string', 'operator': 'is', 'value': 'Common'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Common Sense'}, {'field': 'Artist', 'type': 'string', 'operator': 'is', 'value': 'Cro'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'CunninLynguists'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Cypress Hill'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Danger Doom'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Danny Brown'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Death Grips'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Dephlow'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'De La Soul'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Dessa'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Die Antwoord'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Digable Planets'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Digital Underground'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Divine Nimbus'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Dilated Peoples'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Dizzee Rascal'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Dizzy Wright'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'DJ Nasty'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'DJ Shadow'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'DMX'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': "Double O' Ryderz"}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Dominique Young Unique'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Dr. Dre'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Dr. Octagon'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Dr. Yen Lo'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Duenday'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'DZK'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'E-40'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'East Side Boyz'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Ed O.G. & Da Bulldogs'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Earl Sweatshirt'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Eminem'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Emotionz'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Equipto'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Eve Feat. Gwen Stefani'}, {'and': [{'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Everlast'}, {'field': 'Artist', 'type': 'string', 'operator': 'not like', 'value': 'Santana'}]}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Fat Boys'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Fat Joe'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Fatman Scoop'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'The Fearless Four'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Fort Minor'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Freak Nasty'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'French Montana'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Funky Four + 1'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'The Game'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Gang Gang Dance'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Gang Starr'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Gavlyn'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': "Get 'Em Mamis"}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Geto Boys'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Ghostface Killah'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Gnarls Barkley'}, {'and': [{'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Golden Brahams'}, {'field': 'Genre', 'type': 'string', 'operator': 'like', 'value': 'Hip'}]}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Gorillaz'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'G-Side'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Grand Analog'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Grandmaster Flash'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Grieves'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'G-Unit'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Gym Class Heroes'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Heavy D'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'The High and Mighty'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Hilltop Hoods'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Hoodie Allen'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Hodgy'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'CØNSEPT'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'House Of Pain'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Hudson Mohawke'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Hush'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Iamsu'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Ice Cube'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Iggy Azalea'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Ill Bill'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Immortal Technique'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Injury Reserve'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'The Internet'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Ivy Sole'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Jadakiss'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Jay-Z'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Jazz Spastiks & Junclassic'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Jazzy Jeff & The Fresh Prince'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Jc Subliminal'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Jimmy Spicer'}, {'and': [{'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Jinx'}, {'field': 'Genre', 'type': 'string', 'operator': 'like', 'value': 'Hip'}]}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'J.J. Fad'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'J-Love'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Jon Young'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'The Juggaknots'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Kanye West'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Kendrick Lamar'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Kerser'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'K.Flay'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Kid Cudi'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Kid N Play'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Kill the Vultures'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'The Knux'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Kool Keith'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Krs-One'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Kurdo'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Kurtis Blow'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Lauryn Hill'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'LL Cool J'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'The LOX'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Lupe Fiasco'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Kanye West'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'The Knux'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Lil Wayne'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Lil Jon'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Little Simz'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Lloyd Banks'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': "L'Orange"}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Lucky Luciano'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Lupe Fiasco'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Lyrics Born'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Macklemore & Ryan Lewis'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Madcon'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Malow Mac'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Major Lazer'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Machine Gun Kelly'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Mantra'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Marley Marl'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Mattafix'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': '¡MAYDAY!'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Metro Boomin'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Meridian Dan'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'MGK'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Mims'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Mobb Deep'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'More Than Lights'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Mount Cyanide'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Mr. Capone-E'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Mr. Criminal'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Mr.Dero & Klumzy Tung'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': "Mr. Muthafuckin' eXquire"}, {'and': [{'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Nas'}, {'field': 'Artist', 'type': 'string', 'operator': 'not like', 'value': 'Nash'}, {'field': 'Artist', 'type': 'string', 'operator': 'not like', 'value': 'Nass'}, {'field': 'Artist', 'type': 'string', 'operator': 'not like', 'value': 'Nasty'}]}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Nate Dogg'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Naughty By Nature'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Nelly'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Noname'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'The Notorious B.I.G.'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'N.W.A.'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': "O'Neal McKnight"}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Onyx'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Otayo Dubb'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Pacewon'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Peebs The Prophet'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'People Under The Stairs'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Pete Rock'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Phife Dawg'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Puff Daddy'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Pregnant Boy'}, {'field': 'Artist', 'type': 'string', 'operator': 'is', 'value': 'Prez'}, {'field': 'Artist', 'type': 'string', 'operator': 'is', 'value': 'Priest'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Princess Nokia'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Proof'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Prop Dylan'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Public Enemy'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Queen Latifah'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Qwel and Maker'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Rakim'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Rebeca Lane'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Rhymefest'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'RiFF RAFF'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Rizzle Kicks'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Rob Base & DJ E-Z Rock'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Robyn'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Roc Marciano'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Roll Deep'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'The Roots'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Run-D.M.C.'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Salt-N-Pepa'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': "Salt'N'Pepa"}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Sara Hebe'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Scarface'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Sirkle Of Sound'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Shirt'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Slick Rick'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Snoop Dogg'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Spit Syndicate'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Stalley'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Styles of Beyond'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'The Sugar Hill Gang'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'The Sugarhill Gang'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Suni Clay'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Supar Novar'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Sweatshop Union'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Swollen Members'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Terror Squad'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Three Loco'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Tiff The Gift'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'T.I.'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Tor Cesay'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Tor Cesay ft Seanie T'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'T-Ski Valley'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'A Tribe Called Quest'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'The Treacherous Three'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Tyler, The Creator'}, {'field': 'AlbumArtist', 'type': 'string', 'operator': 'is', 'value': 'U-God'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Ugly Heroes'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Vanilla Ice'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Vel The Wonder'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Vel ft. The Herbalistics'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Vince Staples'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Warren G'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Watsky'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Wax'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Wu-Tang Clan'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'YFN Lucci'}, {'field': 'Artist', 'type': 'string', 'operator': 'like', 'value': 'Young M.C.'}, {'field': 'Album', 'type': 'string', 'operator': 'is', 'value': 'The Southcoast Soulshine Ep'}]}]}}
    
    createXSP("Hip-Hop", x)
