"""
Module holding the parsing algorithm
"""

import logging
import base64
import datetime
import struct
import json
from itunessmart.data_structure import *


class SmartPlaylist:
    """ Parser result. Contains all decoded playlist data"""

    def __init__(self, parser):
        self.output = parser.output
        self.query = parser.query
        self.queryTree = parser.queryTree
        self.ignore = parser.ignore

    def __str__(self):
        return "SmartPlaylist(`%s`)" % self.query

    def __repr__(self):
        return "SmartPlaylist(%s)" % json.dumps({"queryTree": self.queryTree, "ignore": self.ignore}, indent=2)


class SmartPlaylistParser:
    def __init__(self, datastr_info=None, datastr_criteria=None):
        self.is_parsed = False
        if datastr_info and datastr_criteria:
            self.str_data(datastr_info, datastr_criteria)
            self.parse()

    def str_data(self, datastr_info, datastr_criteria):
        i = base64.standard_b64decode("".join(datastr_info.split()))
        c = base64.standard_b64decode("".join(datastr_criteria.split()))
        return self.data(i, c)

    def data(self, data_info, data_criteria):
        self.is_parsed = False
        self.info = data_info
        self.criteria = data_criteria
        self.query = ""
        self.root = {}
        self.queryTree = self.root
        self.queryTreeCurrent = []
        self.fullTreeRoot = {}
        self.fullTree = self.fullTreeRoot
        self.fullTreeCurrent = []
        self.output = ""
        self.ignore = ""
        self.limit = {}

        self.subStack = []

    def result(self):
        if self.is_parsed:
            return SmartPlaylist(self)
        raise RuntimeError("Data not parsed yet. Call parse() before result()")

    def parse(self):
        if self.is_parsed:
            return

        if not hasattr(self, 'info') or not hasattr(self, 'criteria') or not self.info or not self.criteria:  # pragma: no cover
            raise RuntimeError("Set smart info with data() or strdata() before running parse()")

        self.offset = int(Offset.FIELD)

        if self.info[Offset.MATCHBOOL] == 1:
            self.is_or = self.criteria[Offset.LOGICTYPE] == 1
            if self.is_or:
                self.conjunctionQuery = " OR "
                self.conjunctionOutput = ' or\n'
                self.queryTree["or"] = self.queryTreeCurrent
                self.fullTree["or"] = self.fullTreeCurrent
            else:
                self.conjunctionQuery = " AND "
                self.conjunctionOutput = ' and\n'
                self.queryTree["and"] = self.queryTreeCurrent
                self.fullTree["and"] = self.fullTreeCurrent

            while True:
                self.again = False

                if len(self.subStack) > 0:
                    if self.subStack[-1]["N"] == 0:
                        old = self.subStack.pop()

                        self.query = old["query"] + \
                            old["conjunctionQuery"] + "( %s )" % self.query
                        self.output = old["output"] + old["conjunctionOutput"] + \
                            "[\n\t%s\n]" % "\n\t".join(self.output.split("\n"))

                        self.conjunctionQuery = old["conjunctionQuery"]
                        self.conjunctionOutput = old["conjunctionOutput"]
                        self.queryTreeCurrent = old["queryTreeCurrent"]
                        self.fullTreeCurrent = old["fullTreeCurrent"]
                    else:
                        self.subStack[-1]["N"] -= 1

                self.logicSignOffset = self.offset + int(Offset.LOGICSIGN)
                self.logicRulesOffset = self.offset + int(Offset.LOGICRULE)
                self.stringOffset = self.offset + int(Offset.STRING)
                self.intAOffset = self.offset + int(Offset.INTA)
                self.intBOffset = self.intAOffset + int(Offset.INTB)
                self.timeMultipleOffset = self.offset + \
                    int(Offset.TIMEMULTIPLE)
                self.timeValueOffset = self.offset + int(Offset.TIMEVALUE)

                if any(self.criteria[self.offset] ==
                       e.value for e in StringFields):
                    self.ProcessStringField()
                elif any(self.criteria[self.offset] == e.value for e in IntFields):
                    self.ProcessIntField()
                elif any(self.criteria[self.offset] == e.value for e in DateFields):
                    self.ProcessDateField()
                elif any(self.criteria[self.offset] == e.value for e in BooleanFields):
                    self.ProcessBooleanField()
                elif any(self.criteria[self.offset] == e.value for e in MediaKindFields):
                    self.ProcessListField(MediaKindFields, MediaKinds, type="mediakind")
                elif any(self.criteria[self.offset] == e.value for e in PlaylistFields):
                    self.ProcessPlaylistField()
                elif any(self.criteria[self.offset] == e.value for e in CloudFields):
                    self.ProcessListField(CloudFields, iCloudStatus, type="cloud")
                elif any(self.criteria[self.offset] == e.value for e in LoveFields):
                    self.ProcessListField(LoveFields, LoveStatus, type="love")
                elif any(self.criteria[self.offset] == e.value for e in LocationFields):
                    self.ProcessListField(LocationFields, LocationKinds, type="location")
                elif self.criteria[self.offset] == 0:
                    # Subexpression

                    self.is_or = self.criteria[self.offset +
                                               Offset.SUBLOGICTYPE] == 1

                    numberOfSubExpression = self._iTunesUint(
                        self.criteria[self.offset + Offset.SUBINT:self.offset + +Offset.SUBINT + 4])

                    self.subStack.append({
                        "query": self.query,
                        "output": self.output,
                        "N": numberOfSubExpression,
                        "conjunctionQuery": self.conjunctionQuery,
                        "conjunctionOutput": self.conjunctionOutput,
                        "queryTreeCurrent": self.queryTreeCurrent,
                        "fullTreeCurrent": self.fullTreeCurrent,
                    })

                    newtree = {}
                    newcurrent = []
                    self.queryTreeCurrent.append(newtree)

                    newfulltree = {}
                    newfulltreecurrent = []
                    self.fullTreeCurrent.append(newfulltree)

                    if self.is_or:
                        self.conjunctionQuery = " OR "
                        self.conjunctionOutput = ' or\n'
                        newtree["or"] = newcurrent
                        newfulltree["or"] = newfulltreecurrent
                    else:
                        self.conjunctionQuery = " AND "
                        self.conjunctionOutput = ' and\n'
                        newtree["and"] = newcurrent
                        newfulltree["and"] = newfulltreecurrent

                    self.query = ""
                    self.output = ""
                    self.queryTreeCurrent = newcurrent
                    self.fullTreeCurrent = newfulltreecurrent

                    self.offset += Offset.SUBEXPRESSIONLENGTH
                    self.again = True
                else:  # pragma: no cover
                    errormessage = "Unkown field: %s" % (hex(self.criteria[self.offset]))
                    logging.warning(errormessage)
                    self.ignore += "Not processed: %s " % errormessage
                    logging.debug(self.criteria[self.offset:self.offset + 100])

                if not self.again:
                    break

        if self.info[Offset.LIMITBOOL] == 1:
            # Limit
            self.limit["number"] = self._iTunesUint(
                self.info[Offset.LIMITINT:Offset.LIMITINT + 4])

            self.limit["type"] = LimitMethods(
                self.info[Offset.LIMITMETHOD]).name

            # Selection
            selectionmethod = SelectionMethods(
                self.info[Offset.SELECTIONMETHOD]).name
            sign = int(self.info[Offset.SELECTIONMETHODSIGN] == 0)
            self.limit["order"] = SelectionMethodsStrings[selectionmethod][1] if isinstance(
                SelectionMethodsStrings[selectionmethod][1],
                str) else SelectionMethodsStrings[selectionmethod][1][sign]

            if len(self.output) > 0:
                self.output += '\n'
            self.output += "Limited to %d %s selected by %s" % (self.limit["number"],
                                                                self.limit["type"],
                                                                SelectionMethodsStrings[selectionmethod][0] if isinstance(
                SelectionMethodsStrings[selectionmethod][0],
                str) else SelectionMethodsStrings[selectionmethod][0][sign])

        if self.info[Offset.LIMITCHECKED] == 1:
            # Exclude unchecked items
            self.limit["onlychecked"] = True

            if len(self.output) > 0:
                self.output += '\n'
            self.output += "Exclude unchecked items"
        else:
            self.limit["onlychecked"] = False

        if self.info[Offset.LIVEUPDATE] == 0:
            # Live Update disabled
            self.limit["liveupdate"] = False

            if len(self.output) > 0:
                self.output += '\n'
            self.output += "Live updating disabled"
        else:
            self.limit["liveupdate"] = True

        t = self.limit
        t["tree"] = self.queryTree
        self.queryTree = t

        t2 = self.limit
        t2["fulltree"] = self.fullTree
        self.fullTree = t2

        self.is_parsed = True

    def ProcessStringField(self):
        end = False
        self.fieldName = StringFields(self.criteria[self.offset]).name
        self.workingOutput = self.fieldName
        self.workingQuery = "(lower(" + self.fieldName + ")"
        self.workingFull = {"field": self.fieldName, "type": "string"}

        KindEval = None

        if self.criteria[self.logicRulesOffset] == LogicRule.Contains:
            if self.criteria[self.logicSignOffset] == LogicSign.StringPositive:
                self.workingOutput += " contains "
                self.workingQuery += " LIKE '%"
                self.workingFull["operator"] = "like"
            else:
                self.workingOutput += " does not contain "
                self.workingQuery += " NOT LIKE '%"
                self.workingFull["operator"] = "not like"
            if self.criteria[self.offset] == StringFields.Kind:
                KindEval = lambda kind, query: query in kind.name
            end = True

        elif self.criteria[self.logicRulesOffset] == LogicRule.Is:
            if self.criteria[self.logicSignOffset] == LogicSign.StringPositive:
                self.workingOutput += " is "
                self.workingQuery += " = '"
                self.workingFull["operator"] = "is"
            else:
                self.workingOutput += " is not "
                self.workingQuery += " != '"
                self.workingFull["operator"] = "is not"
            if self.criteria[self.offset] == StringFields.Kind:
                KindEval = lambda kind, query: query == kind.name

        elif self.criteria[self.logicRulesOffset] == LogicRule.Starts:
            self.workingOutput += " starts with "
            self.workingQuery += " Like '"
            self.workingFull["operator"] = "starts with"
            if self.criteria[self.offset] == StringFields.Kind:
                KindEval = lambda kind, query: query not in kind.name
            end = True

        elif self.criteria[self.logicRulesOffset] == LogicRule.Ends:
            self.workingOutput += " ends with "
            self.workingQuery += " Like '%"
            self.workingFull["operator"] = "ends with"
            if self.criteria[self.offset] == StringFields.Kind:
                KindEval = lambda kind, query: kind.name.index(query) == len(kind.name) - len(query)
            end = True

        self.workingOutput += '"'
        self.content = ""
        onByte = True
        for i in range(self.stringOffset, len(self.criteria)):
            if onByte:
                if self.criteria[i] == 0 and i != len(self.criteria) - 1:
                    self.FinishStringField(end, KindEval)
                    self.offset = i + 2
                    self.again = True
                    return
                self.content += chr(self.criteria[i])
            onByte = not onByte
        self.FinishStringField(end, KindEval)
        return

    def FinishStringField(self, end, KindEval):
        self.workingOutput += self.content
        self.workingOutput += '" '
        failed = False
        if self.criteria[self.offset] == StringFields.Kind:
            self.workingQuery = ""
            for kind in FileKinds:
                if KindEval(kind, self.content):
                    if len(self.workingQuery) > 0:
                        if (len(self.query) == 0 and not self.again) or self.is_or:
                            self.workingQuery += " OR "
                        else:
                            failed = True
                            break

                    self.workingQuery += "(lower(Uri)"
                    self.workingQuery += (" LIKE '%" +
                                          kind.extension +
                                          "')") if self.criteria[self.logicSignOffset] == LogicSign.StringPositive else (" NOT LIKE '%" +
                                                                                                                         kind.extension +
                                                                                                                         "%')")
                    self.workingFull["kind_value"] = kind.extension
                    self.workingFull["kind_operator"] = "like" if self.criteria[
                        self.logicSignOffset] == LogicSign.StringPositive else "not like"
        else:
            self.workingQuery += self.content.lower()
            self.workingQuery += "%')" if end else "')"
            self.workingFull["value"] = self.content

        if len(self.ignore) > 0:
            self.ignore += self.conjunctionOutput

        if failed:
            self.ignore += self.workingOutput
        else:
            if len(self.output) > 0:
                self.output += self.conjunctionOutput
            self.output += self.workingOutput

            if len(self.query) > 0:
                self.query += self.conjunctionQuery
            self.query += self.workingQuery

            self.queryTreeCurrent.append((self.fieldName, self.workingQuery))
            self.fullTreeCurrent.append(self.workingFull)

    def ProcessIntField(self):
        self.fieldName = IntFields(self.criteria[self.offset]).name
        self.workingOutput = self.fieldName
        self.workingQuery = "(" + self.fieldName
        self.workingFull = {"field": self.fieldName, "type": "int"}

        if self.criteria[self.logicRulesOffset] == LogicRule.Is:
            number = self._iTunesUint(
                self.criteria[self.intAOffset:self.intAOffset + 4], self.criteria[self.offset] == IntFields.Rating)
            if self.criteria[self.logicSignOffset] == LogicSign.IntPositive:
                self.workingOutput += " is %d" % number
                self.workingQuery += " = %d" % number
                self.workingFull["operator"] = "is"
                self.workingFull["value"] = number
            else:
                self.workingOutput += " is not %d" % number
                self.workingQuery += " != %d" % number
                self.workingFull["operator"] = "is not"
                self.workingFull["value"] = number

        elif self.criteria[self.logicRulesOffset] == LogicRule.Greater:
            number = self._iTunesUint(
                self.criteria[self.intAOffset:self.intAOffset + 4], self.criteria[self.offset] == IntFields.Rating)
            self.workingOutput += " is greater than %d" % number
            self.workingQuery += " > %d" % number
            self.workingFull["operator"] = "greater than"
            self.workingFull["value"] = number

        elif self.criteria[self.logicRulesOffset] == LogicRule.Less:
            number = self._iTunesUint(
                self.criteria[self.intAOffset:self.intAOffset + 4], self.criteria[self.offset] == IntFields.Rating)
            self.workingOutput += " is less than %d" % number
            self.workingQuery += " < %d" % number
            self.workingFull["operator"] = "less than"
            self.workingFull["value"] = number

        elif self.criteria[self.logicRulesOffset] == LogicRule.Other:
            if self.criteria[self.logicSignOffset + 2] == 1:
                numberA = self._iTunesUint(
                    self.criteria[self.intAOffset:self.intAOffset + 4], self.criteria[self.offset] == IntFields.Rating)
                numberB = self._iTunesUint(
                    self.criteria[self.intBOffset:self.intBOffset + 4], self.criteria[self.offset] == IntFields.Rating)
                self.workingOutput += " is in the range of %d to %d" % (
                    numberA, numberB)
                self.workingQuery += " BETWEEN %d AND %d" % (numberA, numberB)
                self.workingFull["operator"] = "between"
                self.workingFull["value"] = (numberA, numberB)

            else:
                numberA = self._iTunesUint(
                    self.criteria[self.intAOffset:self.intAOffset + 4], self.criteria[self.offset] == IntFields.Rating)
                numberB = self._iTunesUint(
                    self.criteria[self.intBOffset:self.intBOffset + 4], self.criteria[self.offset] == IntFields.Rating)
                if numberA == numberB:
                    if self.criteria[self.logicSignOffset] == LogicSign.IntPositive:
                        self.workingOutput += " is %d" % numberA
                        self.workingQuery += " = %d" % numberA
                        self.workingFull["operator"] = "is"
                        self.workingFull["value"] = numberA
                    else:
                        self.workingOutput += " is not %d" % numberA
                        self.workingQuery += " != %d" % numberA
                        self.workingFull["operator"] = "is not"
                        self.workingFull["value"] = numberA
                else:  # pragma: no cover
                    errormessage = "Unkown case in ProcessIntField:LogicRule.Other: a=%d and b=%d" % (numberA, numberB)
                    logging.warning(errormessage)
                    self.ignore += " Not processed: %s " % errormessage

                    self.workingOutput += " ##UnkownCase IntField: LogicRule.Other##"
                    self.workingQuery += " ##UnkownCase IntField: LogicRule.Other##"

        self.workingQuery += ")"

        if len(self.output) > 0:
            self.output += self.conjunctionOutput

        if len(self.query) > 0:
            self.query += self.conjunctionQuery

        self.output += self.workingOutput
        self.query += self.workingQuery
        self.queryTreeCurrent.append((self.fieldName, self.workingQuery))
        self.fullTreeCurrent.append(self.workingFull)

        self.offset = self.intAOffset + Offset.INTLENGTH
        if len(self.criteria) > self.offset:
            self.again = True

    def ProcessPlaylistField(self):
        self.fieldName = PlaylistFields(self.criteria[self.offset]).name
        self.workingOutput = self.fieldName
        self.workingQuery = "(" + self.fieldName
        self.workingFull = {"field": self.fieldName, "type": "playlist"}

        if self.criteria[self.logicRulesOffset] == LogicRule.Is:
            idpart0 = self._iTunesUint(
                self.criteria[self.intAOffset - 4:self.intAOffset], self.criteria[self.offset] == IntFields.Rating)
            idpart1 = self._iTunesUint(
                self.criteria[self.intAOffset:self.intAOffset + 4], self.criteria[self.offset] == IntFields.Rating)

            if self.criteria[self.logicSignOffset] == LogicSign.IntPositive:
                self.workingOutput += " is %s%s" % (
                    hex(idpart0)[2:].upper(), hex(idpart1)[2:].upper())
                self.workingQuery += " = '%s%s'" % (
                    hex(idpart0)[2:].upper(), hex(idpart1)[2:].upper())
                self.workingFull["operator"] = "is"
                self.workingFull["value"] = "%s%s" % (
                    hex(idpart0)[2:].upper(), hex(idpart1)[2:].upper())
            else:
                self.workingOutput += " is not %s%s" % (
                    hex(idpart0)[2:].upper(), hex(idpart1)[2:].upper())
                self.workingQuery += " != '%s%s'" % (
                    hex(idpart0)[2:].upper(), hex(idpart1)[2:].upper())
                self.workingFull["operator"] = "is not"
                self.workingFull["value"] = "%s%s" % (
                    hex(idpart0)[2:].upper(), hex(idpart1)[2:].upper())

        else:  # pragma: no cover
            errormessage = "Unkown logic rule in ProcessPlaylistField: LogicRule=%d" % self.criteria[self.logicRulesOffset]
            logging.warning(errormessage)
            self.ignore += " Not processed: %s " % errormessage
            self.workingOutput += " ##UnkownCase PlaylistField:LogicRule##"
            self.workingQuery += " ##UnkownCase PlaylistField:LogicRule##"

        self.workingQuery += ")"

        if len(self.output) > 0:
            self.output += self.conjunctionOutput

        if len(self.query) > 0:
            self.query += self.conjunctionQuery

        self.output += self.workingOutput
        self.query += self.workingQuery
        self.queryTreeCurrent.append((self.fieldName, self.workingQuery))
        self.fullTreeCurrent.append(self.workingFull)

        self.offset = self.intAOffset + Offset.INTLENGTH
        if len(self.criteria) > self.offset:
            self.again = True

    def ProcessBooleanField(self):
        self.fieldName = BooleanFields(self.criteria[self.offset]).name
        self.workingOutput = self.fieldName
        self.workingQuery = "(" + self.fieldName
        self.workingFull = {"field": self.fieldName, "type": "boolean"}

        if self.criteria[self.logicRulesOffset] == LogicRule.Is:
            value = self.criteria[self.logicSignOffset] != LogicSign.IntPositive
            boolstr = "True" if value == 1 else "False"

            self.workingOutput += " is %s" % (boolstr)
            self.workingQuery += " = %d" % (value)
            self.workingFull["operator"] = "is"
            self.workingFull["value"] = value == 1

        else:  # pragma: no cover
            errormessage = "Unkown logic rule in ProcessBooleanField: LogicRule=%d" % self.criteria[self.logicRulesOffset]
            logging.warning(errormessage)
            self.ignore += " Not processed: %s " % errormessage
            self.workingOutput += " ##UnkownCase BooleanField:LogicRule##"
            self.workingQuery += " ##UnkownCase BooleanField:LogicRule##"

        self.workingQuery += ")"

        if len(self.output) > 0:
            self.output += self.conjunctionOutput

        if len(self.query) > 0:
            self.query += self.conjunctionQuery

        self.output += self.workingOutput
        self.query += self.workingQuery
        self.queryTreeCurrent.append((self.fieldName, self.workingQuery))
        self.fullTreeCurrent.append(self.workingFull)

        self.offset = self.intAOffset + Offset.INTLENGTH
        if len(self.criteria) > self.offset:
            self.again = True

    def ProcessDateField(self):
        self.fieldName = DateFields(self.criteria[self.offset]).name
        self.workingOutput = self.fieldName
        self.workingQuery = "TIMESTAMP(%s)" % self.fieldName
        self.workingFull = {"field": self.fieldName, "type": "date"}

        if self.criteria[self.logicRulesOffset] == LogicRule.Greater:
            timestamp = self._iTunesDate(
                self.criteria[self.intAOffset:self.intAOffset + 4])
            self.workingOutput += " is after %s" % self._dateString(timestamp)
            self.workingQuery += " > %d" % timestamp
            self.workingFull["operator"] = "is after"
            self.workingFull["value"] = timestamp
        elif self.criteria[self.logicRulesOffset] == LogicRule.Less:
            timestamp = self._iTunesDate(
                self.criteria[self.intAOffset:self.intAOffset + 4])
            self.workingOutput += " is before %s" % self._dateString(timestamp)
            self.workingQuery += " < %d" % timestamp
            self.workingFull["operator"] = "is before"
            self.workingFull["value"] = timestamp
        elif self.criteria[self.logicRulesOffset] == LogicRule.Other:
            if self.criteria[self.logicSignOffset + 2] == 1:
                timestampA = self._iTunesDate(
                    self.criteria[self.intAOffset:self.intAOffset + 4])
                timestampB = self._iTunesDate(
                    self.criteria[self.intBOffset:self.intBOffset + 4])
                if self.criteria[self.logicSignOffset] == LogicSign.IntPositive:
                    self.workingOutput += " is in the range of %s to %s" % (
                        self._dateString(timestampA), self._dateString(timestampB))
                    self.workingQuery += " BETWEEN %d AND %d" % (
                        timestampA, timestampB)
                    self.workingFull["operator"] = "is in the range"
                    self.workingFull["value"] = (timestampA, timestampB)
                    self.workingFull["value_date"] = (
                        self._dateString(timestampA), self._dateString(timestampB))
                else:
                    self.workingOutput += " is not in the range of %s to %s" % (
                        self._dateString(timestampA), self._dateString(timestampB))
                    self.workingQuery += " NOT BETWEEN %d AND %d" % (
                        timestampA, timestampB)
                    self.workingFull["operator"] = "is not in the range"
                    self.workingFull["value"] = (timestampA, timestampB)
                    self.workingFull["value_date"] = (
                        self._dateString(timestampA), self._dateString(timestampB))
            elif self.criteria[self.logicSignOffset + 2] == 2:
                if self.criteria[self.logicSignOffset] == LogicSign.IntPositive:
                    self.workingOutput += " is in the last "
                    self.workingQuery = "(TIMESTAMP(NOW()) - TIMESTAMP(%s)) < " % self.fieldName
                    self.workingFull["operator"] = "is in the last"
                else:
                    self.workingOutput += " is not in the last "
                    self.workingQuery = "(TIMESTAMP(NOW()) - TIMESTAMP(%s)) > " % self.fieldName
                    self.workingFull["operator"] = "is not in the last"

                t = (self._iTunesUint(bytes(
                    [255 - c for c in self.criteria[self.timeValueOffset:self.timeValueOffset + 4]])) + 1) % 4294967296
                multiple = self._iTunesUint(
                    self.criteria[self.timeMultipleOffset:self.timeMultipleOffset + 4])
                self.workingQuery += "%d" % (t * multiple)
                self.workingFull["value"] = t * multiple
                if multiple == 86400:
                    self.workingOutput += "%d days" % t
                    self.workingFull["value_date"] = "%d days" % t
                elif multiple == 604800:
                    self.workingOutput += "%d weeks" % t
                    self.workingFull["value_date"] = "%d weeks" % t
                elif multiple == 2628000:
                    self.workingOutput += "%d months" % t
                    self.workingFull["value_date"] = "%d months" % t
                else:  # pragma: no cover
                    self.workingOutput += "%d*%d seconds" % (multiple, t)
                    self.workingFull["value_date"] = "%d*%d seconds" % (
                        multiple, t)
                    errormessage = "##UnkownCase DateField: LogicRule.Other: multiple '%d' is unkown##" % multiple
                    logging.warning(errormessage)
                    self.ignore += " Not processed: %s " % errormessage

        if len(self.output) > 0:
            self.output += self.conjunctionOutput

        if len(self.query) > 0:
            self.query += self.conjunctionQuery

        self.output += self.workingOutput
        self.query += self.workingQuery
        self.queryTreeCurrent.append((self.fieldName, self.workingQuery))
        self.fullTreeCurrent.append(self.workingFull)

        self.offset = self.intAOffset + Offset.INTLENGTH
        if len(self.criteria) > self.offset:
            self.again = True

    def ProcessListField(self, fields, valueDict, type="list"):
        self.fieldName = fields(self.criteria[self.offset]).name
        self.workingOutput = self.fieldName
        self.workingQuery = "(" + self.fieldName
        self.workingFull = {"field": self.fieldName, "type": type}

        if self.criteria[self.logicRulesOffset] == LogicRule.Is:
            number = self._iTunesUint(
                self.criteria[self.intAOffset:self.intAOffset + 4], self.criteria[self.offset] == IntFields.Rating)
            if self.criteria[self.logicSignOffset] == LogicSign.IntPositive:
                self.workingOutput += " is %s" % valueDict[number]
                self.workingQuery += " = '%s'" % valueDict[number]
                self.workingFull["operator"] = "is"
                self.workingFull["value"] = valueDict[number]

            else:
                self.workingOutput += " is not %s" % valueDict[number]
                self.workingQuery += " != '%s'" % valueDict[number]
                self.workingFull["operator"] = "is not"
                self.workingFull["value"] = valueDict[number]

        elif self.criteria[self.logicRulesOffset] == LogicRule.Other:
            numberA = self._iTunesUint(
                self.criteria[self.intAOffset:self.intAOffset + 4], self.criteria[self.offset] == IntFields.Rating)
            numberB = self._iTunesUint(
                self.criteria[self.intBOffset:self.intBOffset + 4], self.criteria[self.offset] == IntFields.Rating)
            if numberA == numberB:
                if self.criteria[self.logicSignOffset] == LogicSign.IntPositive:
                    self.workingOutput += " is %s" % valueDict[numberA]
                    self.workingQuery += " = '%s'" % valueDict[numberA]
                    self.workingFull["operator"] = "is"
                    self.workingFull["value"] = valueDict[numberA]
                else:
                    self.workingOutput += " is not %s" % valueDict[numberA]
                    self.workingQuery += " != '%s'" % valueDict[numberA]
                    self.workingFull["operator"] = "is not"
                    self.workingFull["value"] = valueDict[numberA]

            else:  # pragma: no cover
                errormessage = "Unkown case in ProcessListField %s:LogicRule.Other: %d != %d" % (self.fieldName, numberA, numberB)
                logging.warning(errormessage)
                self.ignore += " Not processed: %s " % errormessage

                self.workingOutput += " ##UnkownCase ListField %s: LogicRule.Other##" % self.fieldName
                self.workingQuery += " ##UnkownCase ListField %s: LogicRule.Other##" % self.fieldName
        else:  # pragma: no cover
            errormessage = "Unkown logic rule in ProcessListField %s: LogicRule=%d" % (self.fieldName, self.criteria[self.logicRulesOffset])
            logging.warning(errormessage)
            self.ignore += " Not processed: %s " % errormessage

            self.workingOutput += " ##UnkownCase ListField %s:LogicRule##" % self.fieldName
            self.workingQuery += " ##UnkownCase ListField %s:LogicRule##" % self.fieldName

        self.workingQuery += ")"

        if len(self.output) > 0:
            self.output += self.conjunctionOutput

        if len(self.query) > 0:
            self.query += self.conjunctionQuery

        self.output += self.workingOutput
        self.query += self.workingQuery
        self.queryTreeCurrent.append((self.fieldName, self.workingQuery))
        self.fullTreeCurrent.append(self.workingFull)

        self.offset = self.intAOffset + Offset.INTLENGTH
        if len(self.criteria) > self.offset:
            self.again = True

    @staticmethod
    def _iTunesUint(bytearr, divideby=False, denominator=20):
        num = struct.unpack('>I', bytearr)[0]
        if divideby:  # For rating/stars by 20
            num = int(num / denominator)
        return num

    @classmethod
    def _iTunesDate(cls, bytearr):
        timestamp = cls._iTunesUint(bytearr)
        return timestamp + DateStartFromUnix

    @staticmethod
    def _dateString(timestamp):
        return datetime.datetime.utcfromtimestamp(
            int(timestamp)).strftime('%Y-%m-%dT%H:%M:%SZ')
