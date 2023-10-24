from os import system, name


all_headings = {}
all_subheadings = {}
all_codes = {}
all_rules_with_classes = {}

parent_heading = ""


def format_parts(s, index):
    s = s.strip()
    string_length = len(s)
    if index == 0:
        s = s + (10 - string_length) * "0"
    else:
        s = s + (10 - string_length) * "9"

    return s


def clear():
    # for windows
    if name == 'nt':
        _ = system('cls')
    else:
        _ = system("printf '\33c\e[3J'")


def is_numeric(s):
    s = s.strip()
    s = s.replace(" to ", "")
    s = s.replace("-", "")
    s = s.replace("\n", "")
    s = s.replace(".", "")
    s = s.replace(" ", "")
    ret = s.isnumeric()
    return ret


def left(s, amount):
    return s[:amount]


def right(s, amount):
    return s[-amount:]


def mid(s, offset, amount):
    return s[offset:offset + amount]
