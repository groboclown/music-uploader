
from .tag import *
from .unidecode import to_ascii


def get_keywords_for_tags(tags):
    keywords = set()
    for tk, tv in tags.items():
        if tk not in SKIPPED_KEY_TAGS:
            keywords = keywords.union(strip_keywords(tv))
    return keywords


def strip_keywords(text):
    # Translate the text into simple ascii characters.
    # Ascii conversion is done AFTER word split.
    if text is None:
        return []
    r = []
    b = ''
    isc = True
    for c in text:
        if isc:
            if c.isalnum():
                b += c
            else:
                isc = False
                if len(b) > 0:
                    r.append(to_ascii(b))
                b = ''
        else:
            if c.isalnum():
                isc = True
                b = c
    if len(b) > 0:
        r.append(to_ascii(b))
    return r
