import json
import copy
import os
import base64

try:
    import itunessmart
except ImportError:
    import sys
    include = os.path.relpath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, include)
    import itunessmart
    print("Imported itunessmart from %s" % os.path.abspath(os.path.join(include, "itunessmart")))

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
                    (
                      "HasArtwork",
                      "(HasArtwork = 1)"
                    ),
                    (
                      "HasArtwork",
                      "(HasArtwork = 0)"
                    ),
                    (
                      "Purchased",
                      "(Purchased = 1)"
                    ),
                    (
                      "Purchased",
                      "(Purchased = 0)"
                    ),
                    (
                      "SortAlbum",
                      "(lower(SortAlbum) = 'l.e.s artistes - ep')"
                    ),
                    (
                      "SortAlbumartist",
                      "(lower(SortAlbumartist) = 'academy is...')"
                    ),
                    (
                      "SortComposer",
                      "(lower(SortComposer) = 'cardigans')"
                    ),
                    (
                      "SortName",
                      "(lower(SortName) LIKE '%abc%')"
                    ),
                    (
                      "SortShow",
                      "(lower(SortShow) Like 'fair%')"
                    ),
                    (
                      "VideoRating",
                      "(lower(VideoRating) = 'old')"
                    )
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
    for test in copy.deepcopy(testdata):
        parser = itunessmart.Parser(test["info"], test["criteria"])
        result = parser.result
        if verbose:
            print("\n\nTest: %s" % test["desc"])
            print("############")
            print(result.output)
            print("############")
            print(result.query)
            print("############")
            print(json.dumps(result.queryTree, indent=2))
            print("############")
            print(result.ignore)

        if "expected" in test and test["expected"]:
            exp = test["expected"]
            if "output" in exp:
                assert exp.pop("output") == result.output
            if "query" in exp:
                assert exp.pop("query") == result.query
            if "queryTree" in exp:
                assert exp.pop("queryTree") == result.queryTree
            if "ignore" in exp:
                assert exp.pop("ignore") == result.ignore

            for key in exp:
                assert exp[key] == result.queryTree[key]
        else:
            raise NotImplementedError(test["desc"])

def test_double_parse(verbose=False):
    parser = itunessmart.Parser(testdata[0]["info"], testdata[0]["criteria"])
    query = parser.result.query
    parser._parser.parse()
    assert query == parser.result.query
    parser._parser.parse()
    assert query == parser.result.query
    
    
def test_reuse_parser(verbose=False):
    parser0 = itunessmart.Parser(testdata[0]["info"], testdata[0]["criteria"])
    parser1 = itunessmart.Parser(testdata[1]["info"], testdata[1]["criteria"])
    
    # Reuse parser 0 with data[1]
    parser0.update_data_base64(testdata[1]["info"], testdata[1]["criteria"])
    
    assert parser0.result.queryTree == parser1.result.queryTree
    
    # Reuse parser 0 with data[3]
    parser0.update_data_base64(testdata[3]["info"], testdata[3]["criteria"])
    
    # Reuse parser 1 with data[3]
    parser1.update_data_base64(testdata[3]["info"], testdata[3]["criteria"])
    
    assert parser0.result.queryTree == parser1.result.queryTree


def test_mixed_and_or_subgroup(verbose=False):
    info = "AQEAAwAAABoAAAAZAQEAAAAAAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="
    criteria = "U0xzdAABAAEAAAACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGAU0xzdAABAAEAAAACAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABEAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA8AAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAARAAAAAAAAAAgAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAgAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEBAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAsRTTHN0AAEAAQAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAMAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABwAUgBoAHkAdABoAG0AIAAmACAAQgBsAHUAZQBzAAAACAMAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAQgBsAHUAZQBzACAAUgBvAGMAawAAAAAAAAABAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFkU0xzdAABAAEAAAADAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgBAAACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAKAEIAbAB1AGUAcwAAAAgBAAACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAEoAdQBnACAAQgBhAG4AZAAAAAgBAAACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAaAEIAbwBvAGcAaQBlACAAVwBvAG8AZwBpAGU="
    result = itunessmart.Parser(info, criteria).result

    assert 'Genre does not contain "Rhythm & Blues" ' in result.output
    assert 'Genre does not contain "Blues Rock" ' in result.output
    assert 'Genre contains "Blues" ' in result.output
    assert "[\n\tGenre contains \"Blues\" " in result.output
    assert "(lower(Genre) NOT LIKE '%rhythm & blues%')" in result.query
    assert "(lower(Genre) NOT LIKE '%blues rock%')" in result.query


def test_icloud_status_no_longer_available(verbose=False):
    info = "AQEAAwAAAAIAAAAZAAAAAAAAAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="
    criteria = "U0xzdAABAAEAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIYAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABEAAAAAAAAAAkAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAkAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAA="
    result = itunessmart.Parser(info, criteria).result

    assert result.output == "iCloudStatus is No Longer Available"
    assert result.query == "(iCloudStatus = 'No Longer Available')"


def test_unknown_list_value_falls_back_without_crashing(verbose=False):
    info = "AQEAAwAAAAIAAAAZAAAAAAAAAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="
    criteria = "U0xzdAABAAEAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIYAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABEAAAAAAAAAAkAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAkAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAA="
    decoded = bytearray(base64.standard_b64decode(criteria))
    decoded[199] = 0x0B
    result = itunessmart.BytesParser(base64.standard_b64decode(info), bytes(decoded)).result

    assert result.output == "iCloudStatus is UnknownValue[11]"
    assert result.query == "(iCloudStatus = 'UnknownValue[11]')"


def test_kind_contains_output_uses_original_string(verbose=False):
    info = (
        "AQEAAwAAAAIAAAAZAAAAAAAAAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAA=="
    )
    criteria = (
        "U0xzdAABAAEAAAACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAQAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGAU0xzdAABAAEAAAACAAAAAQAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAADwAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAABEAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAB"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA8AAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAARAAAAAAAAAAgAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAg"
        "AAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEBAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQhTTHN0AAEAAQAAAAIAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAACQEAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAYAYQBhAGMAAAAEAQAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAACgBOAG8AawBpAGE="
    )
    result = itunessmart.Parser(info, criteria).result

    assert 'Kind contains "aac" ' in result.output
    assert 'Artist contains "Nokia" ' in result.output
    assert "None" not in result.output


def run_all(verbose=False):
    for fname, f in list(globals().items()):
        if fname.startswith('test_'):
            print("%s()" % fname)
            f(verbose)
            print("Ok.")



if __name__ == '__main__':
    run_all(verbose=False)
