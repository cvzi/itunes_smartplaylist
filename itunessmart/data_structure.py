"""
Module holding static data related to the playlist format.
"""

from enum import IntEnum


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
]

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
    0x1021B1 : "Music", # TODO My guess: This is similar to Music
    0x208004 : "Undesired Music", # TODO My guess: This is some kind of Music that should not appear in the toplevel playlist
    0x20A004 : "Undesired Other" # TODO My guess: This is something (other than music) that should not appear in the toplevel playlist
}

iCloudStatus = {
    0x01: "Purchased",
    0x02: "Matched",
    0x03: "Uploaded",
    0x04: "Ineligible",
    0x05: "Local Only",
    0x07: "Duplicate"
}

LocationKinds = {
    0x01: "Computer",
    0x10: "iCloud"
}

SelectionMethodsStrings = {
    "Random" :["random", "RANDOM()"],
    "Name" : ["name", "SortName"],
    "Album" : ["album", "SortAlbum"],
    "Artist" : ["artist", "SortArtist"],
    "Genre" : ["genre", "Genre"],
    "HighestRating" : ["highest rated", "Rating DESC"],
    "LowestRating" : ["lowest rated", "Rating ASC"],
    "RecentlyPlayed" : [["most recently played", "least recently played"], ["LastPlayed DESC", "LastPlayed ASC"]],
    "OftenPlayed" : [["most often played", "least often played"], ["Plays DESC", "Plays ASC"]],
    "RecentlyAdded" : [["most recently added", "least recently added"], ["DateAdded DESC", "DateAdded ASC"]]
}


DateStartFromUnix = -2082844800 # iTunes/Unix time stamp 0 difference

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
    """Byte offsets for the fields"""
    INTLENGTH = 67;           # The length on a int criteria starting at the first int
    SUBEXPRESSIONLENGTH = 192 # The length of a subexpression starting from FIELD
    
    # INFO OFFSETS
    # Offsets for bytes which...
    LIVEUPDATE = 0           # determine whether live updating is enabled - Absolute offset
    MATCHBOOL = 1            # determine whether logical matching is to be performed - Absolute offset
    LIMITBOOL = 2            # determine whether results are limited - Absolute offset
    LIMITMETHOD = 3          # determine by what criteria the results are limited - Absolute offset
    SELECTIONMETHOD = 7      # determine by what criteria limited playlists are populated - Absolute offset
    LIMITINT = 8             # determine the limited - Absolute offset
    LIMITCHECKED = 12        # determine whether to exclude unchecked items - Absolute offset
    SELECTIONMETHODSIGN = 13 # determine whether certain selection methods are "most" or "least" - Absolute offset
    
    # CRITERIA OFFSETS
    # Offsets for bytes which...
    LOGICTYPE = 15    # determine whether all or any criteria must match - Absolute offset
    FIELD = 139       # determine what is being matched (Artist, Album, &c) - Absolute offset
    LOGICSIGN = 1     # determine whether the matching rule is positive or negative (e.g., is vs. is not) - Relative offset from FIELD
    LOGICRULE = 4     # determine the kind of logic used (is, contains, begins, &c) - Relative offset from FIELD
    STRING = 54       # begin string data - Relative offset from FIELD
    INTA = 57         # begin the first int - Relative offset from FIELD
    INTB = 24         # begin the second int - Relative offset from INTA
    TIMEMULTIPLE = 73 # begin the int with the multiple of time - Relative offset from FIELD
    TIMEVALUE = 65    # begin the inverse int with the value of time - Relative offset from FIELD
    SUBLOGICTYPE = 68 # determine whether all or any criteria must match - Relative offset from FIELD
    SUBINT = 61       # begin the first int - Relative offset from FIELD

