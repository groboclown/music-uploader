"""
Probes media files using ffprobe.

Does not work for module files.
"""

import subprocess
import json
import hashlib
from ..probe import MediaProbe, ProbeFactory
from .ffmpeg import convert

BIN_FFPROBE = 'ffprobe'


def __run(srcfile):
    """
    Runs the probe operation on the given file, and returns the Json text.
    Raises an error if the tool reports an error.
    """

    # Test out with:
    # probe() {
    # ffprobe -v quiet -hide_banner -of json -print_format json -show_format -show_streams -i "$1"
    # }

    cp = subprocess.run([BIN_FFPROBE, "-v", "quiet", "-hide_banner", "-of",
        "json", "-print_format", "json", "-show_format", "-show_streams", "-i", srcfile],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    return cp.stdout.decode('utf-8')


def __format_run(arg):
    """
    Runs the probe operation to return the list of encoder or decoder.
    """
    cp = subprocess.run([BIN_FFPROBE, arg, "-v", "quiet", "-hide_banner"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    return cp.stdout.decode('utf-8')


def __format_split(line):
    whitespace = True
    ret = []
    buf = ''
    for c in line:
        if whitespace:
            if not c.isspace():
                whitespace = False
                buf = c
        else:
            if len(ret) < 2 and c.isspace():
                ret.append(buf.strip())
                buf = ''
            else:
                buf += c
    if len(buf) > 0:
        ret.append(buf.strip())
    return ret


BASIC_FORMATS = (
    'wav', 'aac', 'ac3', 'm4a', 'mkv', 'swf', 'thp',
    'xa', 'vima', 'alac', 'flac', 'adpcm', 'ape',
    'mp3', 'mp2', 'als', 'opus', 'paf', 'ralf',
    'sonic', 'tak', 'ogg', 'oga', 'xma', 'wma',
    'spex'
)


def __get_formats(arg):
    listing = False
    for line in __format_run(arg).splitlines():
        line = line.strip()
        if listing:
            # Some video formats also include audio formats...
            if line[0] == 'A':
                # audio format
                parts = __format_split(line)
                # print("DEBUG F- {0} -> {1}".format(repr(line), repr(parts)))
                yield parts[1].strip().lower()
        elif line.endswith('coders:'):
            listing = True


def _json_probe(srcfile):
    """
    Probe the file for its details, and return the results as a parsed
    JSon object.
    """
    return json.loads(__run(srcfile))

def _hash_tags(srcfile):
    with open(srcfile, 'rb') as inp:
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
            tags[k] = h.hexdigest()
        tags['size_bytes'] = str(size)
        return tags



class FfProbe(MediaProbe):
    def __init__(self, filename):
        MediaProbe.__init__(self, filename)

    def transcode(self, tofile, sample_rate = 44100, bit_rate = 0, channels = 2, codec = None):
        convert(self.filename, tofile,
            bit_rate=bit_rate,
            channels=channels,
            sample_rate=sample_rate,
            codec=codec,
            tags=self.get_tags())


def probe(srcfile):
    j = _json_probe(srcfile)
    p = FfProbe(srcfile)
    for s in j['streams']:
        if s['codec_type'] == 'audio':
            # print("DEBUG probe stream keys: {0}".format(repr(s.keys())))
            for tag_name, tag_value in _hash_tags(srcfile).items():
                p.set_tag(tag_name, tag_value)
            p.codec = s['codec_name']
            p.sample_rate = int(s['sample_rate'])
            if 'bit_rate' in s:
                p.bit_rate = int(s['bit_rate'])
            else:
                # guess?
                p.bit_rate = 320000
            p.channels = int(s['channels'])
            if 'tags' in s:
                for k in s['tags'].keys():
                    p.set_tag(k.lower(), s['tags'][k])
            if 'format' in j:
                s = j['format']
                if 'bit_rate' in s:
                    p.bit_rate = int(s['bit_rate'])
                if 'tags' in s:
                    for k in s['tags'].keys():
                        p.set_tag(k.lower(), s['tags'][k])
            return p
    raise Error('no audio stream in file `{0}`'.format(srcfile))

KNOWN_ALT_FORMATS = {
    'wavpack': [ 'wav' ],
    'vorbis': [ 'ogg' ],
    'pcm_s64be': [ 'pcm' ],
}

FORMATS = set()

def find_supported_formats():
    global FORMATS
    decoders = set()
    for name in __get_formats('-decoders'):
        decoders.add(name)
    for name in __get_formats('-encoders'):
        if name in decoders:
            FORMATS.add(name)
            if name in KNOWN_ALT_FORMATS:
                for f in KNOWN_ALT_FORMATS[name]:
                    FORMATS.add(f.lower())
    #if len(FORMATS) <= 0:
    #    FORMATS = FORMATS.union(BASIC_FORMATS)
    # There are some audio formats that are marked as video,
    # so they are missed.  This ensures we pick them up.
    FORMATS = FORMATS.union(BASIC_FORMATS)


class FfProbeFactory(ProbeFactory):
    def is_supported(self, filename):
        if len(FORMATS) <= 0:
            find_supported_formats()
            # print("DEBUG - supported formats:")
            # for f in FORMATS:
            #     print(" - {0}".format(f))
        if '.' not in filename:
            return False
        p = filename.rindex('.')
        if p >= 0 and p + 1 < len(filename):
            ext = filename[p+1:]
            if ext.lower() in FORMATS:
                return True
        return False

    def probe(self, filename):
        return probe(filename)
