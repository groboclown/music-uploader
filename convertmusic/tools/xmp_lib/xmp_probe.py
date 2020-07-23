
from ..probe import MediaProbe, ProbeFactory
from ..tag import *
from .libxmp import Module
from .xmp_wav import (
    convert,

    OPT_FREQUENCY, OPT_CHANNEL_COUNT, OPT_BITS_PER_SAMPLE
)
from ..ffmpeg_bin import ffmpeg
from .tag_extract import *
import os


FORMATS = (
    '.mod',
    '.m15',
    '.nt',
    '.flx',
    '.wow',
    '.dbm',
    '.digi',
    '.emod',
    '.med',
    '.mtn',
    '.okt',
    '.sfx',
    '.dtm',
    '.mgt',
    '.669',
    '.far',
    '.fnk',
    '.imf',
    '.it',
    '.liq',
    '.mdl',
    '.mtm',
    '.ptm',
    '.rtm',
    '.s3m',
    '.stm',
    '.ult',
    '.xm',
    '.amf',
    '.gdm',
    '.stx',
    '.abk',
    '.amf',
    '.psm',
    '.j2b',
    '.mfp',
    '.smp',
    '.psm',
    '.stim',
    '.umx',
    '.amd',
    '.rad',
    '.hsc',
)

PACKERS = (
    '.bz2', '.gz', '.lha', '.oxm', '.xz',
    '.z', '.zip', '.arcfs', '.arc', '.mmcmp',
    '.pac', '.powerpack', '.!spark', '.sqsh', '.muse', '.lzx', '.s404',
)


def comment_tag_extract(probe, song_name, comment_lines):
    if song_name is not None:
        probe.set_tag(SONG_NAME, song_name)
    author = get_artist_name(song_name, comment_lines)
    if author is not None:
        #print("DEBUG {0} :: {1}".format(repr(name), repr(author)))
        probe.set_tag(ARTIST_NAME, author)

    #print("DEBUG {0} :: {1} :: {2}\nComment:\n{3}".format(
    #    repr(name), repr(sname), probe.tag(ARTIST_NAME), '\n'.join(comment_lines)
    #))
    if len(comment_lines) > 0:
        probe.set_tag(COMMENT, '\n'.join(comment_lines))


class XmpProbe(MediaProbe):
    def __init__(self, filename):
        MediaProbe.__init__(self, filename)
        for tag_name, tag_value in file_checksums(filename).items():
            self.set_tag(tag_name, str(tag_value))
        MediaProbe.__init__(self, filename)
        mod = Module(filename)
        self.sample_rate = OPT_FREQUENCY
        self.bit_rate = OPT_BITS_PER_SAMPLE * OPT_FREQUENCY
        self.channels = OPT_CHANNEL_COUNT
        self.codec = mod.type.decode('ascii', 'ignore')
        # Instruments usually are the comments...
        comment_lines = []
        for i in range(mod.ins):
            ins = mod.xxi[i]
            iname = ins.name.decode('ascii', 'ignore')
            if len(iname.rstrip()) > 0:
                comment_lines.append(iname)
        #print("DEBUG {0} {1} {2}".format(repr(filename), repr(self.codec), repr(comment_lines)))
        comment_tag_extract(self, mod.name.decode('ascii', 'ignore'), comment_lines)

    def transcode(self, tofile, sample_rate = 44100, bit_rate = 0, channels = 2, codec = None, verbose=False):
        # First, transform to a temporary wav file.
        tmp = 'tmp.wav'
        if os.path.exists(tmp):
            os.unlink(tmp)
        try:
            convert(self.filename, tmp)
            ffmpeg.convert(tmp, tofile,
                bit_rate=bit_rate,
                channels=channels,
                sample_rate=sample_rate,
                codec=codec,
                tags=self.get_tags())
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


class XmpProbeFactory(ProbeFactory):
    def is_supported(self, filename):
        f = filename.lower()
        for p in PACKERS:
            if f.endswith(p):
                f = f[0:-len(p)]
                break
        for e in FORMATS:
            if f.endswith(e):
                return True
        return False

    def probe(self, filename):
        return XmpProbe(filename)
