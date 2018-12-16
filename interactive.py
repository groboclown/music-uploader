#!/usr/bin/python3

import os
import sys
import shlex
import re
from convertmusic.db import MediaFileHistory
from convertmusic.cmd import (
    Cmd, std_main, OUTPUT, prompt_key, prompt_value
)
from convertmusic.cache import (MediaCache, MediaEntry)
from convertmusic.tools import (
    is_media_file_supported,
    probe_media_file,
    MediaProbe,
    to_ascii,
    tag,
    set_tags_on_file,
    FfProbeFactory,
    get_media_player,
    filename_util
)

NUMBER_PATTERN = re.compile(r'^\d+$')
TAG_RANK = 'local_rank'

CACHE = None


def print_entries(entries, history):
    if isinstance(entries, MediaEntry):
        entries = [entries]
    OUTPUT.start()
    OUTPUT.list_start("Source-Info")
    for entry in entries:
        assert isinstance(entry, MediaEntry)
        OUTPUT.dict_start(entry.source)
        OUTPUT.dict_item('marked', entry.is_marked)
        OUTPUT.dict_item('transcoded_to', entry.transcoded_to)
        OUTPUT.list_start('duplicates')
        for dn in entry.duplicate_filenames:
            #OUTPUT.dict_start(dn)
            #dn_keys = history.get_keywords_for(dn)
            #OUTPUT.list_section('common_keywords', list(dn_keys.intersection(fn_keys)))
            #OUTPUT.dict_end()
            OUTPUT.list_item(dn)
        OUTPUT.list_end()
        OUTPUT.dict_section('tags', entry.tags)
        # OUTPUT.list_section('keywords', entry.keywords)
        OUTPUT.dict_end()
    OUTPUT.list_end()
    OUTPUT.end()


class Action:
    def __init__(self):
        self.cmds = ['x']
        self.desc = ''
        self.help = ''

    def run(self, history, item_list, current_index, args):
        '''Runs the option, and returns the new current position in that list.
        It can modify the item_list.'''
        raise NotImplementedError()

# Special return codes:
RESULT_QUIT = -2


class HelpAction(Action):
    def __init__(self):
        self.current_options = {}
        self.cmds = ['?']
        self.desc = "Show list of actions, or details for a specific action."
        self.help = """
Usage:
    ?
    ? (option)
Where:
    option     name of the command to inspect
"""

    def run(self, history, item_list, current_index, args):
        if len(args) > 0:
            for arg in args:
                if arg in self.current_options:
                    c = self.current_options[arg]
                    print(', '.join(c.cmds))
                    print(c.desc)
                    print(c.help)
                else:
                    print("Unknown command: {0}".format(arg))
        else:
            max_len = 0
            cmds = list(self.current_options.keys())
            cmds.sort()
            for k in cmds:
                max_len = max(max_len, len(k))
            for k in cmds:
                v = self.current_options[k]
                print(("{0:" + str(max_len) + "s}  {1}").format(k, v.desc))
# Needed because its current_options is used.
HELP_ACTION = HelpAction()


class QuitAction(Action):
    def __init__(self):
        self.cmds = ['quit', 'exit']
        self.desc = 'Quit application.'
        self.help = ''

    def run(self, history, item_list, current_index, args):
        return RESULT_QUIT


class PlayCurrentAction(Action):
    def __init__(self):
        self.cmds = ['play', 'p']
        self.desc = "Play the current item's transcoded file (default), or the source file."
        self.help = """
Usage:
    play
    play src
Where:
    src - play the source file.
"""

    def run(self, history, item_list, current_index, args):
        current = item_list[current_index]
        if 'src' in args:
            source = current.source
        elif current.transcoded_to is None:
            print("No transcoded file for `{0}`".format(current.source))
            return current_index
        else:
            source = current.transcoded_to
        if not os.path.isfile(source):
            print('Cannot find file `{0}`'.format(source))
        else:
            get_media_player().play_file(source)
        return current_index


class ShowCurrentAction(Action):
    def __init__(self):
        self.cmds = ['show', 's']
        self.desc = "Show details about the current selection."
        self.help = ''

    def run(self, history, item_list, current_index, args):
        current = item_list[current_index]
        print_entries([current], history)


class NextItemAction(Action):
    def __init__(self):
        self.cmds = ['next', 'n']
        self.desc = "Advance to next item in the list."
        self.help = """
Usage:
    next [k] [n]
Where:
    k   set this option to not commit when running the next.
    n   set this option to not play when running the next.
"""

    def run(self, history, item_list, current_index, args):
        do_commit = True
        do_play = True
        for a in args:
            if a == 'k':
                do_commit = False
            if a == 'n':
                do_play = False
        if do_commit:
            commit()
        next = min(len(item_list), current_index + 1)
        if do_play and next != current_index:
            source = current.transcoded_to
            if not os.path.isfile(source):
                print('Cannot find file `{0}`'.format(source))
            else:
                get_media_player().play_file(source)
        return next


class PrevItemAction(Action):
    def __init__(self):
        self.cmds = ['prev', 'back']
        self.desc = "Go back to the previous item in the list."
        self.help = ''

    def run(self, history, item_list, current_index, args):
        return max(0, current_index - 1)


class GotoPositionAction(Action):
    def __init__(self):
        self.cmds = ['goto', 'first']
        self.desc = "Go to the selected position in the list; defaults to the first position"
        self.help = """
Usage:
    first
    goto (position)
Where:
    position   the index in the list.
"""

    def run(self, history, item_list, current_index, args):
        pos = 0
        return 0


class ListAction(Action):
    def __init__(self):
        self.cmds = ['ls', 'list']
        self.desc = "Show the current list."
        self.help = """
Usage:
    ls [-] [count] [key] [?]
Where:
    (no arguments)  show the list starting from the current position
    -               show the contents, starting from the start of the list
    count           maximum number of items to show.  Use '0' for no limit.
                    Defaults to 10.
    key             value of the list items to show.  Defaults to 'source'
    ?               List the key values that can be shown.
"""

    def run(self, history, item_list, current_index, args):
        count = 10
        start = current_index
        key = 'source'
        while len(args) > 0:
            if args[0] == '-':
                start = 0
                args = args[1:]
            elif NUMBER_PATTERN.match(args[0]):
                count = int(args[0])
                args = args[1:]
            elif args[0] == '?':
                keys = set('source', 'target')
                for e in item_list:
                    keys = keys.union(e.tags.keys())
                print("Available keys to list:")
                for k in keys:
                    print("  {0}".format(k))
                return current_index
            else:
                key = args[0]
        max_len = str(len(str(start + count - 1)))
        for i in range(start, start + count):
            item = item_list[i]
            assert isinstance(item, MediaEntry)
            if key == 'source':
                value = item.source
            elif key == 'target':
                value = item.transcoded_to
            elif key in item.tags:
                value = item.tags[key]
            else:
                value = "<<no value>>"
            print(("{0}{1:" + max_len + "} `{2}`").format(
                i == current_index and '>' or ' ',
                i,
                value))
        return current_index


class SearchAction(Action):
    def __init__(self):
        self.cmds = ['search', 's', 'find']
        self.desc = "Update the current list with files"
        self.help = """
Usage:
    search [-a | -i | -p] [-x] [-t tagname] [--] (pattern ...)
Where:
    -a       append the discovered files to the current list
    -i       insert the discovered files to the current position
    -p       insert the discovered files after the current position
    -x       file patterns are an exact match.  Without this, the search
             pattern recognizes SQL like patterns - '%' is for 0 or more
             characters, '_' is for 1 character.
    -t       use the pattern to search for the given tag name's contents.
    --       everything after this is a pattern
    pattern  file pattern to match.  If no pattern is given, then it returns all
             the files.  If the '-t tagname' argument was given, then it
             searches tags for matching patterns; if the patterns is blank, then
             only files whose tags are blank or not set are return.
"""

    def run(self, history, item_list, current_index, args):
        action = 'r'
        patterns = []
        exact = False
        on_patterns = False
        tag = None
        on_tag = False
        for arg in args:
            if on_tag:
                tag = arg
                on_tag = False
            if on_patterns:
                patterns.append(arg)
            elif arg == '--':
                on_patterns = True
            elif arg[0] == '-':
                if arg[1:] == 'a':
                    action = 'a'
                elif arg[1:] == 'i':
                    action = 'i'
                elif arg[1:] == 'p':
                    action = 'p'
                elif arg[1:] == 'x':
                    exact = True
                elif arg[1:] == 't':
                    on_tag = True
                else:
                    print("Unknown option: {0}".format(arg))
                    return current_index
            else:
                on_patterns = True
                patterns.append(arg)

        if tag is not None:
            if len(patterns) <= 0:
                sources = history.get_source_files_without_tag_names([tag])
            else:
                sources = []
                for p in patterns:
                    tags = {}
                    tags[tag] = p
                    sources.extend(history.get_tag_matches(tags, exact))
        elif exact:
            sources = []
            for s in history.get_source_files():
                if s in patterns or os.path.basename(s) in patterns:
                    sources.append(s)
        else:
            if len(patterns) > 0:
                sources = []
                for p in patterns:
                    sources.extend(history.get_source_files(p))
            else:
                sources = history.get_source_files()

        if action == 'i':
            if current_index <= 0:
                prev_items = []
            else:
                prev_items = item_list[0:current_index - 1]
            next_items = item_list[current_index:]
        elif action == 'a':
            prev_items = list(item_list)
            next_items = []
        elif action == 'p':
            prev_items = item_list[0:current_index]
            next_items = item_list[0:current_index + 1]
        else:
            prev_items = []
            next_items = []
            current_index = 0

        item_list.clear()
        item_list.extend(prev_items)
        global CACHE
        for s in sources:
            item_list.append(CACHE.get(s))
        item_list.extend(next_items)

        return current_index


class FilterAction(Action):
    def __init__(self):
        self.cmds = ['filter']
        self.desc = "Filter the list of items with a specific query."
        self.help = """
The filtering starts at the current index.
Usage:
    filter [!t] [!r]
Where:
    !t    remove the entries that have no transcoded file
    !r    remove the entries that are not ranked
"""

    def run(self, history, item_list, current_index, args):
        i = current_index
        while i < len(item_list):
            item = item_list[i]
            filter = False
            for cmd in args:
                if cmd == '!t':
                    if item.transcoded_to is None or not os.path.isfile(item.transcoded_to):
                        filter = True
                        break
                elif cmd == '!r':
                    if TAG_RANK not in item.tags:
                        filter = True
                        break
            if filter:
                del item_list[i]
            else:
                i += 1


TAG_ALIASES = {
    'a': tag.ARTIST_NAME,
    'u': tag.ALBUM_NAME,
    't': tag.SONG_NAME,
    'y': tag.YEAR,
    'k': tag.TRACK,
    'kt': tag.TRACK_TOTAL,
}
class TagAction(Action):
    def __init__(self):
        self.cmds = ['tag']
        self.desc = "Update a tag on the current item"
        alias_list = ''
        for k,v in TAG_ALIASES.items():
            alias_list += "    {0} -> {1}\n".format(k, v)
        self.help = """
Usage:
    tag [(tag)=(value) ...]  [-(tag)]
Where:
    tag=value   assign tag (tag) to value (value).  Use quotes where necessary.
    -tag        remove tag (tag)

Some tag aliases:
{0}""".format(alias_list)

    def run(self, history, item_list, current_index, args):
        item = item_list[current_index]
        tags = item.tags
        for arg in args:
            if arg[0] == '-':
                tn = arg[1:]
                if tn in TAG_ALIASES:
                    tn = TAG_ALIASES[tn]
                if tn in tags:
                    del tags[tn]
            elif '=' in arg:
                tn = arg[0:arg.find('=')].strip()
                v = arg[arg.find('=') + 1:].strip()
                if tn in TAG_ALIASES:
                    tn = TAG_ALIASES[tn]
                tags[tn] = v
        item.set_tags(tags)


class RevertAction(Action):
    def __init__(self):
        self.cmds = ['revert']
        self.desc = "Revert all actions since the last commit"
        self.help = ''

    def run(self, history, item_list, current_index, args):
        global CACHE
        CACHE.revert()


class CommitAction(Action):
    def __init__(self):
        self.cmds = ['commit']
        self.desc = "Commit all current pending requests.  Will happen automatically on exit."
        self.help = ''

    def run(self, history, item_list, current_index, args):
        commit()


class DeleteTranscodeAction(Action):
    def __init__(self):
        self.cmds = ['del', 'delete']
        self.desc = "Delete the current item's transcoded file."
        self.help = ''

    def run(self, history, item_list, current_index, args):
        item = item_list[current_index]
        target = item.transcoded_to
        if target is not None and os.path.isfile(target):
            try:
                os.unlink(target)
                print("Deleted {0}".format(target))
            except:
                print("Could not remove file `{0}`".format(target))


class RankAction(Action):
    def __init__(self):
        self.cmds = ['rank']
        self.desc = "Rank the current file with a number, higher being better"
        self.help = """
Usage:
    rank (number)
Where:
    number  ranking to assign to the file.
"""

    def run(self, history, item_list, current_index, args):
        item = item_list[current_index]
        if len(args) == 1 and NUMBER_PATTERN.match(args[0]):
            item.add_tags({ TAG_RANK: args[0] })
        else:
            print("Must provide the rank number.")


class TranscodeAction(Action):
    def __init__(self):
        self.cmds = ['tx', 'transcode', 'tcode']
        self.desc = "Transcode the file again."
        self.help = """
Usage:
    transcode ????
Where:
    Need to allow passing in options to force it to operate a specific way.
"""

    def run(self, history, item_list, current_index, args):
        print("NOT IMPLEMENTED")


class NormalizeAction(Action):
    def __init__(self):
        self.cmds = ['normalize', 'nz']
        self.desc = "Normalize the audio level, so that its volume is not too quiet"
        self.help = """
Usage:
    normalize [percent]
Where:
    percent   the percent of the maximum volume to set.  Defaults to 95.
"""

    def run(self, history, item_list, current_index, args):
        print("NOT IMPLEMENTED")


ACTIONS_WITH_CURRENT = [
    PlayCurrentAction(),
    ShowCurrentAction(),
    TagAction(),
    DeleteTranscodeAction(),
    RankAction(),
    TranscodeAction(),
    NormalizeAction(),
]
ACTIONS_WITH_LIST = [
    NextItemAction(),
    PrevItemAction(),
    GotoPositionAction(),
    ListAction(),
    FilterAction(),
]
ACTIONS_ANY = [
    HELP_ACTION,
    QuitAction(),
    SearchAction(),
    RevertAction(),
    CommitAction(),
]

def add_actions_to_options(action_list, options):
    for action in action_list:
        for c in action.cmds:
            options[c] = action


def commit():
    entries = CACHE.commit()
    for entry in entries:
        if entry.transcoded_to and os.path.isfile(entry.transcoded_to):
            set_tags_on_file(entry.transcoded_to, entry.tags)
    print("Committed {0} entries.".format(len(entries)))


class CmdInteractive(Cmd):
    def __init__(self):
        self.name = 'interactive'
        self.desc = 'Interactive exploration of the catalogue.'
        self.help = ''

    def _cmd(self, history, args):
        global CACHE
        CACHE = MediaCache(history)
        item_list = []
        running = True
        current_index = 0
        while running:
            current = None
            options = {}
            HELP_ACTION.current_options = options
            add_actions_to_options(ACTIONS_ANY, options)
            prompt = "(empty list)"
            if len(item_list) > 0:
                add_actions_to_options(ACTIONS_WITH_LIST, options)
                if current_index < len(item_list) and current_index >= 0:
                    current = item_list[current_index]
                prompt = "(at list end)"
            if current is not None:
                prompt = "{0}\n{2}/{1}".format(current.source, len(item_list), current_index)
                add_actions_to_options(ACTIONS_WITH_CURRENT, options)
            text = None
            while text is None or len(text) <= 0:
                text = prompt_value(prompt)
            p = shlex.split(text, False)
            if p[0] not in options:
                print("Unknown command: {0}".format(p[0]))
                print("Use '?' for help.")
                continue
            else:
                res = options[p[0]].run(history, item_list, current_index, p[1:])
                if res == RESULT_QUIT:
                    running = False
                elif res is not None:
                    current_index = res
        commit()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: {0} (output-dir)".format(sys.argv[0]))
        print(("  {0}  {1}").format('output-dir',
            'The directory where the output was generated.  This will contain the media.db file.'))
        sys.exit(1)
    sys.exit(std_main([sys.argv[0], sys.argv[1], '--yaml', 'interactive'], [CmdInteractive()]))
