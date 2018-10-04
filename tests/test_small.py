try:
    import itunessmart
except ImportError:
    import os
    import sys
    include = os.path.relpath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, include)
    import itunessmart
    print("Imported itunessmart from %s" % os.path.abspath(os.path.join(include, "itunessmart")))

import json


testdata = [
    {
        "desc" : "5 stars  AND  Media Kind is Music, Limited to 50000",
        "info" : ("AQEBAwAAABUAAMNQAAAAAAAAAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
                  "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
                  "AAAAAA=="),

        "criteria" : ("U0xzdAABAAEAAAACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
                      "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
                      "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABkAAAEAAAAAAAAAAAAAAAAAAAAAAAAA"
                      "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABEAAAAAAAAAGQAAAAAAAAAAAAAAAAAAAAB"
                      "AAAAAAAAAG0AAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA8AAAAAQAA"
                      "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAARAAAAAAAAAAB"
                      "AAAAAAAAAAAAAAAAAAAAAQAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAA"
                      "AAAAAAAA"),

        "expected" : {
            "query" : "(Rating BETWEEN 5 AND 5) AND (MediaKind = 'Music')",
            "number": 50000,
        }
        
    },
    {
        "desc" : "string: the new america, select all (checked and unchecked) itms, Live updating on",
        "info" : ("AQEAAgAAAAIAACaUAAAAAAAAAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAA=="),
        "criteria" : ("U0xzdAABAAEAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMBAAABAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAeAFQAaABlACAATgBlAHcAIABBAG0AZQBy"
            "AGkAYwBh"),

        "expected" : {
            "query" : "(lower(Album) = 'the new america')",
            "onlychecked": False,
            "liveupdate": True,
        }
    },
    {
        "desc" : "string: the new america, select only checked itms",
        "info" : ("AQEAAgAAAAIAACaUAQAAAAAAAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAA=="),
        "criteria" : ("U0xzdAABAAEAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMBAAABAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAeAFQAaABlACAATgBlAHcAIABBAG0AZQBy"
            "AGkAYwBh"),
         "expected" : {
            "query" : "(lower(Album) = 'the new america')",
            "onlychecked": True,
            "liveupdate": True,
        }
    },
    {
        "desc" : "string: the new america, select all (checked and unchecked) itms, Live updating off",
        "info" : ("AAEAAgAAAAIAACaUAAAAAAAAAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAA=="),
        "criteria" : ("U0xzdAABAAEAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMBAAABAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAeAFQAaABlACAATgBlAHcAIABBAG0AZQBy"
            "AGkAYwBh"),
         "expected" : {
            "query" : "(lower(Album) = 'the new america')",
            "onlychecked": False,
            "liveupdate": False,
        }
    },

    {
        "desc" : "Boolean fields and Sort fields",
        "info" : ("AQEAAgAAAAIAAAAAAAAAAAAAAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAA=="),
        "criteria" : ('U0xzdAABAAEAAAAKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACUCAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAlAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAARAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAKQIAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACkAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABPAQAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJgBMAC4ARQAuAFMAIABBAHIAdABpAHMAdABlAHMAIAAtACAARQBQAAAAUQEAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABoAQQBjAGEAZABlAG0AeQAgAEkAcwAuAC4ALgAAAFIBAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAASAEMAYQByAGQAaQBnAGEAbgBzAAAATgEAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYAYQBiAGMAAABTAQAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACABGAGEAaQByAAAAWQEAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYATwBsAGQ='),
        "expected" : {
            "queryTree" : {
                "onlychecked": False,
                "liveupdate": True,
                "tree": {
                  "and": [
                    [
                      "HasArtwork",
                      "(HasArtwork = 1)"
                    ],
                    [
                      "HasArtwork",
                      "(HasArtwork = 0)"
                    ],
                    [
                      "Purchased",
                      "(Purchased = 1)"
                    ],
                    [
                      "Purchased",
                      "(Purchased = 0)"
                    ],
                    [
                      "SortAlbum",
                      "(lower(SortAlbum) = 'l.e.s artistes - ep')"
                    ],
                    [
                      "SortAlbumartist",
                      "(lower(SortAlbumartist) = 'academy is...')"
                    ],
                    [
                      "SortComposer",
                      "(lower(SortComposer) = 'cardigans')"
                    ],
                    [
                      "SortName",
                      "(lower(SortName) LIKE '%abc%')"
                    ],
                    [
                      "SortShow",
                      "(lower(SortShow) Like 'fair%')"
                    ],
                    [
                      "VideoRating",
                      "(lower(VideoRating) = 'old')"
                    ]
                  ]
                },
                "fulltree": {
                  "and": [
                    {
                      "field": "HasArtwork",
                      "type": "boolean",
                      "operator": "is",
                      "value": True
                    },
                    {
                      "field": "HasArtwork",
                      "type": "boolean",
                      "operator": "is",
                      "value": False
                    },
                    {
                      "field": "Purchased",
                      "type": "boolean",
                      "operator": "is",
                      "value": True
                    },
                    {
                      "field": "Purchased",
                      "type": "boolean",
                      "operator": "is",
                      "value": False
                    },
                    {
                      "field": "SortAlbum",
                      "type": "string",
                      "operator": "is",
                      "value": "L.E.S Artistes - EP"
                    },
                    {
                      "field": "SortAlbumartist",
                      "type": "string",
                      "operator": "is",
                      "value": "Academy Is..."
                    },
                    {
                      "field": "SortComposer",
                      "type": "string",
                      "operator": "is",
                      "value": "Cardigans"
                    },
                    {
                      "field": "SortName",
                      "type": "string",
                      "operator": "like",
                      "value": "abc"
                    },
                    {
                      "field": "SortShow",
                      "type": "string",
                      "operator": "starts with",
                      "value": "Fair"
                    },
                    {
                      "field": "VideoRating",
                      "type": "string",
                      "operator": "is",
                      "value": "Old"
                    }
                  ]
                }
            }
        }
    },
    {
        "desc" : "Sub expression: Plays > 15 AND (  PLAYS > 16 AND PLAYS > 17 AND PLAYS > 18 ) AND RATING > 4",
        "info" : ("AQEAAwAAAAIAAAAZAAAAAAAAAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAA=="),
        "criteria" : ("U0xzdAABAAEAAAADAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABYAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABEAAAAAAAAAA8AAAAAAAAAAAAAAAAAAAABAAAAAAAAAA8AAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB/FNMc3QAAQABAAAAAwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAARAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFgAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEQAAAAAAAAAEQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAEQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABYAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABEAAAAAAAAABIAAAAAAAAAAAAAAAAAAAABAAAAAAAAABIAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAZAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAARAAAAAAAAABZAAAAAAAAAAAAAAAAAAAAAQAAAAAAAABZAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAA"),
        "expected" : {
            "query" : "(Plays > 15) AND ( (Plays > 16) AND (Plays > 17) AND (Plays > 18) ) AND (Rating > 4)",
        }
    }

]

def test_examples(verbose=False):
    for test in testdata:
        parser = itunessmart.Parser(test["info"], test["criteria"])
        if verbose:
            print("\n\ntest: %s" % test["desc"])
            print("############")
            print(parser.output)
            print("############")
            print(parser.query)
            print("############")
            print(json.dumps(parser.queryTree, indent=2))
            print("############")
            print(parser.ignore)

        if "expected" in testdata:
            exp = testdata["expected"]
            if "output" in exp:
                assert exp.pop("output") == parser.output
            if "query" in exp:
                assert exp.pop("query") == parser.query
            if "queryTree" in exp:
                assert exp.pop("queryTree") == parser.queryTree
            if "ignore" in exp:
                assert exp.pop("ignore") == parser.ignore

            for key in exp:
                assert exp[key] == parser.query[key]

def test_double_parse():
    parser = itunessmart.Parser(testdata[0]["info"], testdata[0]["criteria"])
    query = parser.query
    parser._parser.parse()
    assert query == parser.query
    parser._parser.parse()
    assert query == parser.query
    
def test_reuse_parser():
    parser0 = itunessmart.Parser(testdata[0]["info"], testdata[0]["criteria"])
    parser1 = itunessmart.Parser(testdata[1]["info"], testdata[1]["criteria"])
    
    # Reuse parser 0 with data[1]
    parser0.update_data_base64(testdata[1]["info"], testdata[1]["criteria"])
    
    assert parser0.queryTree == parser1.queryTree
    
    # Reuse parser 0 with data[3]
    parser0.update_data_base64(testdata[3]["info"], testdata[3]["criteria"])
    
    # Reuse parser 1 with data[3]
    parser1.update_data_base64(testdata[3]["info"], testdata[3]["criteria"])
    
    assert parser0.queryTree == parser1.queryTree
    




if __name__ == '__main__':    
    test_examples(verbose=True)
    test_double_parse()
    test_reuse_parser()

