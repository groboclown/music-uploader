
from .db import MediaFileHistory
from .tools import (
    is_media_file_supported,
    probe_media_file,
    MediaProbe
)
from .tools.keywords import get_keywords_for_tags


class MediaCache(object):
    def __init__(self, history, capacity=3000):
        assert isinstance(history, MediaFileHistory)
        self._history = history
        self.__dirty = {}
        self.__cache_by_filename = {}
        self.__filename_order = []
        self.__max_size = max(100, capacity)
        self.__index = 0

    def get(self, filename):
        if filename in self.__cache_by_filename:
            # Move the filename to the end of the list
            self.__filename_order.remove(filename)
            self.__filename_order.append(filename)
            return self.__cache_by_filename[filename]
        if filename in self.__dirty:
            entry = self.__dirty[filename]
        else:
            entry = MediaEntry(filename, self, self.__index)
            self.__index += 1
        if len(self.__filename_order) > self.__max_size:
            # remove the oldest item
            oldest = self.__filename_order[0]
            del self.__filename_order[0]
            old_entry = self.__cache_by_filename[oldest]
            if old_entry._is_dirty:
                self._dirty[oldest] = old_entry
            del self.__cache_by_filename[oldest]
        self.__filename_order.append(filename)
        self.__cache_by_filename[filename] = entry
        return entry
    
    def commit(self):
        dirty = []
        for entry in self.__cache_by_filename.values():
            if entry._commit():
                dirty.append(entry)
        for entry in self.__dirty.values():
            if entry._commit():
                dirty.append(entry)
        self.__dirty = {}
        return dirty

    def revert(self):
        for entry in self.__dirty.values():
            entry._revert()
        for entry in self.__cache_by_filename.values():
            entry._revert()

    def _mark_dirty(self, entry):
        self.__dirty[entry.source] = entry


class MediaEntry(object):
    def __init__(self, source_file, cache, index):
        assert isinstance(source_file, str)
        assert isinstance(cache, MediaCache)
        self.__source = source_file
        self.__dirty_tags = False
        self.__history = cache._history
        self.__cache = cache
        self.__marked = cache._history.is_processed(source_file)
        self.__transcoded = None
        self.__tags = None
        self.__dirty_duplicates = False
        self.__duplicate_data = None
        self.__duplicate_files_dirty = None
        self.__index = index
        self.__probe = None
        # __duplicate_data is a map of duplicate file names to the
        # duplicate entry ID
        # __duplicate_files_dirty is a list of filenames that may or may not
        # have dirty

    @property
    def source(self):
        """Source file name"""
        return self.__source

    @property
    def index(self):
        return self.__index

    @property
    def transcoded_to(self):
        """string or None"""
        if self.__marked and self.__transcoded is None:
            self.__transcoded = self.__history.get_transcoded_to(self.__source)
        return self.__transcoded

    @property
    def is_marked(self):
        return self.__marked
    
    @property
    def probe(self):
        if self.__probe is None:
            self.__probe = probe_media_file(self.__source)
        return self.__probe
    
    def set_transcoded_to(self, destfile):
        # Update immediately the transcode.
        if destfile != self.__transcoded:
            if self.__transcoded is not None:
                self.__history.delete_transcoded_to(self.probe)
            self.__transcoded = destfile
            self.__history.transcoded_to(self.probe, destfile)       

    @property
    def duplicate_filenames(self):
        if self.__duplicate_files_dirty:
            return list(self.__duplicate_files_dirty)
        if self.__duplicate_data is None:
            if self.__marked:
                # __duplicate_data is a list of dict, each one containing the keys:
                # 'source_file_id', 'source_location', 'duplicate_id',
                # 'duplicate_of_source_file_id', 'filename'
                data = self.__history.get_duplicate_data(self.__source)
                self.__duplicate_data = {}
                for d in data:
                    self.__duplicate_data[d['filename']] = d['duplicate_id']
            else:
                self.__duplicate_data = {}
        return list(self.__duplicate_data.keys())

    @property
    def tags(self):
        """Copy of the dictionary of tags."""
        self.__tag_keyword_cache()
        return dict(self.__tags)

    def add_tags(self, tags):
        # ensure the cache is right
        self.__tag_keyword_cache()
        tag_count = len(self.__tags)
        self.__dirty_tags = True
        self.__tags.update(tags)
        self.__cache._mark_dirty(self)
        # TODO should keywords be updated?

    def set_tags(self, tags):
        self.__dirty_tags = True
        self.__tags = dict(tags)
        self.__cache._mark_dirty(self)
        # TODO should keywords be updated?

    @property
    def keywords(self):
        # ensure the cache is right
        self.__tag_keyword_cache()
        return tuple(self.__keywords)
    
    @property
    def has_duplicates(self):
        return len(self.duplicate_filenames) > 0

    @property
    def _is_dirty(self):
        return self.__dirty_tags or self.__dirty_duplicates

    def _commit(self):
        was_dirty = False
        if not self.__marked:
            print("FIXME need to figure out how to mark {0}".format(self.__source))
            return False
        if self.__dirty_tags:
            self.__history.set_tags_for(self.__source, self.__tags)
            self.__dirty_tags = False
            was_dirty = True
        if self.__dirty_duplicates:
            # Remove invalid duplicates
            for filename,dup_id in self.__duplicate_data.items():
                if filename not in self.__duplicate_files_dirty:
                    self.__history.delete_duplicate_id(dup_id)
            # Add missing duplicates
            for filename in self.__duplicate_files_dirty:
                if filename not in self.__duplicate_data:
                    # This needs to probe filename, add a record for
                    # filename, and then call the mark_duplicate method.
                    # That may not be correct, as "filename" may already be
                    # in the db.
                    print("FIXME implement add duplicate for `{0}`".format(filename))
            self.__dirty_duplicates = False
            self.__duplicate_data = self.__history.get_duplicate_data(self.__source)
            self.__duplicate_files_dirty = []
            was_dirty = True
        return was_dirty

    def _revert(self):
        if self.__dirty_tags:
            self.__dirty_tags = False
            self.__tags = None
        if self.__dirty_duplicates:
            self.__duplicate_files_dirty = None
            self.__dirty_duplicates = False

    def __tag_keyword_cache(self):
        # If tags are dirty, then the tag dictionary isn't None.
        if self.__tags is None:
            if self.__marked:
                self.__tags = self.__history.get_tags_for(self.__source)
                self.__keywords = self.__history.get_keywords_for(self.__source)
            elif is_media_file_supported(self.__source):
                self.__tags = self.probe.get_tags()
                self.__keywords = get_keywords_for_tags(self.__tags)
            else:
                self.__tags = {}
                self.__keywords = set()
