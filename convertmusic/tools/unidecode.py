
"""
Decodes a unicode string into a ascii-compatible but usable
string.

Alternatively, see unidecode, but that is under the GPL.
"""

import unicodedata

def to_punycode(bstr):
    """
    Translates the string or bytes input into a punycode formatted string.
    """
    if isinstance(bstr, str):
        # Passed in a string, not a byte array.
        # Transform into a bytes structure
        try:
            bstr = bstr.encode('ascii')
            return bstr.decode('ascii')
        except UnicodeEncodeError:
            bstr = bstr.encode('utf-8')
        except UnicodeDecodeError:
            bstr = bstr.encode('utf-8')
    s = bstr.decode('utf-8')
    return s.encode('punycode').decode('ascii')

def to_ascii(s):
    """
    Translates the string or bytes input into an ascii string with the
    accents stripped off.
    """
    if isinstance(s, bytes):
        s = s.decode('utf-8')
    s = ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
    s = ''.join((c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c)))
    r = ''
    for c in s:
        if ord(c) >= 0 and ord(c) <= 127:
            r += c
        else:
            r += '_'
    return r
