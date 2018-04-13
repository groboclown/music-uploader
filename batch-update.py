#!/usr/bin/python3

import os
import sys
import traceback
from convertmusic.cmd import (
    OUTPUT, Cmd, Option, std_main, JsonOption, YamlOption
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

REPLACED_TAGS = {}

class TagArg(Option):
    def __init__(self):
        Option.__init__(self)
        self.name = 't'
        self.has_arg = True
        self.help = 'Set the tag to the value, in the form "(tag):(value)"'

    def process(self, arg):
        if arg is None:
            OUTPUT.error('Must provide an argument for the option -t')
            return False, None
        p = arg.find(':')
        if p < 0:
            OUTPUT.error('Must provide a value')
            return False
        tag_name = arg[0:p].strip()
        if len(tag_name) <= 0:
            OUTPUT.error('Tag name cannot be zero-length')
            return False
        tag_value = None
        if p < len(arg):
            tag_value = arg[p+1:].strip()
            if len(tag_value) <= 0:
                tag_value = None
        REPLACED_TAGS[tag_name] = tag_value
        return True

PRETEND_MODE = False

class PretendArg(Option):
    def __init__(self):
        Option.__init__(self)
        self.name = 'p'
        self.has_arg = False
        self.help = "Pretend to perform the action, but don't actually change anything."

    def process(self, arg):
        global PRETEND_MODE
        PRETEND_MODE = True
        return True


class CmdReplace(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = 'replace'
        self.desc = 'Replace tags in the matched files.'
        self.help = """
Usage:
    replace (file1 (file2 ...))

Replaces the selected tags in all the discovered files.

For this command, you must specify a path match for matching files after
the command name.
"""

    def _parse_args(self, args):
        if len(args) <= 0:
            OUTPUT.error('Must provide at least one file matching argument')
            return False, []
        return True, args

    def _cmd(self, history, args):
        OUTPUT.list_start('affected_files')
        for fn in history.get_source_files():
            tn = history.get_transcoded_to(fn)
            if tn is None:
                continue
            if not _do_check_file(fn, args) and not _do_check_file(tn, args):
                continue

            OUTPUT.list_dict_start()
            OUTPUT.dict_item('source_file', fn)
            OUTPUT.dict_item('transcoded_file', tn)
            fn_tags = history.get_tags_for(fn)
            new_tags = dict(fn_tags)
            adjusted_tags = False
            for tag_name, tag_value in REPLACED_TAGS.items():
                if not(tag_name in fn_tags and fn_tags[tag_name] == tag_value):
                    adjusted_tags = True
                    new_tags[tag_name] = tag_value
            if adjusted_tags:
                OUTPUT.dict_start('original_tags')
                for tag_name, tag_value in fn_tags.items():
                    OUTPUT.dict_item(tag_name, tag_value)
                OUTPUT.dict_end()
                OUTPUT.dict_start('updated_tags')
                for tag_name, tag_value in new_tags.items():
                    OUTPUT.dict_item(tag_name, tag_value)
                OUTPUT.dict_end()

                if not PRETEND_MODE:
                    if FF_PROBES.is_supported(fn):
                        # Fix the source, too.
                        try:
                            set_tags_on_file(fn, new_tags)
                            # TODO This will make the checksums wrong, but, meh.
                        except Exception as e:
                            OUTPUT.error("Couldn't update tags on source file {0} ({1})".format(
                                fn, e
                            ))
                    set_tags_on_file(tn, new_tags)
                    history.set_tags_for(fn, new_tags)

            OUTPUT.dict_end()

        OUTPUT.list_end()
        return 0


class CmdUpdateSource(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = 'update-tags-from-source'
        self.desc = 'Update database and transcoded file tags with the source tags.'
        self.help = """
Usage:
    update-tags-from-source [-f] [file1 [file2 ...]]

This reads the source file and compares its tags against what is stored in
the database.   If any tags are in the source but not in the database, then
they are updated.  Tags will not be removed, only set.

If you use the '-f' option, then all tags found in the source will be set
in the database and transcoded files, regardless of their current values.
Tags will not be removed, only changed.
"""

    def _cmd(self, history, args):
        force = False
        if args[0] == '-f':
            force = True
            args = args[1:]
        OUTPUT.list_start('affected_files')
        for fn in history.get_source_files():
            tn = history.get_transcoded_to(fn)
            if tn is None:
                continue
            if not _do_check_file(fn, args) and not _do_check_file(tn, args):
                continue
            try:
                probe = probe_media_file(fn)
            except Exception as e:
                OUTPUT.error('Problem loading file {0}: {1}'.format(
                    filename, e
                ))
                traceback.print_exc()
                continue
            OUTPUT.list_dict_start()
            OUTPUT.dict_item('source_file', fn)
            OUTPUT.dict_item('transcoded_file', tn)

            fn_tags = history.get_tags_for(fn)
            probe_tags = probe.get_tags()
            new_tags = dict(fn_tags)
            altered_tags = False
            for tag_name, tag_value in probe_tags.items():
                if force or tag_name not in fn_tags:
                    if tag_name not in fn_tags or fn_tags[tag_name] != tag_value:
                        altered_tags = True
                    new_tags[tag_name] = tag_value
            if altered_tags:
                OUTPUT.dict_start('original_tags')
                for tag_name, tag_value in fn_tags.items():
                    OUTPUT.dict_item(tag_name, tag_value)
                OUTPUT.dict_end()
                OUTPUT.dict_start('updated_tags')
                for tag_name, tag_value in new_tags.items():
                    OUTPUT.dict_item(tag_name, tag_value)
                OUTPUT.dict_end()

                set_tags_on_file(tn, new_tags)
                history.set_tags_for(fn, new_tags)

            OUTPUT.dict_end()

        OUTPUT.list_end()
        return 0



class CmdDeleteTransform(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = 'delete-tform'
        self.desc = "Delete matching files' tranformed files"
        self.help = """
Usage:
    delete-tform (--db) (--files) (file_pattern1 ...)

Deletes transformed files from either the database (--db) or the filesystem
(--files) or both.  If none are selected, then the list of files that would
be affected are listed, but not removed.
"""

    def _cmd(self, history, args):
        del_db = False
        del_files = False
        argp = 0
        while True:
            if args[argp] == '--db':
                del_db = True
            elif args[argp] == '--files':
                del_files = True
            else:
                break
            argp += 1
        args = args[argp:]
        OUTPUT.list_start('deleted_transcoded_files')
        for fn in history.get_source_files():
            tn = history.get_transcoded_to(fn)
            if tn is None:
                continue
            if not _do_check_file(fn, args) and not _do_check_file(tn, args):
                continue
            OUTPUT.list_dict_start()
            OUTPUT.dict_item('source_file', fn)
            OUTPUT.dict_item('transcoded_file', tn)

            did_delete = False
            if del_db:
                did_delete = history.delete_transcoded_to(fn)
            OUTPUT.dict_item('deleted_transcode_db_record', did_delete)

            did_delete = False
            if del_files:
                if os.path.isfile(tn):
                    did_delete = True
                    os.unlink(tn)
            OUTPUT.dict_item('deleted_transcode_file', did_delete)

            OUTPUT.dict_end()

        OUTPUT.list_end()
        return 0



if __name__ == '__main__':
    sys.exit(std_main(sys.argv, (
        CmdReplace(),
        CmdUpdateSource(),
        CmdDeleteTransform(),
    ), (
        JsonOption(), YamlOption(), TagArg(), PretendArg()
        # TODO add TransformTranscodeOption
    )))
