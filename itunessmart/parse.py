#! /usr/bin/env python3
import base64
import datetime
from enum import IntEnum
import json
import struct

class FileKind:
    def __init__(self, name, extension):
        self.name = name
        self.extension = extension

FileKinds = [
    FileKind("Protected AAC audio file", ".m4p"),
    FileKind("MPEG audio file", ".mp3"),
    FileKind("AIFF audio file", ".aiff"),
    FileKind("WAV audio file", ".wav"),
    FileKind("QuickTime movie file", ".mov"),
    FileKind("MPEG-4 video file", ".mp4"),
    FileKind("AAC audio file", ".m4a")
];

MediaKinds = {
        0x01 : "Music",
        0x02 : "Movie",
        0x04 : "Podcast",
        0x08 : "Audiobook",
        0x20 : "Music Video",
        0x40 : "TV Show",
       0x400 : "Home Video",
     0x10000 : "iTunes Extras",
    0x100000 : "Voice Memo",
    0x200000 : "iTunes U",
    0xC00000 : "Book",
    # TODO mediakinds of toplevel playlists
    # The following are only used in the toplevel playlists: Music, TV Shows, Movies and Books 
    # (These playlists can be selected with the arrows or from a dropdown menu in iTunes 12)
    # Theses Media Kinds cannot be selected by the user. I am unsure about their meaning.
    0xC00008 : "Book or Audiobook", # TODO My guess: This contains Books and Audiobooks
    0x1021B1 : "Music", # TODOMy guess: This is similar to Music
    0x208004 : "Undesired Music", # TODO My guess: This is some kind of Music that should not appear in the toplevel playlist
    0x20A004 : "Undesired Other" # TODO My guess: This is something (other than music) that should not appear in the toplevel playlist
}

iCloudStatus = {
    0x01 : "Purchased",
    0x02 : "Matched",
    0x03 : "Uploaded",
    0x04 : "Ineligible",
    0x05 : "Local Only",
    0x07 : "Duplicate"
}

LocationKinds = {
    0x01 : "Computer",
    0x10 : "iCloud"
}

SelectionMethodsStrings = {
    "Random" :["random","RANDOM()"],
    "Name" :["Name","SortName"],
    "Album" :["album","SortAlbum"],
    "Artist" :["artist","SortArtist"],
    "Genre" :["genre","Genre"],
    "HighestRating" :["highest rated", "Rating DESC"],
    "LowestRating" :["lowest rated","Rating ASC"],
    "RecentlyPlayed" :[["most recently played", "least recently played"],["LastPlayed DESC", "LastPlayed ASC"]],
    "OftenPlayed" :[["most often played", "least often played"],["Plays DESC", "Plays ASC"]],
    "RecentlyAdded" :[["most recently added", "least recently added"],["DateAdded DESC", "DateAdded ASC"]]
}

DateStartFromUnix = -2082844800

class LimitMethods(IntEnum):
    """The methods by which the number of songs in a playlist are limited"""
    Minutes = 0x01
    MB = 0x02
    Items = 0x03
    Hours = 0x04
    GB = 0x05

class SelectionMethods(IntEnum):
    """The methods by which songs are selected for inclusion in a limited playlist"""
    Random = 0x02
    Name = 0x05
    Album = 0x06
    Artist = 0x07
    Genre = 0x09
    HighestRating = 0x1c
    LowestRating = 0x01
    RecentlyPlayed = 0x1a
    OftenPlayed = 0x19
    RecentlyAdded = 0x15

class StringFields(IntEnum):
    """The matching criteria which take string data"""
    Album = 0x03
    AlbumArtist = 0x47
    Artist = 0x04
    Category = 0x37
    Comments = 0x0e
    Composer = 0x12
    Description = 0x36
    Genre = 0x08
    Grouping = 0x27
    Kind = 0x09
    Name = 0x02
    Show = 0x3e
    SortAlbum = 0x4f
    SortAlbumartist = 0x51
    SortComposer = 0x52
    SortName = 0x4e
    SortShow = 0x53
    VideoRating = 0x59

class IntFields(IntEnum):
    """The matching criteria which take integer data"""
    BPM = 0x23
    BitRate = 0x05
    Compilation = 0x1f
    DiskNumber = 0x18
    Plays = 0x16
    Rating = 0x19
    Podcast = 0x39
    SampleRate = 0x06
    Season = 0x3f
    Size = 0x0c
    Skips = 0x44
    Duration = 0x0d
    TrackNumber = 0x0b
    Year = 0x07

class BooleanFields(IntEnum):
    """The matching criteria which take boolean data"""
    HasArtwork = 0x25
    Purchased = 0x29
    Checked = 0x1d

class DateFields(IntEnum):
    """The matching criteria which take date data"""
    DateAdded = 0x10
    DateModified = 0x0a
    LastPlayed = 0x17
    LastSkipped = 0x45

class MediaKindFields(IntEnum):
    """The matching criteria which take a Media Kind, as defined above"""
    MediaKind = 0x3c

class PlaylistFields(IntEnum):
    """The matching criteria which take a Persistent Playlist ID (64bit)"""
    PlaylistPersistentID = 0x28

class CloudFields(IntEnum):
    """The matching criteria which take a Persistent Playlist ID (64bit)"""
    iCloudStatus = 0x86

class LocationFields(IntEnum):
    """The matching criteria which take a Location, as defined above"""
    Location = 0x85

class LogicSign(IntEnum):
    """The signs which apply to different kinds of logic (is vs. is not, contains vs. doesn't contain, etc.)"""
    IntPositive = 0x00
    StringPositive = 0x01
    IntNegative = 0x02
    StringNegative = 0x03

class LogicRule(IntEnum):
    """The logical rules"""
    Other = 0x00
    Is = 0x01
    Contains = 0x02
    Starts = 0x04
    Ends = 0x08
    Greater = 0x10
    Less = 0x40

class Offset(IntEnum):
    INTLENGTH = 67;           # The length on a int criteria starting at the first int
    SUBEXPRESSIONLENGTH = 192 # The length of a subexpression starting from FIELD

    # INFO OFFSETS
    # Offsets for bytes which...
    LIVEUPDATE = 0           # determin whether live updating is enabled - Absolute offset
    MATCHBOOL = 1            # determin whether logical matching is to be performed - Absolute offset
    LIMITBOOL = 2            # determin whether results are limited - Absolute offset
    LIMITMETHOD = 3          # determin by what criteria the results are limited - Absolute offset
    SELECTIONMETHOD = 7      # determin by what criteria limited playlists are populated - Absolute offset
    LIMITINT = 8             # determin the limited - Absolute offset
    LIMITCHECKED = 12        # determin whether to exclude unchecked items - Absolute offset
    SELECTIONMETHODSIGN = 13 # determin whether certain selection methods are "most" or "least" - Absolute offset

    # CRITERIA OFFSETS
    # Offsets for bytes which...
    LOGICTYPE = 15    # determin whether all or any criteria must match - Absolute offset
    FIELD = 139       # determin what is being matched (Artist, Album, &c) - Absolute offset
    LOGICSIGN = 1     # determin whether the matching rule is positive or negative (e.g., is vs. is not) - Relative offset from FIELD
    LOGICRULE = 4     # determin the kind of logic used (is, contains, begins, &c) - Relative offset from FIELD
    STRING = 54       # begin string data - Relative offset from FIELD
    INTA = 57         # begin the first int - Relative offset from FIELD
    INTB = 24         # begin the second int - Relative offset from INTA
    TIMEMULTIPLE = 73 # begin the int with the multiple of time - Relative offset from FIELD
    TIMEVALUE = 65    # begin the inverse int with the value of time - Relative offset from FIELD
    SUBLOGICTYPE = 68 # determin whether all or any criteria must match - Relative offset from FIELD
    SUBINT = 61       # begin the first int - Relative offset from FIELD

class SmartPlaylistParser:
    def __init__(self, datastr_info=None, datastr_criteria=None):
        if datastr_info and datastr_criteria:
          self.str_data(datastr_info, datastr_criteria)

    
    def str_data(self,datastr_info, datastr_criteria):
        i = base64.standard_b64decode("".join(datastr_info.split()))
        c = base64.standard_b64decode("".join(datastr_criteria.split()))
        return self.data(i,c)
    
    def data(self,data_info, data_criteria):
        self.info = data_info
        self.criteria = data_criteria
        self.query = ""
        self.root = {}
        self.queryTree = self.root
        self.queryTreeCurrent = []
        self.fullTreeRoot = {}
        self.fullTree = self.fullTreeRoot
        self.fullTreeCurrent = []
        self.output = ""
        self.ignore = ""
        self.limit = {}

        self.subStack = []

    def parse(self):
        if not self.info or not self.data:
            raise Exception("Set smart info with data() or strdata() before running parse()")
        
        self.offset = int(Offset.FIELD)
        
        if self.info[Offset.MATCHBOOL] == 1:
            self.is_or = self.criteria[Offset.LOGICTYPE] == 1
            if self.is_or:
                self.conjunctionQuery = " OR "
                self.conjunctionOutput = ' or\n'
                self.queryTree["or"] = self.queryTreeCurrent
                self.fullTree["or"] = self.fullTreeCurrent
            else:
                self.conjunctionQuery = " AND "
                self.conjunctionOutput = ' and\n'
                self.queryTree["and"] = self.queryTreeCurrent
                self.fullTree["and"] = self.fullTreeCurrent
                
            while True:
                self.again = False

                if len(self.subStack) > 0:
                    if self.subStack[-1]["N"] == 0:
                        old = self.subStack.pop()

                        self.query = old["query"] + old["conjunctionQuery"] + "( %s )" % self.query
                        self.output = old["output"] + old["conjunctionOutput"] + "[\n\t%s\n]" % "\n\t".join(self.output.split("\n"))
    
                        self.conjunctionQuery = old["conjunctionQuery"]
                        self.conjunctionOutput = old["conjunctionOutput"]
                        self.queryTreeCurrent = old["queryTreeCurrent"]
                        self.fullTreeCurrent = old["fullTreeCurrent"]
                    else:
                        self.subStack[-1]["N"] -= 1
                
                self.logicSignOffset = self.offset + int(Offset.LOGICSIGN);
                self.logicRulesOffset = self.offset + int(Offset.LOGICRULE);
                self.stringOffset = self.offset + int(Offset.STRING);
                self.intAOffset = self.offset + int(Offset.INTA);
                self.intBOffset = self.intAOffset + int(Offset.INTB);
                self.timeMultipleOffset = self.offset + int(Offset.TIMEMULTIPLE);
                self.timeValueOffset = self.offset + int(Offset.TIMEVALUE);

                if any(self.criteria[self.offset] == e.value for e in StringFields):
                    self.ProcessStringField()
                elif any(self.criteria[self.offset] == e.value for e in IntFields):
                    self.ProcessIntField()
                elif any(self.criteria[self.offset] == e.value for e in DateFields):
                    self.ProcessDateField()
                elif any(self.criteria[self.offset] == e.value for e in BooleanFields):
                    self.ProcessBooleanField()   
                elif any(self.criteria[self.offset] == e.value for e in MediaKindFields):
                    self.ProcessMediaKindField()
                elif any(self.criteria[self.offset] == e.value for e in PlaylistFields):
                    self.ProcessPlaylistField()
                elif any(self.criteria[self.offset] == e.value for e in CloudFields):
                    self.ProcessCloudField()
                elif any(self.criteria[self.offset] == e.value for e in LocationFields):
                    self.ProcessLocationField()
                elif self.criteria[self.offset] == 0:
                    # Subexpression

                    self.is_or = self.criteria[self.offset+Offset.SUBLOGICTYPE] == 1

                    numberOfSubExpression = self._iTunesUint(self.criteria[self.offset+Offset.SUBINT:self.offset++Offset.SUBINT+4])

                    self.subStack.append({
                        "query" :  self.query,
                        "output" : self.output,
                        "N" : numberOfSubExpression,
                        "conjunctionQuery" : self.conjunctionQuery,
                        "conjunctionOutput" : self.conjunctionOutput,
                        "queryTreeCurrent" : self.queryTreeCurrent,
                        "fullTreeCurrent" : self.fullTreeCurrent,
                        })

                    newtree = {}
                    newcurrent = []
                    self.queryTreeCurrent.append(newtree)
                    
                    newfulltree = {}
                    newfulltreecurrent = []
                    self.fullTreeCurrent.append(newfulltree)
                    
                    if self.is_or:
                        self.conjunctionQuery = " OR "
                        self.conjunctionOutput = ' or\n'
                        newtree["or"] = newcurrent
                        newfulltree["or"] = newfulltreecurrent
                    else:
                        self.conjunctionQuery = " AND "
                        self.conjunctionOutput = ' and\n'
                        newtree["and"] = newcurrent
                        newfulltree["and"] = newfulltreecurrent

                    self.query = ""
                    self.output = ""
                    self.queryTreeCurrent = newcurrent
                    self.fullTreeCurrent = newfulltreecurrent
                    
                    self.offset += Offset.SUBEXPRESSIONLENGTH
                    self.again = True
                else:
                    print("Unkown field: %s" % (hex(self.criteria[self.offset])))
                    self.ignore += "Not processed"
                    print(self.criteria[self.offset:self.offset+100])

                if not self.again:
                    break

        if self.info[Offset.LIMITBOOL] == 1:
            # Limit 
            self.limit["number"] = self._iTunesUint(self.info[Offset.LIMITINT:Offset.LIMITINT+4])

            self.limit["type"] = LimitMethods(self.info[Offset.LIMITMETHOD]).name

            # Selection
            selectionmethod = SelectionMethods(self.info[Offset.SELECTIONMETHOD]).name
            sign = int(self.info[Offset.SELECTIONMETHODSIGN] == 0)
            self.limit["order"] = SelectionMethodsStrings[selectionmethod][1] if type(SelectionMethodsStrings[selectionmethod][1]) is str else SelectionMethodsStrings[selectionmethod][1][sign]
            
            
            if len(self.output) > 0:
                self.output += '\n'
            self.output += "Limited to %d %s selected by %s" % (self.limit["number"],self.limit["type"],SelectionMethodsStrings[selectionmethod][0] if type(SelectionMethodsStrings[selectionmethod][0]) is str else SelectionMethodsStrings[selectionmethod][0][sign])

        if self.info[Offset.LIMITCHECKED] == 1:
            # Exclude unchecked items 
            self.limit["onlychecked"] = True

            if len(self.output) > 0:
                self.output += '\n'
            self.output += "Exclude unchecked items"
        else:
            self.limit["onlychecked"] = False

        if self.info[Offset.LIVEUPDATE] == 0:
            # Live Update disabled
            self.limit["liveupdate"] = False

            if len(self.output) > 0:
                self.output += '\n'
            self.output += "Live updating disabled"
        else:
            self.limit["liveupdate"] = True

        t = self.limit
        t["tree"] = self.queryTree
        self.queryTree = t
        
        t2 = self.limit
        t2["fulltree"] = self.fullTree
        self.fullTree = t2
    
    def ProcessStringField(self):
        end = False
        self.fieldName = StringFields(self.criteria[self.offset]).name
        self.workingOutput = self.fieldName
        self.workingQuery = "(lower(" + self.fieldName + ")"
        self.workingFull = {"field":self.fieldName, "type":"string"}
        
        KindEval = None
        
        
        if self.criteria[self.logicRulesOffset] == LogicRule.Contains:
            if self.criteria[self.logicSignOffset] == LogicSign.StringPositive:
                self.workingOutput += " contains "
                self.workingQuery += " LIKE '%"
                self.workingFull["operator"] = "like"
            else:
                self.workingOutput += " does not contain "
                self.workingQuery += " NOT LIKE '%"
                self.workingFull["operator"] = "not like"
            if self.criteria[self.offset] == StringFields.Kind:
                KindEval = lambda kind, query: query in kind.name
            end = True

        elif self.criteria[self.logicRulesOffset] == LogicRule.Is:
            if self.criteria[self.logicSignOffset] == LogicSign.StringPositive:
                self.workingOutput += " is "
                self.workingQuery += " = '"
                self.workingFull["operator"] = "is"
            else:
                self.workingOutput += " is not "
                self.workingQuery += " != '"
                self.workingFull["operator"] = "is not"
            if self.criteria[self.offset] == StringFields.Kind:
                KindEval = lambda kind, query: query == kind.name

        elif self.criteria[self.logicRulesOffset] == LogicRule.Starts:
            self.workingOutput += " starts with "
            self.workingQuery += " Like '"
            self.workingFull["operator"] = "starts with"
            if self.criteria[self.offset] == StringFields.Kind:
                KindEval = lambda kind, query: not query in kind.name
            end = True
                        
        elif self.criteria[self.logicRulesOffset] == LogicRule.Ends:
            self.workingOutput += " ends with "
            self.workingQuery += " Like '%"
            self.workingFull["operator"] = "ends with"
            if self.criteria[self.offset] == StringFields.Kind:
                KindEval = lambda kind, query: kind.name.index(query) == len(kind.name) - len(query)
            end = True

        self.workingOutput += '"'
        self.content = ""
        onByte = True
        for i in range(self.stringOffset,len(self.criteria)):
            if onByte:
                if self.criteria[i] == 0 and i != len(self.criteria)-1:
                    self.FinishStringField(end, KindEval)
                    self.offset = i + 2
                    self.again = True
                    return
                self.content += chr(self.criteria[i])
            onByte = not onByte
        self.FinishStringField(end, KindEval)
        return

    def FinishStringField(self, end, KindEval):
        self.workingOutput += self.content
        self.workingOutput += '" '
        failed = False
        if self.criteria[self.offset] == StringFields.Kind:
            workingQuery = ""
            for kind in FileKinds:
                if KindEval(kind, self.content):
                    if len(self.workingQuery) > 0:
                        if (len(self.query) == 0 and not self.again) or self.is_or:
                            self.workingQuery += " OR "
                        else:
                            failed = True
                            break

                    self.workingQuery += "(lower(Uri)"
                    self.workingQuery += (" LIKE '%" + kind.extension + "')") if self.criteria[self.logicSignOffset] == LogicSign.StringPositive else (" NOT LIKE '%" + kind.extension + "%')")
                    self.workingFull["kind_value"] = kind.extension
                    self.workingFull["kind_operator"] = "like" if self.criteria[self.logicSignOffset] == LogicSign.StringPositive else "not like"
        else:
            self.workingQuery += self.content.lower()
            self.workingQuery += "%')" if end else "')"
            self.workingFull["value"] = self.content

        if failed:
            if len(self.ignore) > 0:
                self.ignore += self.conjunctionOutput
            self.ignore += self.workingOutput
        else:
            if len(self.output) > 0:
                self.output += self.conjunctionOutput
            self.output += self.workingOutput
            
            if len(self.query) > 0:
                self.query += self.conjunctionQuery
            self.query += self.workingQuery

            self.queryTreeCurrent.append((self.fieldName,self.workingQuery))
            self.fullTreeCurrent.append(self.workingFull)

    def ProcessIntField(self):
        self.fieldName = IntFields(self.criteria[self.offset]).name
        self.workingOutput = self.fieldName
        self.workingQuery = "(" + self.fieldName
        self.workingFull = {"field":self.fieldName, "type":"int"}
        
        if self.criteria[self.logicRulesOffset] == LogicRule.Is:
            number = self._iTunesUint(self.criteria[self.intAOffset:self.intAOffset+4], self.criteria[self.offset] == IntFields.Rating) 
            if self.criteria[self.logicSignOffset] == LogicSign.IntPositive:
                self.workingOutput += " is %d" % number
                self.workingQuery += " = %d" % number
                self.workingFull["operator"] = "is"
                self.workingFull["value"] = number
            else:
                self.workingOutput += " is not %d" % number
                self.workingQuery += " != %d" % number
                self.workingFull["operator"] = "is not"
                self.workingFull["value"] = number

        elif self.criteria[self.logicRulesOffset] == LogicRule.Greater:
            number = self._iTunesUint(self.criteria[self.intAOffset:self.intAOffset+4], self.criteria[self.offset] == IntFields.Rating) 
            self.workingOutput += " is greater than %d" % number
            self.workingQuery += " > %d" % number
            self.workingFull["operator"] = "greater than"
            self.workingFull["value"] = number
            
        elif self.criteria[self.logicRulesOffset] == LogicRule.Less:
            number = self._iTunesUint(self.criteria[self.intAOffset:self.intAOffset+4], self.criteria[self.offset] == IntFields.Rating) 
            self.workingOutput += " is less than %d" % number
            self.workingQuery += " < %d" % number
            self.workingFull["operator"] = "less than"
            self.workingFull["value"] = number
            
        elif self.criteria[self.logicRulesOffset] == LogicRule.Other:
            if self.criteria[self.logicSignOffset + 2] == 1:
                numberA = self._iTunesUint(self.criteria[self.intAOffset:self.intAOffset+4], self.criteria[self.offset] == IntFields.Rating) 
                numberB = self._iTunesUint(self.criteria[self.intBOffset:self.intBOffset+4], self.criteria[self.offset] == IntFields.Rating)
                self.workingOutput += " is in the range of %d to %d" % (numberA, numberB)
                self.workingQuery += " BETWEEN %d AND %d" % (numberA, numberB)
                self.workingFull["operator"] = "between"
                self.workingFull["value"] = (numberA, numberB)
                
            else:
                numberA = self._iTunesUint(self.criteria[self.intAOffset:self.intAOffset+4], self.criteria[self.offset] == IntFields.Rating)
                numberB = self._iTunesUint(self.criteria[self.intBOffset:self.intBOffset+4], self.criteria[self.offset] == IntFields.Rating)
                if numberA == numberB:
                    if self.criteria[self.logicSignOffset] == LogicSign.IntPositive:
                        self.workingOutput += " is %d" % numberA
                        self.workingQuery += " = %d" % numberA
                        self.workingFull["operator"] = "is"
                        self.workingFull["value"] = numberA
                    else:
                        self.workingOutput += " is not %d" % numberA
                        self.workingQuery += " != %d" % numberA
                        self.workingFull["operator"] = "is not"
                        self.workingFull["value"] = numberA
                else:
                    print("Unkown case in ProcessIntField:LogicRule.Other: a=%d and b=%d" % (numberA,numberB))
                    self.workingOutput += " ##UnkownCase IntField: LogicRule.Other##"
                    self.workingQuery += " ##UnkownCase IntField: LogicRule.Other##"

        self.workingQuery += ")"

        if len(self.output) > 0:
            self.output += self.conjunctionOutput

        if len(self.query) > 0:
            self.query += self.conjunctionQuery

        self.output += self.workingOutput
        self.query += self.workingQuery
        self.queryTreeCurrent.append((self.fieldName,self.workingQuery))
        self.fullTreeCurrent.append(self.workingFull)

        self.offset = self.intAOffset + Offset.INTLENGTH
        if len(self.criteria) > self.offset:
            self.again = True


    def ProcessMediaKindField(self):
        self.fieldName = MediaKindFields(self.criteria[self.offset]).name
        self.workingOutput = self.fieldName
        self.workingQuery = "(" + self.fieldName
        self.workingFull = {"field":self.fieldName, "type":"mediakind"}
        
        if self.criteria[self.logicRulesOffset] == LogicRule.Is:
            number = self._iTunesUint(self.criteria[self.intAOffset:self.intAOffset+4], self.criteria[self.offset] == IntFields.Rating) 
            if self.criteria[self.logicSignOffset] == LogicSign.IntPositive:
                self.workingOutput += " is %s" % MediaKinds[number]
                self.workingQuery += " = '%s'" % MediaKinds[number]
                self.workingFull["operator"] = "is"
                self.workingFull["value"] = MediaKinds[number]
                
            else:
                self.workingOutput += " is not %s" % MediaKinds[number]
                self.workingQuery += " != '%s'" % MediaKinds[number]
                self.workingFull["operator"] = "is not"
                self.workingFull["value"] = MediaKinds[number]
                
        elif self.criteria[self.logicRulesOffset] == LogicRule.Other:
            numberA = self._iTunesUint(self.criteria[self.intAOffset:self.intAOffset+4], self.criteria[self.offset] == IntFields.Rating)
            numberB = self._iTunesUint(self.criteria[self.intBOffset:self.intBOffset+4], self.criteria[self.offset] == IntFields.Rating)
            if numberA == numberB:
                if self.criteria[self.logicSignOffset] == LogicSign.IntPositive:
                    self.workingOutput += " is %s" % MediaKinds[numberA]
                    self.workingQuery += " = '%s'" % MediaKinds[numberA]
                    self.workingFull["operator"] = "is"
                    self.workingFull["value"] = MediaKinds[numberA]
                else:
                    self.workingOutput += " is not %s" % MediaKinds[numberA]
                    self.workingQuery += " != '%s'" % MediaKinds[numberA]
                    self.workingFull["operator"] = "is not"
                    self.workingFull["value"] = MediaKinds[numberA]
                    
            else:
                print("Unkown case in ProcessMediaKindField:LogicRule.Other: %d != %d" % (numberA,numberB))
                self.workingOutput += " ##UnkownCase MediaKindField: LogicRule.Other##"
                self.workingQuery += " ##UnkownCase MediaKindField: LogicRule.Other##"
        else:
            print("Unkown logic rule in ProcessMediaKindField: LogicRule=%d" % self.criteria[self.logicRulesOffset])
            self.workingOutput += " ##UnkownCase MediaKindField:LogicRule##"
            self.workingQuery += " ##UnkownCase MediaKindField:LogicRule##"

        self.workingQuery += ")"

        if len(self.output) > 0:
            self.output += self.conjunctionOutput

        if len(self.query) > 0:
            self.query += self.conjunctionQuery

        self.output += self.workingOutput
        self.query += self.workingQuery
        self.queryTreeCurrent.append((self.fieldName, self.workingQuery))
        self.fullTreeCurrent.append(self.workingFull)

        self.offset = self.intAOffset + Offset.INTLENGTH
        if len(self.criteria) > self.offset:
            self.again = True

    def ProcessPlaylistField(self):
        self.fieldName = PlaylistFields(self.criteria[self.offset]).name
        self.workingOutput = self.fieldName
        self.workingQuery = "(" + self.fieldName
        self.workingFull = {"field":self.fieldName, "type":"playlist"}
        
        if self.criteria[self.logicRulesOffset] == LogicRule.Is:
            idpart0 = self._iTunesUint(self.criteria[self.intAOffset-4:self.intAOffset], self.criteria[self.offset] == IntFields.Rating)
            idpart1 = self._iTunesUint(self.criteria[self.intAOffset:self.intAOffset+4], self.criteria[self.offset] == IntFields.Rating)
            
            if self.criteria[self.logicSignOffset] == LogicSign.IntPositive:
                self.workingOutput += " is %s%s" % (hex(idpart0)[2:].upper(), hex(idpart1)[2:].upper())
                self.workingQuery += " = '%s%s'" % (hex(idpart0)[2:].upper(), hex(idpart1)[2:].upper())
                self.workingFull["operator"] = "is"
                self.workingFull["value"] = "%s%s" % (hex(idpart0)[2:].upper(), hex(idpart1)[2:].upper())
            else:
                self.workingOutput += " is not %s%s" % (hex(idpart0)[2:].upper(), hex(idpart1)[2:].upper())
                self.workingQuery += " != '%s%s'" % (hex(idpart0)[2:].upper(), hex(idpart1)[2:].upper())
                self.workingFull["operator"] = "is not"
                self.workingFull["value"] = "%s%s" % (hex(idpart0)[2:].upper(), hex(idpart1)[2:].upper())
                
        else:
            print("Unkown logic rule in ProcessPlaylistField: LogicRule=%d" % self.criteria[self.logicRulesOffset])
            self.workingOutput += " ##UnkownCase PlaylistField:LogicRule##"
            self.workingQuery += " ##UnkownCase PlaylistField:LogicRule##"
        
        self.workingQuery += ")"

        if len(self.output) > 0:
            self.output += self.conjunctionOutput

        if len(self.query) > 0:
            self.query += self.conjunctionQuery

        self.output += self.workingOutput
        self.query += self.workingQuery
        self.queryTreeCurrent.append((self.fieldName, self.workingQuery))
        self.fullTreeCurrent.append(self.workingFull)

        self.offset = self.intAOffset + Offset.INTLENGTH
        if len(self.criteria) > self.offset:
            self.again = True

    def ProcessBooleanField(self):
        self.fieldName = BooleanFields(self.criteria[self.offset]).name
        self.workingOutput = self.fieldName
        self.workingQuery = "(" + self.fieldName
        self.workingFull = {"field":self.fieldName, "type":"boolean"}
        
        if self.criteria[self.logicRulesOffset] == LogicRule.Is:
            value = self.criteria[self.logicSignOffset] != LogicSign.IntPositive
            boolstr = "True" if value == 1 else "False"
            
            self.workingOutput += " is %s" % (boolstr)
            self.workingQuery += " = %d" % (value)
            self.workingFull["operator"] = "is"
            self.workingFull["value"] = value == 1
            
        else:
            print("Unkown logic rule in ProcessBooleanField: LogicRule=%d" % self.criteria[self.logicRulesOffset])
            self.workingOutput += " ##UnkownCase BooleanField:LogicRule##"
            self.workingQuery += " ##UnkownCase BooleanField:LogicRule##"
        
        self.workingQuery += ")"

        if len(self.output) > 0:
            self.output += self.conjunctionOutput

        if len(self.query) > 0:
            self.query += self.conjunctionQuery

        self.output += self.workingOutput
        self.query += self.workingQuery
        self.queryTreeCurrent.append((self.fieldName, self.workingQuery))
        self.fullTreeCurrent.append(self.workingFull)

        self.offset = self.intAOffset + Offset.INTLENGTH
        if len(self.criteria) > self.offset:
            self.again = True

    def ProcessCloudField(self):
        self.fieldName = CloudFields(self.criteria[self.offset]).name
        self.workingOutput = self.fieldName
        self.workingQuery = "(" + self.fieldName
        self.workingFull = {"field":self.fieldName, "type":"cloud"}
        
        if self.criteria[self.logicRulesOffset] == LogicRule.Is:
            number = self._iTunesUint(self.criteria[self.intAOffset:self.intAOffset+4])
            
            if self.criteria[self.logicSignOffset] == LogicSign.IntPositive:
                self.workingOutput += " is %s" % (iCloudStatus[number])
                self.workingQuery += " = '%s'" % (iCloudStatus[number])
                self.workingFull["operator"] = "is"
                self.workingFull["value"] = iCloudStatus[number]
            else:
                self.workingOutput += " is not %s" % (iCloudStatus[number])
                self.workingQuery += " != '%s'" % (iCloudStatus[number])
                self.workingFull["operator"] = "is not"
                self.workingFull["value"] = iCloudStatus[number]
  
        else:
            print("Unkown logic rule in ProcessCloudField: LogicRule=%d" % self.criteria[self.logicRulesOffset])
            self.workingOutput += " ##UnkownCase CloudField:LogicRule##"
            self.workingQuery += " ##UnkownCase CloudField:LogicRule##"
        
        self.workingQuery += ")"

        if len(self.output) > 0:
            self.output += self.conjunctionOutput

        if len(self.query) > 0:
            self.query += self.conjunctionQuery

        self.output += self.workingOutput
        self.query += self.workingQuery
        self.queryTreeCurrent.append((self.workingQuery, self.fieldName))
        self.fullTreeCurrent.append(self.workingFull)
        
        self.offset = self.intAOffset + Offset.INTLENGTH
        if len(self.criteria) > self.offset:
            self.again = True

    def ProcessLocationField(self):
        self.fieldName = LocationFields(self.criteria[self.offset]).name
        self.workingOutput = self.fieldName
        self.workingQuery = "(" + self.fieldName
        self.workingFull = {"field":self.fieldName, "type":"location"}
        
        if self.criteria[self.logicRulesOffset] in (LogicRule.Is, LogicRule.Other):
            number = self._iTunesUint(self.criteria[self.intAOffset:self.intAOffset+4])
            
            if self.criteria[self.logicSignOffset] == LogicSign.IntPositive:
                self.workingOutput += " is %s" % (LocationKinds[number])
                self.workingQuery += " = '%s'" % (LocationKinds[number])
                self.workingFull["operator"] = "is"
                self.workingFull["value"] = LocationKinds[number]
            else:
                self.workingOutput += " is not %s" % (LocationKinds[number])
                self.workingQuery += " != '%s'" % (LocationKinds[number])
                self.workingFull["operator"] = "is not"
                self.workingFull["value"] = LocationKinds[number]
        
        else:
            print("Unkown logic rule in ProcessLocationField: LogicRule=%d" % self.criteria[self.logicRulesOffset])
            self.workingOutput += " ##UnkownCase LocationField:LogicRule##"
            self.workingQuery += " ##UnkownCase LocationField:LogicRule##"
        
        self.workingQuery += ")"

        if len(self.output) > 0:
            self.output += self.conjunctionOutput

        if len(self.query) > 0:
            self.query += self.conjunctionQuery

        self.output += self.workingOutput
        self.query += self.workingQuery
        self.queryTreeCurrent.append((self.fieldName, self.workingQuery))
        self.fullTreeCurrent.append(self.workingFull)
        
        self.offset = self.intAOffset + Offset.INTLENGTH
        if len(self.criteria) > self.offset:
            self.again = True

    
    def ProcessDateField(self):
        self.fieldName = DateFields(self.criteria[self.offset]).name
        self.workingOutput = self.fieldName
        self.workingQuery = "TIMESTAMP(%s)" % self.fieldName
        self.workingFull = {"field":self.fieldName, "type":"date"}

        if self.criteria[self.logicRulesOffset] == LogicRule.Greater:
            timestamp = self._iTunesDate(self.criteria[self.intAOffset:self.intAOffset+4])
            self.workingOutput += " is after %s" % self._dateString(timestamp)
            self.workingQuery += " > %d" % timestamp
            self.workingFull["operator"] = "is after"
            self.workingFull["value"] = timestamp
        elif self.criteria[self.logicRulesOffset] == LogicRule.Less:
            timestamp = self._iTunesDate(self.criteria[self.intAOffset:self.intAOffset+4])
            self.workingOutput += " is before %s" % self._dateString(timestamp)
            self.workingQuery += " < %d" % timestamp
            self.workingFull["operator"] = "is before"
            self.workingFull["value"] = timestamp
        elif self.criteria[self.logicRulesOffset] == LogicRule.Other:
            if self.criteria[self.logicSignOffset + 2] == 1:
                timestampA = self._iTunesDate(self.criteria[self.intAOffset:self.intAOffset+4])
                timestampB = self._iTunesDate(self.criteria[self.intBOffset:self.intBOffset+4])
                if self.criteria[self.logicSignOffset] == LogicSign.IntPositive:
                    self.workingOutput += " is in the range of %s to %s" % (self._dateString(timestampA), self._dateString(timestampB))
                    self.workingQuery += " BETWEEN %d AND %d" % (timestampA,timestampB)
                    self.workingFull["operator"] = "is in the range"
                    self.workingFull["value"] = (timestampA,timestampB)
                    self.workingFull["value_date"] = (self._dateString(timestampA), self._dateString(timestampB))
                else:
                    self.workingOutput += " is not in the range of %s to %s" % (self._dateString(timestampA), self._dateString(timestampB))
                    self.workingQuery += " NOT BETWEEN %d AND %d" % (timestampA,timestampB)
                    self.workingFull["operator"] = "is not in the range"
                    self.workingFull["value"] = (timestampA,timestampB)
                    self.workingFull["value_date"] = (self._dateString(timestampA), self._dateString(timestampB))
            elif self.criteria[self.logicSignOffset + 2] == 2:
                if self.criteria[self.logicSignOffset] == LogicSign.IntPositive:
                    self.workingOutput += " is in the last "
                    self.workingQuery = "(TIMESTAMP(NOW()) - TIMESTAMP(%s)) < " % self.fieldName
                    self.workingFull["operator"] = "is in the last"
                else:
                    self.workingOutput += " is not in the last "
                    self.workingQuery = "(TIMESTAMP(NOW()) - TIMESTAMP(%s)) > " % self.fieldName
                    self.workingFull["operator"] = "is not in the last"
                    
                    
                t = (self._iTunesUint(bytes([255-c for c in  self.criteria[self.timeValueOffset:self.timeValueOffset+4] ])) + 1 )% 4294967296
                multiple = self._iTunesUint(self.criteria[self.timeMultipleOffset:self.timeMultipleOffset+4])
                self.workingQuery += "%d" % (t*multiple)
                self.workingFull["value"] = t*multiple
                if multiple == 86400:
                    self.workingOutput += "%d days" % t
                    self.workingFull["value_date"] = "%d days" % t
                elif  multiple == 604800:
                    self.workingOutput += "%d weeks" % t
                    self.workingFull["value_date"] = "%d weeks" % t
                elif multiple == 2628000:
                    self.workingOutput += "%d months" % t
                    self.workingFull["value_date"] = "%d months" % t
                else:
                    self.workingOutput += "%d*%d seconds" % (multiple,t)
                    self.workingFull["value_date"] = "%d*%d seconds" % (multiple,t)
                    print("##UnkownCase DateField: LogicRule.Other: multiple '%d' is unkown##" % multiple)


        if len(self.output) > 0:
            self.output += self.conjunctionOutput

        if len(self.query) > 0:
            self.query += self.conjunctionQuery

        self.output += self.workingOutput
        self.query += self.workingQuery
        self.queryTreeCurrent.append((self.fieldName, self.workingQuery))
        self.fullTreeCurrent.append(self.workingFull)
        
        self.offset = self.intAOffset + Offset.INTLENGTH
        if len(self.criteria) > self.offset:
            self.again = True              


    def _iTunesUint(self, bytearr, divideby=False, denominator=20):
        num = struct.unpack('>I', bytearr)[0]
        if divideby: # For rating/stars by 20
            num = int(num/denominator)
        return num


    def _iTunesDate(self,bytearr):
        timestamp = self._iTunesUint(bytearr)
        return timestamp + DateStartFromUnix

    def _dateString(self,timestamp):
        return datetime.datetime.utcfromtimestamp(int(timestamp)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
            

if __name__ == '__main__':
    info = "AQEAAwAAAAIAAAAZAAAAAAAAAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="
    criteria = "U0xzdAABAAEAAAADAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABYAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABEAAAAAAAAAA8AAAAAAAAAAAAAAAAAAAABAAAAAAAAAA8AAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB/FNMc3QAAQABAAAAAwAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAARAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFgAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEQAAAAAAAAAEQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAEQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABYAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABEAAAAAAAAABIAAAAAAAAAAAAAAAAAAAABAAAAAAAAABIAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAZAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAARAAAAAAAAABZAAAAAAAAAAAAAAAAAAAAAQAAAAAAAABZAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAA"
    parser = SmartPlaylistParser(info, criteria)
    parser.parse()
    print("############ Output:")
    print(parser.output)
    print("############ Query:")
    print(parser.query)
    print("############ JSON:")
    print(json.dumps(parser.queryTree, indent=2))
    print("############ Ignore:")
    print(parser.ignore)
