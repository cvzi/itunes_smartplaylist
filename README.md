iTunes Smartplaylist parser
===========================

[![itunessmart on PyPI](https://img.shields.io/pypi/v/itunessmart.svg)](https://pypi.python.org/pypi/itunessmart)
[![Python Versions](https://img.shields.io/pypi/pyversions/itunessmart.svg)](https://pypi.python.org/pypi/itunessmart)
[![Coverage Status](https://coveralls.io/repos/github/cvzi/itunes_smartplaylist/badge.svg?branch=master)](https://coveralls.io/github/cvzi/itunes_smartplaylist?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/479adb4cc1eb4f6d8a5e9e193d676338)](https://www.codacy.com/app/cvzi/itunes_smartplaylist?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=cvzi/itunes_smartplaylist&amp;utm_campaign=Badge_Grade)
[![Build Status](https://travis-ci.org/cvzi/itunes_smartplaylist.svg?branch=master)](https://travis-ci.org/cvzi/itunes_smartplaylist)

Convert smart playlist information to a readable form.

This module is a **Python 3** implementation, based on [banshee-itunes-import-plugin](https://code.google.com/archive/p/banshee-itunes-import-plugin/) by [Scott Peterson](https://github.com/lunchtimemama).

It was tested on Windows 10 with iTunes 12.9.0 (64bit) and Python 3.6.

It does not work with Python 2.x.

Kodi smart playlists
--------------------

You can convert all your iTunes smart playlists to Kodi smart playlists with this interactive script: 

`python3 utils/export_xsp.py` or `python3 -m itunessmart`

Then place the resulting .xsp files from `out/` in your [userdata](http://kodi.wiki/view/Userdata) folder.  

Most of the common functions and rules are available in both formats and often iTunes playlists are fully convertible to Kodi.  
The biggest difference are nested rules in iTunes which are not available in Kodi. 
However, nested rules can be simulated with sub-playlists. These "helper"-playlists are named with the prefix "zzzsub_" and a MD5 hash of its rules. 
When you run `utils/export_xsp.py`, you can disable generation of subplaylists.  

More information on Kodie smart playlists:  
[http://kodi.wiki/view/smart_playlists#Format_of_a_smart_playlist_file](http://kodi.wiki/view/smart_playlists#Format_of_a_smart_playlist_file)

Text export
-----------

To export all playlists to text files, use `python3 utils/export.py`  

The format
----------

Smart playlist data in iTunes is saved in the *iTunes Music Library.xml* file.

The data in the playlist entry in the xml file is base64 encoded binary data:
```xml
<dict>
	<key>Name</key><string>Example</string>
	<key>Playlist ID</key><integer>123456</integer>
	<key>Playlist Persistent ID</key><string>49C97D85843B04CC</string>
	<key>Parent Persistent ID</key><string>4DA0F774D3F70473</string>
	<key>All Items</key><true/>
	<key>Smart Info</key>
	<data>
	AQEAAwAAAAIAAAAZAAAAAAAAAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
	AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
	AAAAAA==
	</data>
	<key>Smart Criteria</key>
	<data>
	U0xzdAABAAEAAAADAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
	AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
	AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABYAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAA
	AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABEAAAAAAAAAA8AAAAAAAAAAAAAAAAAAAABAAAA
	AAAAAA8AAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQEAAAAAA
	AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB/FNMc3QAAQABAAAAAw
	AAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
	AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
	AAAAAAAAAAAAAAAAAAAAAAAWAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
	AAAAAAAAAAAAAAAAAAARAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAQAAAAAAAAAA
	AAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFgAAABAAAAAAAAAAAAAAAAAAAAAAAAA
	AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEQAAAAAAAAAEQAAAAAAAAAAAAAAAAAAAAEA
	AAAAAAAAEQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABYAAAAQAAAAA
	AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABEAAAAAAAAABIAAA
	AAAAAAAAAAAAAAAAABAAAAAAAAABIAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAA
	AAAAAAAAZAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
	AAAARAAAAAAAAABZAAAAAAAAAAAAAAAAAAAAAQAAAAAAAABZAAAAAAAAAAAAAAAAAAAAAQAAA
	AAAAAAAAAAAAAAAAAAAAAAA
	</data>
	<key>Playlist Items</key>
	<array>
		<dict>
			<key>Track ID</key><integer>123</integer>
		</dict>
		<dict>
			<key>Track ID</key><integer>124</integer>
		</dict>
		<dict>
		...
		<dict>
	</array>
</dict>

```
It can be converted into three different output formats:
```python
import itunessmart
info = "AQEAAwAAAAIAAAAZ..."
criteria = "U0xzdAABAAEAAAAD..."
parser = itunessmart.Parser(info, criteria)
result = parser.result
print(result.output)
print(result.query)
print(json.dumps(result.queryTree, indent=2))
```

A text format:

```python
Plays is greater than 15 and
[
	Plays is greater than 16 or
	Plays is greater than 17 or
	Plays is greater than 18
] and
Rating is greater than 4
```

A sql-like format:

```sql
(Plays > 15) AND ( (Plays > 16) OR (Plays > 17) OR (Plays > 18) ) AND (Rating > 4)
```

And two tree structures
```javascript
{
  "tree": {
    "and": [
      [
        "Plays",
        "(Plays > 15)"
      ],
      {
        "or": [
          [
            "Plays",
            "(Plays > 16)"
          ],
          [
            "Plays",
            "(Plays > 17)"
          ],
          [
            "Plays",
            "(Plays > 18)"
          ]
        ]
      },
      [
        "Rating",
        "(Rating > 4)"
      ]
    ]
  },
  "liveupdate": true,
  "onlychecked": false
}
```  

```javascript
{
  "fulltree": {
    "and": [
      {
        "field": "Plays",
        "type": "int",
        "operator": "greater than",
        "value": 15
      },
      {
        "or": [
          {
            "field": "Plays",
            "type": "int",
            "operator": "greater than",
            "value": 16
          },
          {
            "field": "Plays",
            "type": "int",
            "operator": "greater than",
            "value": 17
          },
          {
            "field": "Plays",
            "type": "int",
            "operator": "greater than",
            "value": 18
          }
        ]
      },
      {
        "field": "Rating",
        "type": "int",
        "operator": "greater than",
        "value": 4
      }
    ]
  }
}
```
