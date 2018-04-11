#!/usr/bin/python3

import os
import sys
#from .libxmp import Module
from libxmp import Module


def main(args):
    out_file = args[0]
    found_names = set()
    with open(out_file, 'w') as outf:
        outf.write("""#!/usr/bin/python3
import tag_extract
class TestValue:
    def __init__(self, expected_author_name, song_name, *comment_lines):
        self.expected_author_name = expected_author_name
        self.song_name = song_name
        self.comment_lines = comment_lines

TEST_VALUES = (
""")
        dirs = list(args[1:])
        while len(dirs) > 0:
            d = dirs.pop()
            for f in os.listdir(d):
                print("... {0}".format(f))
                fn = os.path.join(d, f)
                if os.path.isdir(fn):
                    dirs.append(fn)
                    continue
                mod = None
                try:
                    mod = Module(fn)
                except Exception as e:
                    print('Skipping {0}: {1}'.format(fn, str(e)))
                    continue
                song_name = mod.name.decode('ascii', 'ignore')
                if song_name in found_names:
                    continue
                found_names.add(song_name)
                outf.write("    TestValue('ZZZZ', {0}".format(repr(song_name)))
                comment_lines = []
                for i in range(mod.ins):
                    ins = mod.xxi[i]
                    iname = ins.name.decode('ascii', 'ignore')
                    if len(iname.rstrip()) > 0:
                        outf.write(", {0}".format(repr(iname)))
                outf.write("),\n")
        outf.write("""
)

if __name__ == '__main__':
    for tv in TEST_VALUES:
        artist = tag_extract.get_artist_name(tv.song_name, tv.comment_lines)
        if tv.expected_author_name is None:
            if artist is not None:
                print("ERROR {0} - incorrectly set artist".format(tv.song_name))
            else:
                print("SUCCESS {0}".format(tv.song_name))
        elif artist is None:
            print("ERROR {0} - no artist set".format(tv.song_name))
        elif (tv.expected_author_name != artist):
            print("ERROR {0} - found author {1}, expected {2}".format(tv.song_name, repr(artist), repr(tv.expected_author_name)))
        else:
            print("SUCCESS {0}".format(tv.song_name))
""")


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
