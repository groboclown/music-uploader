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
    tag
)
from convertmusic.tools.cli_output import OutlineOutput, YamlOutput, JsonOutput

SKIP_DIR_FILENAME = '.skip'
MAX_FILES_PER_DIR = 1000

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

def simplify_name(name_root):
    name_root = to_ascii(name_root)
    ret = ''
    for c in name_root:
        if c.isalnum():
            ret += c
        elif c.isspace():
            if len(ret) > 0 and ret[-1] != '_':
                ret += '_'
        elif c in '-_':
            ret += c
    return ret

def to_filename(probe, dirname, ext):
    artist = probe.tag(tag.ARTIST_NAME)
    song = probe.tag(tag.SONG_NAME)
    name = None
    if artist is None and song is None:
        name = os.path.splitext(os.path.basename(probe.filename))[0]
    elif artist is None:
        name = song.strip()
    elif song is None:
        name = artist.strip() + "-unknown"
    else:
        name = artist.strip() + '-' + song.strip()
    if len(name) <= 0:
        name = 'x'
    if name[0] == '-':
        name = '_' + name[1:]
    # Maximum name length is 32 (roughly), so trim it down to 28 for the
    # extension.
    name = simplify_name(name)[0:31 - len(ext)]
    bn = os.path.join(dirname, name + '.' + ext)
    index = 0
    while os.path.isfile(bn):
        n = '-{0}'.format(index)
        bn = os.path.join(dirname, name[0:31 - len(ext) - len(n)] + n + '.' + ext)
        index += 1

    return bn

def copy_file(src_file, target_file):
    shutil.copyfile(src_file, target_file)

def transcode(probe, dest_dir):
    # Supported formats:
    # If the format is not exactly one of these, then re-encode it.
    #   MP3
    #     mpeg1 layer3
    #        frequencies: 32k, 44.1k, 48k
    #        bit rates: 32-320 kbps
    #     mpeg2 lsf layer3
    #        frequencies: 16k, 22.05k, 24k
    #        bit rates: 8-160 kbps
    #   WMA
    #     version 7, 8, 9
    #     frequencies: 32k, 44.1k, 48k
    #     v7,8 bit rates: 48-192 kbps
    #     v9 bit rates: 48-320 kpbs
    #   AAC
    #     mpeg4/aac-lc
    #     frequencies: 11.025, 12, 16, 22.05, 24, 32, 44.1, 48
    #     bit rates: 16-320
    if probe.codec.lower() == 'mp3':
        if (probe.sample_rate in (32000, 44100, 48000) and
                (probe.bit_rate >= 32000 and probe.bit_rate <= 320000) and
                probe.channels == 2):
            destfile = to_filename(probe, dest_dir, 'mp3')
            copy_file(probe.filename, destfile)
            return destfile
    if probe.codec.lower() == 'wma':
        if (probe.sample_rate in (32000, 44100, 48000) and
                (probe.bit_rate >= 48000 and probe.bit_rate <= 192000) and
                probe.channels == 2):
            destfile = to_filename(probe, dest_dir, 'wma')
            copy_file(probe.filename, destfile)
            return destfile
    if probe.codec.lower() == 'aac':
        if (probe.sample_rate in (11025, 12000, 16000, 22050, 24000, 32000, 44100, 48000) and
                (probe.bit_rate >= 16000 and probe.bit_rate <= 320000) and
                probe.channels == 2):
            destfile = to_filename(probe, dest_dir, 'm4a')
            copy_file(probe.filename, destfile)
            return destfile
    # Convert to aac, without losing quality.
    bit_rate = probe.bit_rate
    sample_rate = probe.sample_rate
    for br in (11025, 12000, 16000, 22050, 24000, 32000, 44100, 48000):
        if bit_rate < br:
            bit_rate = br
            break
    if sample_rate < 16000:
        sample_rate = 16000
    if sample_rate > 320000:
        sample_rate = 320000
    destfile = to_filename(probe, dest_dir, 'm4a')
    probe.transcode(destfile, sample_rate=sample_rate, bit_rate=bit_rate, channels=2, codec='aac')
    return destfile

def get_destdir(base_destdir):
    biggest = 0
    for f in os.listdir(base_destdir):
        fn = os.path.join(base_destdir, f)
        if os.path.isdir(fn) and f.isdigit() and int(f) > biggest:
            biggest = int(f)
    dn = os.path.join(base_destdir, '{0:06d}'.format(biggest))
    if os.path.isdir(dn) and len(os.listdir(dn)) > MAX_FILES_PER_DIR:
        dn = os.path.join(base_destdir, '{0:06d}'.format(biggest + 1))
    return dn

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
        destfile = transcode(probe, destdir)
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
