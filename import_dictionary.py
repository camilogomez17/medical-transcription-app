"""Import English->Spanish headwords from the MedicalSpanishDictionary HTML page.

Usage:
  python import_dictionary.py medical-spanish-dictionary.html

This creates medical_glossary.json next to this script. It parses the downloaded
HTML locally; it does not make network requests.
"""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class H2Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_h2 = False
        self.parts: list[str] = []
        self.headings: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "h2":
            self.in_h2 = True
            self.parts = []
        elif self.in_h2 and tag.lower() == "br":
            self.parts.append(" ")

    def handle_data(self, data):
        if self.in_h2:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "h2" and self.in_h2:
            text = " ".join(" ".join(self.parts).split())
            if text:
                self.headings.append(text)
            self.in_h2 = False
            self.parts = []


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python import_dictionary.py path/to/index.html")
        return 2
    html_path = Path(sys.argv[1]).expanduser()
    if not html_path.is_file():
        print(f"File not found: {html_path}")
        return 2

    parser = H2Parser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    glossary: dict[str, str] = {}
    for heading in parser.headings:
        # Example heading: bronchial asthma (SP. asma bronquial) f. ˈas.ma...
        match = re.match(
            r"^(.+?)\s*\(\s*SP\.\s*(.+?)\s*\)", heading, flags=re.IGNORECASE
        )
        if not match:
            continue
        english = " ".join(match.group(1).split()).strip(" :-")
        spanish = " ".join(match.group(2).split()).strip(" :-")
        if english and spanish:
            glossary[english.lower()] = spanish

    if not glossary:
        print("No English/Spanish headwords found. The page format may have changed.")
        return 1

    output_path = Path(__file__).with_name("medical_glossary.json")
    output_path.write_text(
        json.dumps(glossary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Imported {len(glossary)} headwords to {output_path.name}")
    print("Review the terms before relying on them in a medical interpreting workflow.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
