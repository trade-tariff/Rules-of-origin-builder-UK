import re
import json
import os

from classes.normalizer import Normalizer
from classes.rule import Rule
import classes.globals as g


class RuleSetLegacy(object):
    def __init__(self, row, footnotes_lookup):
        self.hierarchy_divider = " ➔ "
        self.hierarchy_divider = " ▸ "
        self.heading = ""
        self.footnotes_lookup = footnotes_lookup
        self.switched_heading = ""
        self.subdivision = ""
        self.rule = ""
        self.is_ex_code = False
        self.parts = []
        self.rules = []
        self.is_subdivision = False
        self.min = None
        self.max = None
        self.valid = False
        self.chapter = -1
        self.headings = []
        self.subheadings = []

        if row is not None:
            # A rule set essentially equates to a row on the table
            self.original_heading = row["original_heading"].strip()
            self.description = ""
            self.subdivision = row["description"].strip()
            self.subdivision = self.subdivision.replace("; except for:", "")
            self.subdivision = self.subdivision.replace("\n<b>", "<br><b>")

            # Run the corrections
            corrections_file = os.path.join(os.getcwd(), "data", "corrections.json")
            f = open(corrections_file)
            corrections = json.load(f)
            for correction in corrections:
                self.subdivision = self.subdivision.replace(correction["from"], correction["to"])

            self.original_rule = row["original_rule"].strip()
            self.original_rule = self.original_rule.replace("Manufacture;", "Manufacture:")
            self.original_rule2 = row["original_rule2"].strip()

            # Before
            if "Chapter 16" in self.original_heading:
                a = 1
            self.original_rule = self.deal_with_semicolons_in_manufacture_rules(self.original_rule)

            # Concatenate the two columns of rules into one
            if self.original_rule2 != "":
                self.original_rule2 = self.deal_with_semicolons_in_manufacture_rules(self.original_rule2)
                self.original_rule += ";\n\n"
                self.original_rule += "or\n\n" + self.original_rule2

            # self.switch_headings()

            self.process_heading()
            self.process_subdivision()
            self.process_rule()
            self.capture_parent_description()
            self.set_valid_status()

    def deal_with_semicolons_in_manufacture_rules(self, s):
        if "0403" in self.original_heading:
            a = 1
        ret = s.strip()
        ret = ret.replace("Manufacture in which;", "Manufacture in which:")
        if ret.startswith("Manufacture:") or ret.startswith("Manufacture in which:"):
            if ret.count("Manufacture") == 1:
                ret = ret.replace(";", "")
            ret = ret.replace("\n", "\n- ")
            ret = ret.replace("\n- \n", "\n\n")
            ret = ret.replace("\n- - ", "\n- ")
            a = 1

        return ret

    def capture_parent_description(self):
        self.original_rule = self.original_rule.strip()
        if self.original_rule == "" or self.original_rule == "-":
            g.parent_heading = self.subdivision

    def set_valid_status(self):
        for rule in self.rules:
            if rule["rule"] != "-" and rule["rule"] != "":
                self.valid = True
                break

    def process_heading(self):
        self.original_heading = re.sub("([0-9]{4}) and ([0-9]{4})", "\\1 to \\2", self.original_heading)
        self.original_heading = self.original_heading.replace(u'\xa0', u' ')
        self.original_heading = self.original_heading.replace("ex ex", "ex ")
        self.original_heading = self.original_heading.replace("\n", " ")
        self.original_heading = re.sub(" {2,10}", " ", self.original_heading)

        if "300670" in self.original_heading:
            a = 1
        n = Normalizer()
        self.heading = n.normalize(self.original_heading)

        self.heading = self.heading.replace(".", "")
        self.heading = self.heading.replace(" - ", "-")
        self.heading = self.heading.replace(" to ", "-")

        self.get_heading_class()

        if "-" in self.original_heading or " to " in self.original_heading:
            self.determine_minmax_from_range()
        else:
            self.determine_minmax_from_single_term()

    def get_heading_class(self):
        # print(self.heading)
        tmp = self.heading.lower()
        self.is_ex_code = False
        self.is_range = False
        self.is_chapter = False
        self.is_heading = False
        self.is_subheading = False

        # Check if this is the chapter and get the chapter number
        if "chapter" in tmp:
            self.is_chapter = True
            tmp2 = tmp.replace("ex", "").strip()
            tmp2 = tmp2.replace("chapter", "").strip()
            tmp2 = int(tmp2)
            self.chapter = tmp2
        else:
            tmp2 = tmp.replace("ex", "").strip()
            tmp2 = tmp2.strip()[0:2]
            tmp2 = int(tmp2)
            self.chapter = tmp2

        # Check if this is an excode
        if "ex" in tmp:
            self.is_ex_code = True

        # Check if this is a range
        tmp = tmp.replace("-", " to ")
        tmp = tmp.replace("and", " to ")
        tmp = tmp.replace("  ", " ")
        if "to" in tmp:
            self.is_range = True

        # Check if this is a heading / subheading
        if tmp == "2002 to 2003":
            a = 1
        tmp = tmp.replace("ex ex", "").strip()
        tmp = tmp.replace("ex", "").strip()
        if self.is_range:
            parts = tmp.split("to")
            part = parts[0].strip()
            if len(part) == 4:
                self.is_heading = True
            elif len(part) == 6:
                self.is_subheading = True
        else:
            if len(tmp) == 4:
                self.is_heading = True
            elif len(tmp) == 6:
                self.is_subheading = True

    def determine_minmax_from_single_term(self):
        tmp = self.heading.lower()
        tmp = tmp.replace("ex ", "")
        if self.is_chapter:
            tmp = tmp.replace("chapter", "").strip().rjust(2, "0")
            self.min = tmp + "00000000"
            self.max = tmp + "99999999"
        elif self.is_heading:
            tmp = tmp.replace(" ", "").strip()
            self.headings.append(tmp)
            self.min = g.format_parts(tmp, 0)
            self.max = g.format_parts(tmp, 1)
        elif self.is_subheading:
            tmp = tmp.replace(" ", "").strip()
            self.headings.append(tmp[0:4])
            self.subheadings.append(tmp)
            self.min = g.format_parts(tmp, 0)
            self.max = g.format_parts(tmp, 1)

    def determine_minmax_from_range(self):
        if "-" in self.heading:
            parts = self.heading.split("-")
        elif "to" in self.heading:
            parts = self.heading.split("to")

        for i in range(0, len(self.parts)):
            parts[i] = parts[i].replace(" ", "")

        # Work out the min and max of a range
        index = 0
        for part in parts:
            if index == 0:
                self.min = g.format_parts(part, index)
            else:
                self.max = g.format_parts(part, index)
            index += 1

        if self.is_heading:
            # Work out the headings that this rule_set covers
            self.headings.append(parts[0])
            tmp_min = int(parts[0])
            tmp_max = int(parts[1])
            proceed = True
            while proceed:
                tmp_min += 1
                str_min = str(tmp_min).rjust(4, "0")
                if str_min in g.all_headings:
                    self.headings.append(str_min)
                if tmp_min == tmp_max:
                    proceed = False
        elif self.is_subheading:
            # Work out the subheadings that this rule_set covers
            self.subheadings.append(parts[0])
            tmp_min = int(parts[0])
            tmp_max = int(parts[1])
            proceed = True
            while proceed:
                tmp_min += 1
                str_min = str(tmp_min).rjust(6, "0")
                if str_min in g.all_subheadings:
                    self.subheadings.append(str_min)
                if tmp_min == tmp_max:
                    proceed = False

    def process_subdivision(self):
        # Especially dodgy hyphen chars
        self.subdivision = self.subdivision.replace("—", "–")
        self.subdivision = self.subdivision.replace("–", "-")
        # self.subdivision = self.subdivision.replace("-", "- ")
        self.subdivision = self.subdivision.replace("  ", " ")

        n = Normalizer()
        self.subdivision = n.normalize(self.subdivision).strip()
        self.subdivision = self.subdivision.replace(" %", "%")
        self.subdivision = self.subdivision.replace("— ", "\n- ")

        if "Other" in self.subdivision:
            if self.heading == "1302":
                a = 1

        if self.subdivision[0:1] == "-" and self.subdivision[1:2] != " ":
            self.subdivision = "- " + self.subdivision[1:]

        if self.subdivision[0:2] == "- ":
            self.subdivision = self.subdivision[2:]
            self.subdivision = g.parent_heading.replace(":", " ").strip() + self.hierarchy_divider + self.subdivision

        self.subdivision = self.subdivision.replace("- - ", "- ")
        self.subdivision = self.subdivision.replace("ex ex", "ex ")
        self.subdivision = re.sub("^-([^-])", "- \\1", self.subdivision)
        if len(self.subdivision) > 1:
            if self.subdivision[0:3] == "\n- ":
                self.subdivision = self.subdivision[3:]

    def process_footnotes(self):
        if len(self.footnotes_lookup) > 0:
            matches = re.findall(r"\([0-9]{1,2}\)", self.original_rule)
            for match in matches:
                index = re.sub(r"[\(\)]", "", match)
                if index in self.footnotes_lookup["footnotes"]:
                    self.original_rule = self.original_rule.replace(match, "(" + self.footnotes_lookup["footnotes"][index] + ")")
                else:
                    self.original_rule = self.original_rule.replace(match, "")
        else:
            self.original_rule = re.sub("\([0-9]{1,2}\)", "", self.original_rule)

        self.original_rule = self.original_rule.replace("from :", "from:")

    def process_rule(self):
        n = Normalizer()
        self.original_rule = n.normalize(self.original_rule)
        self.original_rule = self.original_rule.replace("ex ex", "ex ")

        # Do not delete footnotes
        # self.original_rule = re.sub("\([0-9]{1,2}\)", "", self.original_rule)
        self.process_footnotes()
        self.rules = []
        tmp = self.original_rule.lower()

        self.original_rule = self.original_rule.replace("\nOr\n", "\nor\n", )

        # Remove any residual references to footnotes from the original Word documents
        self.original_rule = re.sub("\.[0-9]{1,2}$", ".", self.original_rule)
        self.original_rule = self.original_rule.replace(";\nor", ";\n\nTEMPOR")
        self.original_rule = self.original_rule.replace(";\n\nor", ";\n\nTEMPOR")
        self.original_rule = self.original_rule.replace("\nor\n", ";\n\nor\n\n")
        self.original_rule = self.original_rule.replace("TEMPOR", "or")
        self.original_rule = self.original_rule.strip(";")
        self.rule_strings = self.original_rule.split(";")

        for rule_string in self.rule_strings:
            rule = Rule(rule_string, self.heading)
            self.rules.append(rule.as_dict())

    def as_dict(self):
        my_dictionary = {
            "heading": self.heading,
            "headings": self.headings,
            "subheadings": self.subheadings,
            "chapter": self.chapter,
            "subdivision": self.subdivision,
            "min": self.min,
            "max": self.max,
            "rules": self.rules,
            "is_ex_code": self.is_ex_code,
            "is_chapter": self.is_chapter,
            "is_heading": self.is_heading,
            "is_subheading": self.is_subheading,
            "is_range": self.is_range,
            "valid": self.valid
        }
        return my_dictionary

    def switch_headings(self):
        return
        data_file = "data/heading_replacements.json"
        with open(data_file) as jsonFile:
            heading_replacements = json.load(jsonFile)
            jsonFile.close()

        if self.original_heading in heading_replacements:
            obj = heading_replacements[self.original_heading]
            tmp = obj["dest"].replace("ex ", "")
            self.min = g.format_parts(tmp, 0)
            self.max = g.format_parts(tmp, 1)
            self.switched_heading = self.original_heading
            self.original_heading = obj["dest"]
