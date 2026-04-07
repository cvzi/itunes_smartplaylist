"""
Module holding the parsing algorithm
"""

import sys
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
            self.current_operator = self._operatorFromLogicType(self.criteria[Offset.LOGICTYPE])
            self.queryTree[self.current_operator] = self.queryTreeCurrent
            self.fullTree[self.current_operator] = self.fullTreeCurrent

            while True:
                self.again = False

                if len(self.subStack) > 0:
                    if self.subStack[-1]["N"] == 0:
                        old = self.subStack.pop()

                        self.current_operator = old["operator"]
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
                    self.ProcessListField(MediaKindFields, MediaKinds, listtype="mediakind")
                elif any(self.criteria[self.offset] == e.value for e in PlaylistFields):
                    self.ProcessPlaylistField()
                elif any(self.criteria[self.offset] == e.value for e in CloudFields):
                    self.ProcessListField(CloudFields, iCloudStatus, listtype="cloud")
                elif any(self.criteria[self.offset] == e.value for e in LoveFields):
                    self.ProcessListField(LoveFields, LoveStatus, listtype="love")
                elif any(self.criteria[self.offset] == e.value for e in LocationFields):
                    self.ProcessListField(LocationFields, LocationKinds, listtype="location")
                elif self.criteria[self.offset] == 0:
                    # Subexpression

                    parent_operator = self.current_operator
                    subgroup_operator = self._operatorFromLogicType(self.criteria[self.offset + Offset.SUBLOGICTYPE])

                    numberOfSubExpression = self._iTunesUint(
                        self.criteria[self.offset + Offset.SUBINT:self.offset + Offset.SUBINT + 4])

                    self.subStack.append({
                        "N": numberOfSubExpression,
                        "operator": parent_operator,
                        "queryTreeCurrent": self.queryTreeCurrent,
                        "fullTreeCurrent": self.fullTreeCurrent,
                    })

                    newtree = {}
                    newcurrent = []
                    self.queryTreeCurrent.append(newtree)

                    newfulltree = {}
                    newfulltreecurrent = []
                    self.fullTreeCurrent.append(newfulltree)

                    newtree[subgroup_operator] = newcurrent
                    newfulltree[subgroup_operator] = newfulltreecurrent

                    self.current_operator = subgroup_operator
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

        self.query = self._buildQuery(self._stripImplicitMediaKindFilter(self.root))
        self.output = self._buildOutputTree(self._stripImplicitMediaKindFilter(self.fullTreeRoot))

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
            self.workingFull["value"] = self.content
            self.workingQuery = ""
            for kind in FileKinds:
                if KindEval(kind, self.content):
                    if len(self.workingQuery) > 0:
                        if (len(self.queryTreeCurrent) == 0 and not self.again) or self.current_operator == "or":
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
            self.ignore += " or\n" if self.current_operator == "or" else " and\n"

        if failed:
            self.ignore += self.workingOutput
        else:
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
                self.workingOutput += " is %s" % self._formatPersistentID(idpart0, idpart1)
                self.workingQuery += " = '%s'" % self._formatPersistentID(idpart0, idpart1)
                self.workingFull["operator"] = "is"
                self.workingFull["value"] = "%s" % self._formatPersistentID(idpart0, idpart1)
            else:
                self.workingOutput += " is not %s" % self._formatPersistentID(idpart0, idpart1)
                self.workingQuery += " != '%s'" % self._formatPersistentID(idpart0, idpart1)
                self.workingFull["operator"] = "is not"
                self.workingFull["value"] = "%s" % self._formatPersistentID(idpart0, idpart1)

        else:  # pragma: no cover
            errormessage = "Unkown logic rule in ProcessPlaylistField: LogicRule=%d" % self.criteria[self.logicRulesOffset]
            logging.warning(errormessage)
            self.ignore += " Not processed: %s " % errormessage
            self.workingOutput += " ##UnkownCase PlaylistField:LogicRule##"
            self.workingQuery += " ##UnkownCase PlaylistField:LogicRule##"

        self.workingQuery += ")"

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

        self.queryTreeCurrent.append((self.fieldName, self.workingQuery))
        self.fullTreeCurrent.append(self.workingFull)

        self.offset = self.intAOffset + Offset.INTLENGTH
        if len(self.criteria) > self.offset:
            self.again = True

    def ProcessListField(self, fields, valueDict, listtype="list"):
        self.fieldName = fields(self.criteria[self.offset]).name
        self.workingOutput = self.fieldName
        self.workingQuery = "(" + self.fieldName
        self.workingFull = {"field": self.fieldName, "type": listtype}

        if self.criteria[self.logicRulesOffset] == LogicRule.Is:
            number = self._iTunesUint(
                self.criteria[self.intAOffset:self.intAOffset + 4], self.criteria[self.offset] == IntFields.Rating)
            value = self._lookupListValue(valueDict, number, self.fieldName, listtype)
            if self.criteria[self.logicSignOffset] == LogicSign.IntPositive:
                self.workingOutput += " is %s" % value
                self.workingQuery += " = '%s'" % value
                self.workingFull["operator"] = "is"
                self.workingFull["value"] = value

            else:
                self.workingOutput += " is not %s" % value
                self.workingQuery += " != '%s'" % value
                self.workingFull["operator"] = "is not"
                self.workingFull["value"] = value

        elif self.criteria[self.logicRulesOffset] == LogicRule.Other:
            numberA = self._iTunesUint(
                self.criteria[self.intAOffset:self.intAOffset + 4], self.criteria[self.offset] == IntFields.Rating)
            numberB = self._iTunesUint(
                self.criteria[self.intBOffset:self.intBOffset + 4], self.criteria[self.offset] == IntFields.Rating)
            if numberA == numberB:
                value = self._lookupListValue(valueDict, numberA, self.fieldName, listtype)
                if self.criteria[self.logicSignOffset] == LogicSign.IntPositive:
                    self.workingOutput += " is %s" % value
                    self.workingQuery += " = '%s'" % value
                    self.workingFull["operator"] = "is"
                    self.workingFull["value"] = value
                else:
                    self.workingOutput += " is not %s" % value
                    self.workingQuery += " != '%s'" % value
                    self.workingFull["operator"] = "is not"
                    self.workingFull["value"] = value

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
        if sys.version_info < (3, 11):
            return datetime.datetime.utcfromtimestamp(
                int(timestamp)).strftime('%Y-%m-%dT%H:%M:%SZ')
        return datetime.datetime.fromtimestamp(
            int(timestamp), datetime.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')

    @staticmethod
    def _formatPersistentID(idpart0, idpart1):
        return '{:08X}{:08X}'.format(idpart0, idpart1)

    @staticmethod
    def _operatorFromLogicType(logictype):
        if logictype == 1:
            return "or"
        if logictype == 0:
            return "and"

        logging.error("Unknown logic type encountered: %d; defaulting to 'and'", logictype)
        return "and"

    @staticmethod
    def _lookupListValue(valueDict, number, fieldName="unknown", listtype="list"):
        if number in valueDict:
            return valueDict[number]
        logging.warning("Unknown %s list value encountered for %s: %d", listtype, fieldName, number)
        return "UnknownValue[%d]" % number

    def _buildQuery(self, node, nested=False):
        if not node:
            return ""

        if isinstance(node, tuple):
            return node[1]

        if isinstance(node, dict):
            if "and" in node:
                rendered = " AND ".join(
                    filter(None, (self._buildQuery(child, nested=True) for child in node["and"]))
                )
            elif "or" in node:
                rendered = " OR ".join(
                    filter(None, (self._buildQuery(child, nested=True) for child in node["or"]))
                )
            else:
                return ""
            if not rendered:
                return ""
            if nested:
                return "( %s )" % rendered
            return rendered

        return ""

    def _stripImplicitMediaKindFilter(self, node):
        if not isinstance(node, dict) or "and" not in node:
            return node

        children = list(node["and"])
        if len(children) < 2 or not self._isImplicitMediaKindFilter(children[0]):
            return node

        remaining = children[1:]
        if len(remaining) == 1:
            return remaining[0]
        return {"and": remaining}

    @staticmethod
    def _isImplicitMediaKindFilter(node):
        if isinstance(node, tuple):
            return node[0] == "MediaKind" and node[1] in {
                "(MediaKind = 'Music')",
                "(MediaKind = 'Music Video')",
            }

        if isinstance(node, dict) and "or" not in node:
            return (
                node.get("field") == "MediaKind" and
                node.get("operator") == "is" and
                node.get("value") in {"Music", "Music Video"}
            )

        if not isinstance(node, dict) or "or" not in node:
            return False

        values = []
        for child in node["or"]:
            if isinstance(child, tuple):
                if child[0] != "MediaKind":
                    return False
                if child[1] == "(MediaKind = 'Music')":
                    values.append("Music")
                elif child[1] == "(MediaKind = 'Music Video')":
                    values.append("Music Video")
                else:
                    return False
            elif isinstance(child, dict):
                if child.get("field") != "MediaKind" or child.get("operator") != "is":
                    return False
                if child.get("value") not in {"Music", "Music Video"}:
                    return False
                values.append(child["value"])
            else:
                return False

        return sorted(values) == ["Music", "Music Video"]

    def _buildOutputTree(self, node, nested=False):
        if not node:
            return ""

        if isinstance(node, dict):
            if "and" in node:
                rendered = ' and\n'.join(
                    filter(None, (self._buildOutputTree(child, nested=True) for child in node["and"]))
                )
                return self._formatNestedOutput(rendered) if nested else rendered
            if "or" in node:
                rendered = ' or\n'.join(
                    filter(None, (self._buildOutputTree(child, nested=True) for child in node["or"]))
                )
                return self._formatNestedOutput(rendered) if nested else rendered
            return self._renderOutputLeaf(node)

        return ""

    @staticmethod
    def _formatNestedOutput(rendered):
        if not rendered:
            return ""
        return "[\n\t%s\n]" % "\n\t".join(rendered.split("\n"))

    def _renderOutputLeaf(self, node):
        field = node["field"]
        operator = node["operator"]
        value = node.get("value_date", node.get("value"))

        if node["type"] == "string":
            if operator == "like":
                return '%s contains "%s" ' % (field, value)
            if operator == "not like":
                return '%s does not contain "%s" ' % (field, value)
            if operator == "is":
                return '%s is "%s" ' % (field, value)
            if operator == "is not":
                return '%s is not "%s" ' % (field, value)
            if operator == "starts with":
                return '%s starts with "%s" ' % (field, value)
            if operator == "ends with":
                return '%s ends with "%s" ' % (field, value)

        if operator == "is":
            return "%s is %s" % (field, value)

        if operator == "is not":
            return "%s is not %s" % (field, value)

        if operator in {"is in the range", "is not in the range"} and isinstance(value, tuple):
            return "%s %s of %s to %s" % (field, operator, value[0], value[1])

        if operator in {"greater than", "less than", "is after", "is before", "is in the last", "is not in the last"}:
            connector = " " if operator.startswith("is ") else " is "
            return "%s%s%s" % (field, connector, value)

        if operator == "between" and isinstance(value, tuple):
            return "%s is in the range of %s to %s" % (field, value[0], value[1])

        if operator == "not between" and isinstance(value, tuple):
            return "%s is not in the range of %s to %s" % (field, value[0], value[1])

        return "%s %s %s" % (field, operator, value)
