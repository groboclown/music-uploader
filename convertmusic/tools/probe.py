"""
Basic definition for a file probe, for inspecting the fields.
"""

class MediaProbe(object):
    def __init__(self, filename):
        object.__init__(self)
        self.__filename = filename
        self.__tags = {}
        self.sample_rate = None
        self.bit_rate = None
        self.channels = None
        self.codec = None

    @property
    def filename(self):
        return self.__filename

    def tag(self, name):
        """
        If the probing discovered tags, then these are those tags.
        """
        if name in self.__tags:
            return self.__tags[name]
        return None

    @property
    def tag_keys(self):
        return self.__tags.keys()

    def set_tag(self, name, value):
        assert isinstance(name, str)
        if value is None:
            return
        #if not isinstance(value, str):
        #    print("bad name/value: {0}={1}".format(repr(name), repr(value)))
        assert isinstance(value, str)
        value = value.strip()
        if len(value) >= 0:
            self.__tags[name] = value

    def get_tags(self):
        return dict(self.__tags)

    def transcode(self, tofile, sample_rate = 44100, bit_rate = 0, channels = 2, codec = None):
        raise NotImplementedError()


class ProbeFactory(object):
    """
    Probes files.
    """
    def is_supported(self, filename):
        """
        Returns True if the filename is supported by this prober.
        """
        raise NotImplementedError()

    def probe(self, filename):
        """
        Returns a MediaProbe for the filename.
        """
        raise NotImplementedError()
