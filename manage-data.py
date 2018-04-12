#!/usr/bin/python3

import os
import sys
from convertmusic.cmd import (
    OUTPUT, Cmd, Option, std_main, prompt_key, prompt_value
)
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


def _do_check_file(fn, args):
    if len(args) <= 0:
        return True
    for arg in args:
        if fn.startswith(arg):
            return True
    return False


class CmdDupes(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = 'dupes'
        self.desc = 'Manage files marked as duplicate'
        self.help = '''
For each file marked as being a duplicate in the database, you can
modify whether it is actually a duplicate or not, and which files
it is actually a duplicate of.

If you pass in an argument, it will be used as the source or target file
selection: all source files that start with that text will be checked.
'''

    def _cmd(self, history, args):
        for fn in history.get_source_files():
            # Note: dupes don't have transcoded-to, so only check source.
            if not _do_check_file(fn, args):
                continue
            dupe_data = history.get_duplicate_data(fn)
            if len(dupe_data) <= 0:
                continue
            print(fn)
            fn_tags = history.get_tags_for(fn)
            print('- Tags: {0}'.format(repr(fn_tags)))
            fn_keys = history.get_keywords_for(fn)
            print('- Keywords: {0}'.format(repr(list(fn_keys))))
            print('Duplicate list:')
            remaining_duplicate_count = len(dupe_data)
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
                    remaining_duplicate_count -= 1
                elif 'D' == k:
                    if history.delete_source_record(fn):
                        print('=> Deleted all record of {0}.'.format(fn))
                        remaining_duplicate_count = 0
                    else:
                        print('=> Could not remove {0}'.format(fn))
                    break
                # else just continue
            # TODO if there are no duplicates left, allow the user to
            # transcode the file.
            if remaining_duplicate_count == 0:
                print('NO DUPLICATES LEFT! ... we should allow transcoding the file again.')
        return 0


TAG_TYPES = {
    't': tag.SONG_NAME,
    'a': tag.ARTIST_NAME
}

class CmdEmptyTags(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = 'empty-tags'
        self.desc = 'Manage files with empty artist and / or song title tags.'
        self.help = '''
Usage:
    empty-tags [a|t] [file1 ...]
At least one of 'a' or 't' (and perhaps both, in either order) must be
specified.  't' means managing empty title tags, and 'a' means managing
empty artist tags.

If no files are specified, then all files with empty tags are checked.
If files are specified, then any source file starting with the text will
be checked.
'''
    def _parse_args(self, args):
        if len(args) <= 0:
            OUTPUT.error('Must provide at least one of `a` or `t` arguments.')
            return False, []
        tags = []
        for i in args[0]:
            if i not in TAG_TYPES:
                OUTPUT.error('Invalid tag types ({0}) must be at least one of `a` or `t`.'.format(args[0]))
                return False, []
            tags.append(TAG_TYPES[i])
        return True, [tags, args[1:]]


    def _cmd(self, history, args):
        tag_names = args[0]
        args = args[1]
        for fn in history.get_source_files_without_tag_names(tag_names):
            tn = history.get_transcoded_to(fn)
            if tn is None:
                continue
            if not _do_check_file(fn, args) and not _do_check_file(tn, args):
                continue
            print(fn)
            print(' -> {0}'.format(tn))
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
                        # TODO This will make the checksums wrong, but, meh.
                    except Exception as e:
                        OUTPUT.error("Couldn't update tags on source file {0} ({1})".format(
                            fn, e
                        ))
                set_tags_on_file(tn, fn_tags)
                history.set_tags_for(fn, fn_tags)
        print("Finished with tag handling")
        return 0


class CmdFixTags(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = 'fix-tags'
        self.desc = 'Correct tags on target files and in the database.'
        self.help = '''
Allows you to edit the tags on the songs.

If any argument is given, then only source files matching the start of the
arguments will be checked.
'''

    def _cmd(self, history, args):
        for fn in history.get_source_files():
            tn = history.get_transcoded_to(fn)
            if tn is None:
                continue
            if not _do_check_file(fn, args) and not _do_check_file(tn, args):
                continue
            print(fn)
            fn_tags = history.get_tags_for(fn)
            print('- Tags: {0}'.format(repr(fn_tags)))
            adjusted_tags = False
            while True:
                tag_name = prompt_value('Tag to edit (empty to continue)')
                if tag_name is None:
                    break
                tag_name = tag_name.strip()
                tag_value = prompt_value('New value')
                if tag_value is None:
                    if tag_name in fn_tags:
                        del fn_tags[tag_name]
                        adjusted_tags = True
                else:
                    fn_tags[tag_name] = tag_value
                    adjusted_tags = True
            if adjusted_tags:
                if FF_PROBES.is_supported(fn):
                    # Fix the source, too.
                    try:
                        set_tags_on_file(fn, fn_tags)
                        # TODO This will make the checksums wrong, but, meh.
                    except Exception as e:
                        OUTPUT.error("Couldn't update tags on source file {0} ({1})".format(
                            fn, e
                        ))
                set_tags_on_file(tn, fn_tags)
                history.set_tags_for(fn, fn_tags)
        return 0


if __name__ == '__main__':
    sys.exit(std_main(sys.argv, (
        CmdDupes(),
        CmdEmptyTags(),
        CmdFixTags()
    )))
