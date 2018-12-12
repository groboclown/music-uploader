
from ..tools.unidecode import to_ascii
from .db_api import DbApi

from ..tools.tag import *

class MediaFileHistory(object):
    def __init__(self, db):
        assert isinstance(db, DbApi)
        self.__db = db

    def __del__(self):
        self.close()

    def close(self):
        if self.__db is not None:
            self.__db.close()

    def is_processed(self, filename):
        return self.__db.get_source_file_id(filename) is not None

    def mark_duplicate(self, source_probe, duplicate_of_filename):
        duplicate_of_id = self.__db.get_source_file_id(duplicate_of_filename)
        if duplicate_of_id is None:
            raise Exception('not registered: {0}'.format(duplicate_of_filename))
        s_id = self._add_probe(source_probe)
        d_id = duplicate_of_id
        while duplicate_of_id is not None:
            d_id = duplicate_of_id
            duplicate_of_id = self.__db.get_duplicate_of_id(d_id)
        self.__db.add_duplicate(s_id, d_id)

    def get_duplicate_filenames(self, source_probe_or_file):
        ret = []
        for d in self.get_duplicate_data(source_probe_or_file):
            ret.append(d['source_location'])
        return ret

    def get_duplicate_data(self, source_probe_or_file):
        if not isinstance(source_probe_or_file, str):
            source_probe_or_file = source_probe_or_file.filename
        source_id = self.__db.get_source_file_id(source_probe_or_file)
        return self.__db.get_duplicate_data_for_id(source_id)

    def delete_duplicate_id(self, duplicate_id):
        """
        Deletes the duplicate record with the explicit duplicate_id,
        as returned by get_duplicate_data.
        """
        return self.__db.delete_duplicate_id(duplicate_id)

    def get_keywords_for(self, source_probe_or_file):
        if not isinstance(source_probe_or_file, str):
            source_probe_or_file = source_probe_or_file.filename
        source_id = self.__db.get_source_file_id(source_probe_or_file)
        return self.__db.get_keywords_for_id(source_id)

    def set_tags_for(self, source_probe_or_file, tags):
        """
        Changes all the db recorded tags for the file to reflect the new
        dictionary of values.
        """
        if not isinstance(source_probe_or_file, str):
            source_probe_or_file = source_probe_or_file.filename
        source_id = self.__db.get_source_file_id(source_probe_or_file)
        if source_id is None:
            return
        self.__db.remove_tags_for_source_id(source_id)
        for tk, tv in tags.items():
            if tv is not None and tk is not None and len(tv.strip()) > 0:
                self.__db.add_tag(source_id, tk, tv.strip())

        # Because the tags changed, the keywords changed, too
        self.__db.delete_keywords_for_source_id(source_id)
        for k in self._get_probe_keywords_for_tags(tags):
            self.__db.add_keyword(source_id, k)

    def get_tags_for(self, source_probe_or_file):
        if not isinstance(source_probe_or_file, str):
            source_probe_or_file = source_probe_or_file.filename
        source_id = self.__db.get_source_file_id(source_probe_or_file)
        return self.__db.get_tags_for_id(source_id)

    def get_source_files_without_tag_names(self, tag_names):
        return self.__db.get_source_files_without_tag_names(tag_names)

    def mark_found(self, probe):
        self._add_probe(probe)

    def delete_source_record(self, probe_or_filename):
        if not isinstance(probe_or_filename, str):
            probe_or_filename = probe_or_filename.filename
        source_id = self.__db.get_source_file_id(probe_or_filename)
        if source_id is None:
            return False
        target_file = self.__db.get_target_file(source_id)
        if target_file is not None:
            # TODO better error reporting
            print('ERROR will not delete record; transcode destination exists ({0})'.format(target_file))
            return False
        return self.__db.delete_source_graph(source_id)

    # For removing nasty files. If you really want this function,
    # strip off the '__'.
    def __remove_source_records_like(self, like, commit=False):
        source_ids = self.__db.get_source_file_ids_like(like)
        for source_id in source_ids:
            if source_id is None:
                return False

            if commit:
                r = self.__db.delete_source_graph(source_id)
                print("Removed {0} with source_id {1}", r, source_id)
            else:
                print(source_id)


    def get_exact_matches(self, probe):
        """
        Checks if the probe's key tags already exist in the database.
        """
        tags = {}
        for k in KEY_TAGS:
            v = probe.tag(k)
            if v is not None and len(v.strip()) > 0:
                tags[k] = v.strip()
        ret = self.__db.get_source_files_with_tags(tags)
        if probe.filename in ret:
            ret.remove(probe.filename)
        return ret

    def get_file_duplicate_tag_matches(self, probe):
        tags = {}
        for k in FILE_DUPLICATE_TAGS:
            v = probe.tag(k)
            if v is not None and len(v) > 0:
                tags[k] = v
            else:
                # The tag isn't on the file, so quit early.
                return []
        ret = self.__db.get_source_files_with_tags(tags)
        if probe.filename in ret:
            ret.remove(probe.filename)
        return ret

    def get_tag_matches(self, tags, exact=False):
        return self.__db.get_source_files_with_tags(tags, exact)

    def get_close_matches(self, probe, accuracy):
        """
        Accuracy is between 0 and 1
        """
        assert accuracy >= 0 and accuracy <= 1
        keywords = self._get_probe_keywords(probe)
        kcount = len(keywords)
        source_matches = {}
        for sk in self.__db.get_source_files_with_matching_keywords(keywords):
            filename = sk[0]
            k = sk[1]
            if filename not in source_matches:
                source_matches[filename] = set()
            source_matches[filename].add(k)
        ret = []
        for f in source_matches.keys():
            c = len(source_matches[f])
            if c / kcount >= accuracy:
                ret.append(f)
        return ret

    def transcoded_to(self, probe, target_file):
        """
        Does not mark as found; that must be done outside of here.
        """
        s_id = self.__db.get_source_file_id(probe.filename)
        if s_id is None:
            raise Exception('No such known source {0}'.format(prbe.filename))
        self.__db.add_target_file(s_id, target_file)

    def get_transcoded_to(self, probe_or_filename):
        if not isinstance(probe_or_filename, str):
            probe_or_filename = probe_or_filename.filename
        s_id = self.__db.get_source_file_id(probe_or_filename)
        if s_id is not None:
            return self.__db.get_target_file(s_id)
        return None

    def delete_transcoded_to(self, probe_or_filename):
        if not isinstance(probe_or_filename, str):
            probe_or_filename = probe_or_filename.filename
        s_id = self.__db.get_source_file_id(probe_or_filename)
        if s_id is not None:
            return self.__db.delete_transcoded_file_for_source_id(s_id) > 0
        return False

    def get_source_file_for_transcoded_filename(self, transcoded_filename):
        return self.__db.get_source_file_for_target_file(transcoded_filename)

    def get_transcoded_filenames(self, like=None):
        return self.__db.find_target_files(like)

    def get_duplicates(self, probe_or_filename):
        if not isinstance(probe_or_filename, str):
            probe_or_filename = probe_or_filename.filename
        dups = set()
        s_id = self.__db.get_source_file_id(probe_or_filename)
        if s_id is not None:
            dup_id = self.__db.get_duplicate_of_id(s_id)
            if dup_id is not None:
                dups.add(self.__db.get_source_file_for_id(dup_id))
            dups = dups.union(self.__db.get_duplicate_filenames_for_id(s_id))
        return dups

    def get_source_files(self, name_like=None):
        return self.__db.get_source_files_like(name_like)

    def _get_probe_keywords(self, probe):
        return self._get_probe_keywords_for_tags(probe.get_tags())

    def _get_probe_keywords_for_tags(self, tags):
        keywords = set()
        for tk, tv in tags.items():
            if tk not in SKIPPED_KEY_TAGS:
                keywords = keywords.union(_strip_keywords(tv))
        return keywords

    def _add_probe(self, probe):
        id = self.__db.add_source_file(probe.filename)
        for tk in probe.tag_keys:
            tv = probe.tag(tk)
            if tv is not None and tk is not None and len(tv) > 0:
                self.__db.add_tag(id, tk, tv)
        for k in self._get_probe_keywords(probe):
            self.__db.add_keyword(id, k)
        return id


def _strip_keywords(text):
    # Translate the text into simple ascii characters.
    # Ascii conversion is done AFTER word split.
    if text is None:
        return []
    r = []
    b = ''
    isc = True
    for c in text:
        if isc:
            if c.isalnum():
                b += c
            else:
                isc = False
                if len(b) > 0:
                    r.append(to_ascii(b))
                b = ''
        else:
            if c.isalnum():
                isc = True
                b = c
    if len(b) > 0:
        r.append(to_ascii(b))
    return r
