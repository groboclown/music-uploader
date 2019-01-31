#!/usr/bin/python3

import os
import shutil
import sys
import traceback
from convertmusic import (MediaFileHistory, get_history)
from convertmusic.tools import (
    is_media_file_supported,
    probe_media_file,
    MediaProbe,
    to_ascii,
    tag,
    get_destdir,
    transcode_correct_format,
)
from convertmusic.tools.cli_output import (OutlineOutput, YamlOutput, JsonOutput)
from convertmusic.tools.filename_util import (simplify_name, to_filename)

SKIP_DIR_FILENAME = '.skip'

def _out_writer(text):
    print(text)

OUTPUT = OutlineOutput(_out_writer)

def find_files(rootdir):
    """
    Iterates through the files under the given base directory.  It yields values
    back.  If a directory contains a "skip" file, then that directory and its
    sub-directories are skipped.
    """
    remaining_dirs = [rootdir]
    while len(remaining_dirs) > 0:
        basedir = remaining_dirs.pop()
        if os.path.isfile(os.path.join(basedir, SKIP_DIR_FILENAME)):
            continue
        for f in os.listdir(basedir):
            filename = os.path.join(basedir, f)
            if os.path.isdir(filename):
                remaining_dirs.append(filename)
            elif os.path.isfile(filename):
                yield filename

def find_new_media(rootdir, history):
    """
    Returns media probes for media files not already processed.
    """
    assert isinstance(history, MediaFileHistory)
    for filename in find_files(rootdir):
        # print("DEBUG - checking {0}".format(repr(filename)))
        if is_media_file_supported(filename) and not history.is_processed(filename):
            try:
                probe = probe_media_file(filename)
                yield probe
            except Exception as e:
                OUTPUT.error('Problem loading file {0}: {1}'.format(
                    filename, e
                ))
                # traceback.print_exc()

def copy_file(src_file, target_file):
    shutil.copyfile(src_file, target_file)

def process_probe(history, base_destdir, probe):
    OUTPUT.dict_start(probe.filename)
    try:
        matches = history.get_file_duplicate_tag_matches(probe)
        if len(matches) > 0:
            OUTPUT.list_section('exact_duplicate_of', matches)
            #print("Marking song {0} as duplicate of {1}".format(
            #    probe.filename, ', '.join(matches)
            #))
            history.mark_duplicate(probe, matches[0])
            return
        if probe.tag(tag.ARTIST_NAME) is not None and probe.tag(tag.SONG_NAME) is not None:
            matches = history.get_exact_matches(probe)
            if len(matches) > 0:
                OUTPUT.list_section('exact_duplicate_of', matches)
                #print("Marking song {0} as duplicate of {1}".format(
                #    probe.filename, ', '.join(matches)
                #))
                history.mark_duplicate(probe, matches[0])
                return
        matches = history.get_close_matches(probe, 0.9)
        if len(matches) > 0:
            OUTPUT.list_section('close_duplicate_of', matches)
            #print("Marking song {0} as duplicate of {1}".format(
            #    probe.filename, ', '.join(matches)
            #))
            history.mark_duplicate(probe, matches[0])
            return
        destdir = get_destdir(base_destdir)
        if not os.path.isdir(destdir):
            os.makedirs(destdir)
        OUTPUT.dict_item('title', probe.tag(tag.SONG_NAME))
        OUTPUT.dict_item('artist', probe.tag(tag.ARTIST_NAME))
        #print("{0} ({1} by {2})".format(probe.filename, probe.tag(tag.SONG_NAME), probe.tag(tag.ARTIST_NAME)))
        destfile = transcode_correct_format(history, probe, destdir)
        OUTPUT.dict_item('destination', destfile)
        #print("   -> {0}".format(destfile))
        history.mark_found(probe)
        history.transcoded_to(probe, destfile)
    finally:
        OUTPUT.dict_end()


def main(args):
    if len(args) < 3:
        print("Usage: main.py [--json] [--yaml] (src music dir) (dest music dir)")
        return 1
    global OUTPUT
    argp = 1
    if args[argp] == '--json':
        OUTPUT = JsonOutput(_out_writer)
        argp += 1
    elif args[argp] == '--yaml':
        OUTPUT = YamlOutput(_out_writer)
        argp += 1
    src_dir = args[argp]
    target_dir = args[argp + 1]
    if not os.path.isdir(target_dir):
        os.makedirs(target_dir)
    history = get_history(os.path.join(target_dir, 'media.db'))
    try:
        OUTPUT.start()
        OUTPUT.list_start('transcoded')
        for probe in find_new_media(src_dir, history):
            process_probe(history, target_dir, probe)
        OUTPUT.list_end()
    finally:
        OUTPUT.end()
        history.close()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
