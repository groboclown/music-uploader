#!/usr/bin/python3

import os
import sys
from convertmusic.db import get_history
from convertmusic.tools.cli_output import OutlineOutput, JsonOutput, YamlOutput
from convertmusic.tools import (
    is_media_file_supported,
    probe_media_file,
    MediaProbe,
    to_ascii,
    tag,
    set_tags_on_file,
    FfProbeFactory
)

FF_PROBES = FfProbeFactory()


def _out_writer(text):
    print(text)

OUTPUT = OutlineOutput(_out_writer)

def prompt_key(msg, keys):
    print('{0} ({1}) > '.format(msg, '/'.join(keys)), end='')
    while True:
        sys.stdout.flush()
        k = sys.stdin.readline().strip()
        if k == '?':
            print('{0} ({1}) > '.format(msg, '/'.join(keys)), end='')
        if len(k) != 1 or k not in keys:
            print('{0} > '.format('/'.join(keys)), end='')
        else:
            return k

def prompt_value(msg):
    print('{0} > '.format(msg))
    sys.stdout.flush()
    ret = sys.stdin.readline().strip()
    if len(ret) <= 0:
        return None
    return ret

def dupes(history):
    for fn in history.get_source_files():
        dupe_data = history.get_duplicate_data(fn)
        if len(dupe_data) <= 0:
            continue
        print(fn)
        fn_tags = history.get_tags_for(fn)
        print('- Tags: {0}'.format(repr(fn_tags)))
        fn_keys = history.get_keywords_for(fn)
        print('- Keywords: {0}'.format(repr(list(fn_keys))))
        print('Duplicate list:')
        for dd in dupe_data:
            dn = dupe_data['location']
            print('  {0}'.format(dn))
            dn_tags = history.get_tags_for(dn)
            print('  - Tags: {0}'.format(repr(dn_tags)))
            dn_keys = history.get_keywords_for(dn)
            print('  - Keywords: {0}'.format(repr(list(dn_keys))))
            print('  - Shared Keys: {0}'.format(repr(list(dn_keys.intersection(fn_keys)))))
            k = prompt_key('(k)eep duplicate, (r)emove duplicate, (s)kip source file, (D)elete source record', 'knsD')
            if 's' == k:
                break
            elif 'r' == k:
                history.delete_duplicate_id(dd['duplicate_id'])
            elif 'D' == k:
                if history.delete_source_record(fn):
                    print('=> Deleted all record of {0}'.format(fn))
                else:
                    print('=> Could not remove {0}'.format(fn))
                break
            # else just continu

TAG_TYPES = {
    't': tag.SONG_NAME,
    'a': tag.ARTIST_NAME
}

def tags(history, types):
    tag_names = []
    for tag_type in types:
        # Note: no error checking
        tag_names.append(TAG_TYPES[tag_type])
    for fn in history.get_source_files_without_tag_names(tag_names):
        tn = history.get_transcoded_to(fn)
        if tn is None:
            continue
        print(fn)
        fn_tags = history.get_tags_for(fn)
        print('- Tags: {0}'.format(repr(fn_tags)))
        adjusted_tags = False
        for t in tag_names:
            if t not in fn_tags or len(fn_tags[t].strip()) <= 0:
                tv = prompt_value(t)
                if tv is not None:
                    fn_tags[t] = tv
                    adjusted_tags = True
            else:
                print("Already handled {0}".format(t))
        if adjusted_tags:
            if FF_PROBES.is_supported(fn):
                # Fix the source, too.
                try:
                    set_tags_on_file(fn, fn_tags)
                except Exception as e:
                    OUTPUT.error("Couldn't update tags on source file {0} ({1})".format(
                        fn, e
                    ))
            set_tags_on_file(tn, fn_tags)
            history.set_tags_for(fn, fn_tags)
    print("Finished with tag handling")


def main(args):
    if len(args) <= 1:
        print("Usage: manage-data.py output-dir (command) (command args)")
        print("Commands:")
        print("  dupes      manage duplicates")
        print("  tags [at]  manage missing tags for title (t) and/or artist (a).  Does not")
        print("             fix the source files, but only the target files.")
        print("  fix-tags (tag-name) (files)")
        print("             fix the given tag name for the listed soruce files' targets")
        # TODO make tags and fix-tags also fix the source, if it's an ffmpeg file.
        return 1
    history = get_history(os.path.join(args[0], 'media.db'))
    try:
        if args[1] == 'dupes':
            return dupes(history)
        if args[1] == 'tags':
            return tags(history, args[2])
        return 1
    finally:
        history.close()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
