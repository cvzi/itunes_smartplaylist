"""
iTunes Smart playlist parser with Python. Decode itunes smart playlist rules from base64 data. Convert iTunes smart playlists to Kodi xsp smart playlists.
"""

__version__ = '1.1.5'
__author__ = 'cuzi'
__email__ = 'cuzi@openmail.cc'
__source__ = 'https://github.com/cvzi/itunes_smartplaylist'
__license__ = """
MIT License

Copyright (c) cuzi 2018

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

__all__ = ["Parser", "SmartPlaylist", "BytesParser", "createXSPFile", "createXSP", "PlaylistException", "EmptyPlaylistException", "readiTunesLibrary", "generatePersistentIDMapping", "createPlaylistTree", "LibraryException"]

from itunessmart.parse import SmartPlaylistParser, SmartPlaylist
from itunessmart.xsp import createXSPFile, createXSP, PlaylistException, EmptyPlaylistException
from itunessmart.library import readiTunesLibrary, generatePersistentIDMapping, createPlaylistTree, LibraryException


class Parser:
    """Parse data from a base64 encoded string"""
    def __init__(self, datastr_info: str = None, datastr_criteria: str = None):
        """Parse data from a base64 encoded string"""
        self.result = None
        self._parser = SmartPlaylistParser(datastr_info, datastr_criteria)
        if datastr_info and datastr_criteria:
            self._update()

    def _update(self):
        self.result = None
        self._parser.parse()
        self.result = self._parser.result()

    def update_data_base64(self, datastr_info: str, datastr_criteria: str) -> SmartPlaylist:
        self._parser.str_data(datastr_info, datastr_criteria)
        self._update()
        return self.result

    def update_data_bytes(self, data_info: bytes, data_criteria: bytes) -> SmartPlaylist:
        self._parser.data(data_info, data_criteria)
        self._update()
        return self.result


class BytesParser(Parser):
    """Parse data from raw bytes"""
    def __init__(self, data_info, data_criteria):
        """Parse data from raw bytes"""
        super().__init__()
        self._parser = SmartPlaylistParser()
        self._parser.data(data_info, data_criteria)
        self._parser.parse()

        self._update()
