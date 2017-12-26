iTunes Smartplaylist parser
===========================

Convert smart playlist information to a readable form.

This script is a **Python 3** implementation, based on [banshee-itunes-import-plugin](https://code.google.com/archive/p/banshee-itunes-import-plugin/) by [Scott Peterson](https://github.com/lunchtimemama).

It was tested on Windows 10 with iTunes 12.7.2 (64bit) and Python 3.6.

It does not work with Python 2.x.

Kodi smart playlists
--------------------

You can convert all your iTunes smart playlists to Kodi smart playlists with this command: 

`python3 export_xsp.py`  

Then place the resulting .xsp files in your [userdata](http://kodi.wiki/view/Userdata) folder.  

Most of the common functions and rules are available in both formats and often iTunes playlists are fully convertible to Kodi.  
The biggest difference are nested rules in iTunes which are not available in Kodi. 
However, nested rules can be simulated with sub-playlists. These "helper"-playlists are named with the prefix "zzzsub_" and a MD5 hash of its rules. 
If you don't want these subplaylists, set the variable `EXPORT_NESTED_RULES_AS_SUBPLAYLIST = False` in the *export_xsp.py* file.  

More information on Kodie smart playlists:  
http://kodi.wiki/view/smart_playlists#Format_of_a_smart_playlist_file




Text export
-----------

To export all playlists to text files, use `python3 export.py`  


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
info = "AQEAAwAAAAIAAAAZ..."
criteria = "U0xzdAABAAEAAAAD..."
parser = SmartPlaylistParser(info, criteria)
parser.parse()
print(parser.output)
print(parser.query)
print(json.dumps(parser.queryTree, indent=2))
```

A text format:

```
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

