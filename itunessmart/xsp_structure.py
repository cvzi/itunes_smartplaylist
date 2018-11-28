"""
Module holding static data related to the XSP playlist format.
"""

xml_dec = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
xml_doc = '''{dec}
<smartplaylist type="songs">
    <name>{name}</name>
    <match>{globalmatch}</match>
{rules}
{meta}
</smartplaylist>'''

xml_rule = '''    <rule field="{field}" operator="{operator}">
{values}
    </rule>'''

xml_value = '''        <value>{value}</value>'''

xsp_fields = {
"Artist": "artist",
"AlbumArtist": "albumartist",
"Album": "album",
"Genre": "genre",
"Name": "title",
"Year": "year",
"Duration": "time",
"TrackNumber": "tracknumber",
"Plays": "playcount",
"LastPlayed": "lastplayed",
"Rating": "userrating",
"Comments": "comment",
"PlaylistPersistentID": "playlist"}

xsp_allowed_fields = xsp_fields.keys()

xsp_operators = {
"and": "all",
"or": "one",
"like": "contains",
"not like": "doesnotcontain",
"is": "is",
"is not": "isnot",
"starts with": "startswith",
"ends with": "endswith",
"less than": "lessthan",
"greater than": "greaterthan",
"is after": "after",
"is before": "before",
"is in the last": "inthelast",
"is not in the last": "notinthelast"}

xsp_allowed_operators = xsp_operators.keys()

xsp_sorting = {
"SortName": ("title", "ascending"),
"SortAlbum": ("album", "ascending"),
"SortArtist": ("artist", "ascending"),
"Genre": ("genre", "ascending"),
"Rating DESC": ("userrating", "descending"),
"Rating ASC": ("userrating", "ascending"),
"LastPlayed DESC": ("lastplayed", "descending"),
"LastPlayed ASC": ("lastplayed", "ascending"),
"Plays DESC": ("playcount", "descending"),
"Plays ASC": ("playcount", "ascending"),
"DateAdded DESC": ("dateadded ", "descending"),
"DateAdded ASC": ("dateadded ", "ascending")
}