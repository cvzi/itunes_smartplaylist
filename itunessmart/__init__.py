
__all__ = ["Parser", "BytesParser"]


from itunessmart.parse import SmartPlaylistParser

class Parser:
    """Parse data from a base64 encoded string"""
    def __init__(self, datastr_info, datastr_criteria):
        """Parse data from a base64 encoded string"""
        self._parser = SmartPlaylistParser(datastr_info, datastr_criteria)
        self._update()
    
    def _update(self):
        self.output = self._parser.output
        self.query = self._parser.query
        self.queryTree = self._parser.queryTree
        self.ignore = self._parser.ignore

    def update_data_base64(self, datastr_info, datastr_criteria):
        self._parser.str_data(datastr_info, datastr_criteria)
        self._parser.parse()
        self._update()
        
    def update_data_bytes(self, data_info, data_criteria):
        self._parser.data(data_info, data_criteria)
        self._parser.parse()
        self._update()


class BytesParser(Parser):
    """Parse data from raw bytes"""
    def __init__(self, data_info, data_criteria):
        """Parse data from raw bytes"""
        self._parser = SmartPlaylistParser()
        self._parser.data(data_info, data_criteria)
        self._parser.parse()
        
        self._update()



if __name__ == '__main__':
    info = "AQEAAwAAAAIAAAAZAAAAAAAAAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="
    criteria = "U0xzdAABAAEAAAADAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABYAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABEAAAAAAAAAA8AAAAAAAAAAAAAAAAAAAABAAAAAAAAAA8AAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB/FNMc3QAAQABAAAAAwAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAARAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFgAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEQAAAAAAAAAEQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAEQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABYAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABEAAAAAAAAABIAAAAAAAAAAAAAAAAAAAABAAAAAAAAABIAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAZAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAARAAAAAAAAABZAAAAAAAAAAAAAAAAAAAAAQAAAAAAAABZAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAA"
    parser = Parser(info, criteria)
    print("############ Output:")
    print(parser.output)
    print("############ Query:")
    print(parser.query)
    print("############ JSON:")
    import json
    print(json.dumps(parser.queryTree, indent=2))
    print("############ Ignore:")
    print(parser.ignore)
