"""Result converter for FAMAS contact angle goniometer software (KYOWA Inc.)
   This module only guarantees writing functionality to FAMAS compatible format.
   Readout is with minimal support!
"""
import csv
from pathlib import Path
import re
import sys
import io

curdir = Path(__file__).parent

default_sections = ["WORKSHEET", "DETAIL", "EDGE", "PIXEL", "EOF"]


def output_section_line(name):
    """Return a single line with the section name and spacer
    """
    name = name.upper()
    assert name in default_sections
    return "\"[{name}]\"".format(name=name)


def extract_section(text, name="WORKSHEET"):
    """Extract the corresponding text field 
    that starts and ends with \"[name]\"
    """
    name = name.upper()
    assert name in default_sections
    pattern = r"^\"\[{name}\]\"$\n(.*)\n^\"\[{name}\]\"$".format(name=name)
    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
    if len(matches) == 0:
        print("The file format is probably corrupted!",
              file=sys.stderr)
        return ""
    else:
        return matches[0]


def text_to_csv_list(text, delimiter=","):
    """Convert a delimiter-spaced text buffer to header and data blocks
    """
    with io.StringIO(text) as f:
        reader = csv.reader(f, dialect="excel", delimiter=delimiter)
        lines = [line for line in reader]
        header = lines[0]
        data = lines[1:]
        return header, data


def csv_list_to_text(header, data, delimiter=",", all_quote=True):
    """output the delimiter-separated text from the header and data
    """
    assert len(header) == len(data[0])
    with io.StringIO() as f:
        if all_quote:
            quote = csv.QUOTE_NONNUMERIC
        else:
            quote = csv.QUOTE_ALL
        writer = csv.writer(f, dialect="excel",
                            delimiter=delimiter,
                            quoting=quote)
        writer.writerow(header)
        writer.writerows(data)
        f.seek(0)
        text = f.read()
    return text
