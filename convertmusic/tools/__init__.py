
from .unidecode import to_ascii
from . import tag
from .probe import MediaProbe
from .ffmpeg_bin.ffprobe import FfProbeFactory
from .xmp_lib.xmp_probe import XmpProbeFactory
from . import cli_output
from .tag_file import set_tags_on_file

FFMPEG_FACTORY = FfProbeFactory()
XMP_FACTORY = XmpProbeFactory()

PROBE_FACTORIES = (
    FFMPEG_FACTORY,
    XMP_FACTORY
)


def is_media_file_supported(filename):
    for f in PROBE_FACTORIES:
        if f.is_supported(filename):
            return True
    return False

def probe_media_file(filename):
    err = None
    for f in PROBE_FACTORIES:
        if f.is_supported(filename):
            try:
                return f.probe(filename)
            except Exception as e:
                err = e
    if err is not None:
        raise err
    raise Exception('No supported probe for {0}'.format(filename))
