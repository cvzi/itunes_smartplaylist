
__all__ = ["Parser", "SmartPlaylist", "BytesParser", "createXSPFile", "createXSP", "PlaylistException", "EmptyPlaylistException", "readiTunesLibrary", "generatePersistentIDMapping", "createPlaylistTree"]


from itunessmart.parse import SmartPlaylistParser, SmartPlaylist
from itunessmart.xsp import createXSPFile, createXSP, PlaylistException, EmptyPlaylistException
from itunessmart.library import readiTunesLibrary, generatePersistentIDMapping, createPlaylistTree


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

    def update_data_base64(self, datastr_info: str, datastr_criteria: str):
        self._parser.str_data(datastr_info, datastr_criteria)
        self._update()
        
    def update_data_bytes(self, data_info: bytes, data_criteria: bytes):
        self._parser.data(data_info, data_criteria)
        self._update()


class BytesParser(Parser):
    """Parse data from raw bytes"""
    def __init__(self, data_info, data_criteria):
        """Parse data from raw bytes"""
        self._parser = SmartPlaylistParser()
        self._parser.data(data_info, data_criteria)
        self._parser.parse()
        
        self._update()


