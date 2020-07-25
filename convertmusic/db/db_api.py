

class DbApi(object):
    def __init__(self):
        object.__init__(self)

    def add_source_file(self, filename):
        """
        Returns the ID for the source file.  Raises exception if it
        already exists.
        """
        raise NotImplementedError()

    def get_source_file_id(self, filename):
        """
        Returns the ID for the source file, or None if not present.
        """
        raise NotImplementedError()

    def add_tag(self, file_id, tag_name, tag_value):
        """
        Returns the ID of the tag.
        """
        raise NotImplementedError()

    def add_keyword(self, file_id, keyword):
        """
        Returns the ID of the keyword.
        """
        raise NotImplementedError()

    def add_target_file(self, source_file_id, target_filename):
        """
        Returns the ID of the target file.
        """
        raise NotImplementedError()

    def get_source_files_with_tags(self, tags, exact=True):
        """
        Returns the source file names that has the matching tag keys to tag values.
        If none are found, then an empty list is returned.
        """
        raise NotImplementedError()

    def get_source_files_with_matching_keywords(self, keywords):
        """
        Returns a list of [source file name, keyword],
        possibily with duplicate source files, for any keyword.
        """
        raise NotImplementedError()

    def add_duplicate(self, source_id, duplicate_of_id):
        raise NotImplementedError()

    def get_duplicate_of_id(self, source_id):
        """
        Returns the source file ID of the file marked as a duplicate of the
        source file.
        """
        raise NotImplementedError()

    def close(self):
        """Close the connection."""
        raise NotImplementedError()
