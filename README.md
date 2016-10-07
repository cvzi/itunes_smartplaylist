iTunes Smartplaylist parser
===========================

Convert smart playlist information to a readable form.

This script is a **Python 3** implementation, based on **banshee-itunes-import-plugin** by Scott Peterson.

It was tested on Windows 10 with iTunes 12.5.1 (64bit) and Python 3.4.4.

As far as I know it does not work with Python 2.x.

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

And a tree structure
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


To export all playlists to text files, use `python3 export.py`

