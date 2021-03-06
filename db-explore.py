#!/usr/bin/python3

import os
import sys
from convertmusic.db import get_history
from convertmusic.cmd import (
    Cmd, std_main, OUTPUT
)

class CmdInfo(Cmd):
    def __init__(self):
        self.name = 'info'
        self.desc = 'Information about a single media file.'
        self.help = '''
Usage:
    info (source media file name)
        '''

    def _cmd(self, history, args):
        OUTPUT.list_start("Source-Info")
        for fn in args:
            OUTPUT.dict_start(fn)
            if not history.is_processed(fn):
                OUTPUT.dict_item('marked', False)
                sn = history.get_source_file_for_transcoded_filename(fn)
                OUTPUT.dict_item('transcoded_from', sn)
                continue
            OUTPUT.dict_item('marked', True)
            OUTPUT.dict_item('transcoded_to', history.get_transcoded_to(fn))
            fn_keys = history.get_keywords_for(fn)
            dups = history.get_duplicates(fn)
            OUTPUT.dict_start('duplicates')
            for dn in dups:
                OUTPUT.dict_start(dn)
                dn_keys = history.get_keywords_for(dn)
                OUTPUT.list_section('common_keywords', list(dn_keys.intersection(fn_keys)))
                OUTPUT.dict_end()
            OUTPUT.dict_end()
            OUTPUT.dict_section('tags', history.get_tags_for(fn))
            OUTPUT.list_section('keywords', list(fn_keys))
            OUTPUT.dict_end()
        return 0


class CmdFileList(Cmd):
    def __init__(self):
        self.name = 'list'
        self.desc = 'List all registered files and basic information about them.'
        self.help = '''
Usage:
    list [name-like] ...
Where:
    name-like       SQL like phrase for matching the filename.  If not given,
                    then all files are returned.  Multiple of these can be
                    given.
'''

    def _cmd(self, history, args):
        count = 0
        if len(args) > 0:
            names = set()
            for name_like in args:
                names = names.union(history.get_source_files(name_like))
        else:
            names = history.get_source_files()
        OUTPUT.dict_start('Sources')
        for fn in names:
            count += 1
            OUTPUT.dict_start(fn)
            OUTPUT.dict_item('transcode', repr(history.get_transcoded_to(fn)))
            OUTPUT.list_section('duplicates', history.get_duplicate_filenames(fn))
            OUTPUT.dict_end()
        if count <= 0:
            OUTPUT.error('No matching files in database')
        OUTPUT.dict_end()
        return 0


class CmdFrom(Cmd):
    def __init__(self):
        self.name = 'from'
        self.desc = 'Find the source information for the transcoded file(s)'
        self.help = """
Usage:
    from (output-file) ...
Where:
    output-file     One or more output files to report on its source.
                    If no output file is given, then it will report on all
                    transcoded files.
"""

    def _cmd(self, history, args):
        if len(args) == 0:
            args = history.get_transcoded_filenames()
        OUTPUT.dict_start('transcoded_from')
        for tn in args:
            sources = []
            sn = history.get_source_file_for_transcoded_filename(tn)
            if sn is not None:
                sources.append(sn)
                # Get the duplicates, so it traces all the files.
                sources.extend(history.get_duplicate_filenames(sn))
            OUTPUT.list_section(tn, sources)
        OUTPUT.dict_end()


class CmdTagSearch(Cmd):
    def __init__(self):
        self.name = 'tag-search'
        self.desc = 'Search for files based on tags.'
        self.help = """
Usage:
    tag-search (-a) (-e) [tag]=[value] ...
where:
    -a      If multiple tags are specified, then only files that match
            all the tags are shown.
    -e      Exact match.  If not specified, then the value can be a "like"
            clause.
    tag     The tag to search against.
    value   The value to search for.
"""

    def _cmd(self, history, args):
        tags = {}
        match_all = False
        match_exact = False
        for a in args:
            if a == '-a':
                match_all = True
            elif a == '-e':
                match_exact = True
            else:
                p = a.find('=')
                if p > 0:
                    tag = a[0:p]
                    value = a[p+1:]
                    tags[tag] = value
                else:
                    OUTPUT.error('Invalid argument format: {0}'.format(a))
        if match_all:
            matches = history.get_tag_matches(tags, match_exact)
        else:
            matches = set()
            for k,v in tags.items():
                m = history.get_tag_matches({k: v}, match_exact)
                matches = matches.union(m)
        OUTPUT.dict_start('Tag Matches')
        OUTPUT.list_section('Source Files', matches)
        OUTPUT.dict_end()


if __name__ == '__main__':
    sys.exit(std_main(sys.argv, (
        CmdInfo(),
        CmdFileList(),
        CmdFrom(),
        CmdTagSearch()
    )))
