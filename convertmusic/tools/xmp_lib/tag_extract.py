
import unicodedata
import re
import bz2
import hashlib
import gzip
import lzma

def file_checksums(src_filename):
    fn = src_filename.lower()
    if fn.endswith('.bz2'):
        inp = bz2.open(src_filename, 'rb')
    elif fn.endswith('.gz') or fn.endswith('.z'):
        inp = gzip.open(src_filename, 'rb')
    elif fn.endswith('.xz'):
        inp = lzma.open(src_filename, 'rb')
    else:
        inp = open(src_filename, 'rb')
    hashes = {
        'sha1': hashlib.sha1(),
        'sha256': hashlib.sha256()
    }
    size = 0
    buff = inp.read(4096)
    while len(buff) > 0:
        size += len(buff)
        for h in hashes.values():
            h.update(buff)
        buff = inp.read(4096)
    tags = {}
    for k,h in hashes.items():
        tags[k] = h.digest().decode('UTF-8')
    tags['size_bytes'] = size
    return tags


COPYRIGHT_MATCHERS = (
    re.compile(r'^\([cC]\)\s+(.*?)\s+\d\d\d\d$'),
    re.compile(r'^\[[cC]\]\s+(.*?)\s+\d\d\d\d$'),
    re.compile(r'^\([cC]\)\s+(.*?)\s+\d\d$'),
    re.compile(r'^\[[cC]\]\s+(.*?)\s+\d\d$'),
    re.compile(r"^\([cC]\)\s+(.*?)\s+'\d\d$"),
    re.compile(r"^\[[cC]\]\s+(.*?)\s+'\d\d$"),
    re.compile(r'^\([cC]\)\s*\d\d\d\d\s+(.*)$'),
    re.compile(r'^\[[cC]\]\s*\d\d\d\d\s+(.*)$'),
    re.compile(r'^\s*[cC][oO][pP][yY][rR][iI][gG][hH][tT]\s+(.*?)\s+\d\d\d\d$'),
    re.compile(r'^\([cC]\)\s*\d\d\s+(.*)$'),
    re.compile(r'^\[[cC]\]\s*\d\d\s+(.*)$'),
    re.compile(r"^\([cC]\)\s*'\d\d+\s+(.*)$"),
    re.compile(r"^\[[cC]\]\s*'\d\d+\s+(.*)$"),
    re.compile(r'^\([cC]\)\s+(.*)$'),
    re.compile(r'^\[[cC]\]\s+(.*)$')
)

def to_ascii(s):
    """
    Translates the string or bytes input into an ascii string with the
    accents stripped off.
    """
    if isinstance(s, bytes):
        s = s.decode('utf-8')
    return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))


class Stripped(object):
    WORDS = '01234567890123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    ALNUM_SEPS = ''
    SLASH_SEPS = '/'
    WORDGROUP_SEPS = (ALNUM_SEPS, SLASH_SEPS)
    WORDGROUP_COUNT = 2

    def __init__(self, s):
        if isinstance(s, bytes):
            s = s.decode('utf-8')
        self.__original = s
        self.__wg_words = []
        self.__wg_start_index = []
        self.__wg_end_index = []
        s = to_ascii(s)
        if len(s) != len(self.__original):
            raise Exception('ascii decode did not match length: {0} into {1}'.format(
                repr(self.__original), repr(s)
            ))

        for separators in Stripped.WORDGROUP_SEPS:
            words = []
            starts = []
            ends = []
            pos = 0
            is_word = False
            b = ''
            start_pos = -1
            for c in s:
                if is_word:
                    if c in Stripped.WORDS:
                        b += c
                    elif c in separators:
                        if len(b) > 0:
                            words.append(b.lower())
                            starts.append(start_pos)
                            ends.append(pos + 1)
                            b = ''
                            start_pos = pos
                        words.append(c.lower())
                        starts.append(pos)
                        ends.append(pos + 1)
                    else:
                        if len(b) > 0:
                            words.append(b.lower())
                            starts.append(start_pos)
                            ends.append(pos + 1)
                        is_word = False
                else:
                    if c in Stripped.WORDS:
                        is_word = True
                        start_pos = pos
                        b = c
                    elif c in separators:
                        words.append(c.lower())
                        starts.append(pos)
                        ends.append(pos + 1)
                pos += 1
            if is_word and len(b) > 0:
                words.append(b.lower())
                starts.append(start_pos)
                ends.append(pos + 1)
            self.__wg_words.append(words)
            self.__wg_start_index.append(starts)
            self.__wg_end_index.append(ends)

    @property
    def has_words(self):
        return self.alnum_count > 0 and self.slash_count > 0

    @property
    def has_slash_words(self):
        # Does this have slashes and words?
        slashes = False
        words = False
        for w in self.slash_words:
            if w in Stripped.SLASH_SEPS:
                slashes = True
            else:
                words = True
            if slashes and words:
                return True
        return False

    @property
    def ends_with_slash(self):
        # TODO fixme
        return False

    @property
    def has_perfect_slash_words(self):
        # This code here does perfect word / word / word format checking.
        slashes = False
        last_slash = True
        last_word = False
        # debug = ''
        word_count = 0
        for w in self.slash_words:
            # debug += ' ' + repr(w)
            if w in Stripped.SLASH_SEPS:
                # This may not be true...  Needs testing
                if last_slash:
                    # print("  xx two slashes {0}".format(repr(debug)))
                    return False
                last_slash = True
                last_word = False
            elif not last_slash:
                # print("  xx two words {0}".format(repr(debug)))
                return False
            elif last_word:
                # print("  xx two words {0}".format(repr(debug)))
                return False
            else:
                word_count += 1
                last_word = True
                last_slash = False
        # print("  xx final {0}".format(repr(debug)))
        return not last_slash and word_count >= 2

    @property
    def original(self):
        return self.__original

    def original_from(self, pos):
        return self.__original[pos:]

    def alnum_word(self, index):
        return self._word(0, index)

    @property
    def alnum_words(self):
        return self._word_list(0)

    def alnum_word_index_matcher(self, start_word_index, matcher):
        return self._word_index_matcher(0, start_word_index, matcher)

    def alnum_word_list_index_matcher(self, matcher_list):
        return self._word_list_index_matcher(0, matcher_list)

    @property
    def alnum_count(self):
        return self._word_count(0)

    def alnum_orig_word(self, index):
        return self._word_orig(0, index)

    def alnum_orig_word_pos(self, index):
        return self._word_orig_pos(0, index)

    def slash_word(self, index):
        return self._word(1, index)

    @property
    def slash_words(self):
        return self._word_list(1)

    def slash_word_index_matcher(self, start_word_index, matcher):
        return self._word_index_matcher(1, start_word_index, matcher)

    @property
    def slash_count(self):
        return self._word_count(1)

    def slash_orig_word(self, index):
        return self._word_orig(1, index)

    def slash_orig_word_pos(self, index):
        return self._word_orig_pos(1, index)

    def _word_list(self, wordid):
        assert wordid >= 0 and wordid < Stripped.WORDGROUP_COUNT
        return list(self.__wg_words[wordid])

    def _word_count(self, wordid):
        assert wordid >= 0 and wordid < Stripped.WORDGROUP_COUNT
        return len(self.__wg_words[wordid])

    def _word(self, wordid, index):
        assert wordid >= 0 and wordid < Stripped.WORDGROUP_COUNT
        assert index >= 0 and index < len(self.__wg_words[wordid])
        return self.__wg_words[wordid][index]

    def _word_orig(self, wordid, index):
        assert wordid >= 0 and wordid < Stripped.WORDGROUP_COUNT
        assert index >= 0 and index < len(self.__wg_words[wordid])
        return self.__original[self.__wg_start_index[wordid][index]:self.__wg_end_index[wordid][index]]

    def _word_orig_pos(self, wordid, index):
        assert wordid >= 0 and wordid < Stripped.WORDGROUP_COUNT
        if index < 0:
            return -1
        if index >= len(self.__wg_words[wordid]):
            return len(self.__original)
        return self.__wg_start_index[wordid][index]

    def _word_index_matcher(self, wordid, start_word_index, matches):
        assert start_word_index >= 0
        word_list = self._word_list(wordid)
        for i in range(start_word_index, len(word_list)):
            if matches == word_list[i]:
                return i
        return -1

    def _word_list_index_matcher(self, wordid, matcher_list):
        word_list = self._word_list(wordid)
        for i in range(0, len(word_list) - len(matcher_list)):
            match = True
            for j in range(0, len(matcher_list)):
                if matcher_list[j] != word_list[i + j]:
                    match = False
                    break
            if match:
                return i
        return -1


AUTHOR_MARKERS = (
    'by',
    'author',
    'composer'
)

def find_author_markers_pos(stripped, start_word_index):
    """
    Find a list of possible marker positions in the stripped string.  The positions
    will be the original word position *after* the marker.
    """
    assert isinstance(stripped, Stripped)
    ret = []
    for m in AUTHOR_MARKERS:
        word_index = stripped.alnum_word_index_matcher(start_word_index, m)
        if word_index >= 0:
            ret.append(stripped.alnum_orig_word_pos(word_index + 1))
    return ret


def guess_start_characters(prev, line):
    for i in range(0, min(len(prev), len(line))):
        if prev[i] != line[i]:
            if i == 0:
                return ''
            return prev[0:i]
    return ''


def guess_end_characters(prev, line):
    pi = len(prev)
    li = len(line)
    while pi > 0 and li > 0:
        pi -= 1
        li -= 1
        if prev[pi] != line[li]:
            return prev[pi+1:]
    return ''


CRUFT_GENERAL = '#-=\\/_:|'
CRUFT_OPEN = '[<(>'
CRUFT_CLOSE = ']>)<'
def strip_character_cruft(text, same_start, same_end):
    if same_start == text or not text.startswith(same_start):
        same_start = ''
    if same_end == text or not text.endswith(same_end):
        same_end = ''
    text = text[len(same_start or ''):len(text) - len(same_end or '')].strip()
    match = True
    if text.endswith('.') and not text.endswith('..'):
        text = text[0:-1].strip()
    while len(text) > 0 and match:
        match = False
        if text[0] in CRUFT_GENERAL:
            m = text[0]
            text = text[1:]
            if len(text) > 0 and text[-1] == m:
                text = text[:-1]
            text = text.strip()
            match = True
        else:
            p = CRUFT_OPEN.find(text[0])
            if p >= 0:
                text = text[1:]
                if len(text) > 0 and text[-1] == CRUFT_CLOSE[p]:
                    text = text[:-1]
                text = text.strip()
                match = True
    # Cleanup trailing
    while len(text) > 0 and text[-1] in CRUFT_GENERAL:
        text = text[:-1].strip()
    return text


def get_artist_name(name, comment_lines):
    # Heuristics to extract the author or composer name within the comments.
    # General observations:
    # - Usually, the comments have the title as the first line.  For a few
    #   mods, if that's not the case, then the first line is the artist.
    # - Some mods have the line after the title be the artist.
    # - Most have a line like "composed by" or "mixed by", followed by a line
    #   with the artist name.
    # - A few have the "by ABC" on one line.
    # - Many are a team effort, and are represented by a slash dividing each
    #   person (or the name / team).  The name slash name slash name ...
    #   format may be on its own.
    # - For the slash form, sometimes it spreads across lines.
    #   (see Chris & Rita example)
    # - Copyright: (c) NAME YEAR or (C) YEAR NAME
    # - some comments have a character or multiple characters at the start
    #   and/or the end of every line.  These need to be stripped.
    # TODO when several things match a line, add up the factors for that line.
    # With this, we can add in "anti-patterns", so that if a pattern is matched,
    # it will reduce the match factor.
    #print("  >> {0}".format(repr(name)))
    stripped_name = Stripped(name)
    simple_song_name = ' '.join(stripped_name.alnum_words)
    title_found = False
    author_prefix_found = False
    maybe_author_found = False
    author_found = False
    first = True
    author_matches = []
    line_count_factor = (len(comment_lines) + 1) / 1000
    same_start = None
    same_end = None
    for line in comment_lines:
        line_count_factor -= 0.001
        sline = Stripped(line)
        # print("  ** {0}".format(repr(' '.join(sline.slash_words))))
        #print("  ** {0}".format(repr(line)))
        if same_start is None:
            same_start = line
            same_end = line
        else:
            same_start = guess_start_characters(same_start, line)
            same_end = guess_end_characters(same_end, line)
        #print("DEBUG processing line {0} -> {1}".format(repr(line), repr(s)))
        if sline.has_words:
            if first:
                first = False
                #print("  -- first line {0:.3f} => {1}".format(line_count_factor + 0.1, repr(sline.original)))
                author_matches.append([
                    sline.original,
                    line_count_factor + 0.1
                ])
                # Keep looking
            if title_found:
                #print("  -- line after title {0:.3f} => {1}".format(line_count_factor + 0.3, repr(sline.original)))
                author_matches.append([
                    sline.original,
                    line_count_factor + 0.3
                ])
                # Keep looking
            # Always mark title found as false after the title found check;
            # if it's found again, that will be after this next block.
            title_found = False
            title_index = sline.alnum_word_list_index_matcher(stripped_name.alnum_words)
            if title_index >= 0 or ''.join(sline.alnum_words) == ''.join(simple_song_name):
                # Line with the title
                next_word_index = title_index + stripped_name.alnum_count
                author_markers_pos = find_author_markers_pos(sline, next_word_index)
                factor = line_count_factor + 0.5
                title_found = True
                #print("  -- title match")
                if len(author_markers_pos) > 0:
                    #print("  -- + author marker match")
                    author_prefix_found = True
                for p in author_markers_pos:
                    orig = sline.original_from(p)
                    if len(orig) > 0:
                        #print("  -- title post author marker {0:.3f} => {1}".format(factor, repr(orig)))
                        author_matches.append([
                            orig,
                            factor
                        ])
                        author_found = False
                        maybe_author_found = True
                        author_prefix_found = False
                    factor += 0.02

            if author_prefix_found:
                author_markers_pos = find_author_markers_pos(sline, 0)
                if len(author_markers_pos) <= 0:
                    #print("  -- post author marker line {0:.3f} => {1}".format(line_count_factor + 0.9, repr(sline.original)))
                    author_matches.append([
                        sline.original,
                        line_count_factor + 0.9
                    ])
                    maybe_author_found = True
                    author_found = True
                    author_prefix_found = False
                else:
                    #print("  -- line after author marker {0:.3f} => {1}".format(line_count_factor + 0.6, repr(sline.original)))
                    author_matches.append([
                        sline.original,
                        line_count_factor + 0.6
                    ])
                    factor = line_count_factor + 0.7
                    author_prefix_found = True
                    for p in author_markers_pos:
                        orig = sline.original_from(p)
                        if len(orig) > 0:
                            #print("  -- line after author marker, post author marker {0:.3f} => {1}".format(factor, repr(orig)))
                            author_matches.append([
                                orig,
                                factor
                            ])
                            author_found = False
                            maybe_author_found = True
                            author_prefix_found = False
                        factor += 0.02
            elif not author_found:
                author_markers_pos = find_author_markers_pos(sline, 0)
                if len(author_markers_pos) <= 0:
                    if sline.has_perfect_slash_words:
                        #print("  -- perfect slash words line {0:.3f} => {1}".format(line_count_factor + 0.6, repr(sline.original)))
                        author_matches.append([
                            sline.original,
                            line_count_factor + 0.6
                        ])
                    elif sline.has_slash_words:
                        #print("  -- slash words line {0:.3f} => {1}".format(line_count_factor + 0.4, repr(sline.original)))
                        author_matches.append([
                            sline.original,
                            line_count_factor + 0.4
                        ])
                        # TODO if ends with slash, then concatenate the author
                        # with this text.  See "omniphilia  (Rama-II)" test.

                    # copyright match.
                    copy_match = False
                    factor = line_count_factor + 0.7
                    for cc in COPYRIGHT_MATCHERS:
                        m = cc.match(sline.original)
                        if m:
                            #print("  -- copyright line {0:.3f} => {1}".format(factor, repr(m.group(1))))
                            author_matches.append([
                                m.group(1),
                                factor
                            ])
                            copy_match = True
                            author_found = True
                            maybe_author_found = False
                            author_prefix_found = False
                    if not copy_match:
                        maybe_author_found = False
                        author_found = False
                        author_prefix_found = False
                else:
                    factor = line_count_factor + 0.5
                    author_prefix_found = True
                    for p in author_markers_pos:
                        orig = sline.original_from(p)
                        if len(orig) > 0:
                            #print("  -- post author marker {0:.3f} => {1}".format(factor, repr(orig)))
                            author_matches.append([
                                orig,
                                factor
                            ])
                            author_found = False
                            maybe_author_found = True
                            author_prefix_found = False
                        factor += 0.02

    author = None
    author_index = 0
    #print("  ** same {0} to {1}".format(repr(same_start), repr(same_end)))
    for am in author_matches:
        a = strip_character_cruft(am[0], same_start, same_end)
        if len(a) > 0 and am[1] > author_index:
            author = a
            author_index = am[1]
    return author
