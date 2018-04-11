
from .db_api import DbApi
from .meta import Db
from .schema import *

class Impl(DbApi):
    def __init__(self, db):
        assert isinstance(db, Db)
        DbApi.__init__(self)
        self.__db = db

    def __del__(self):
        self.close()

    def close(self):
        if self.__db is not None:
            self.__db.close()
            self.__db = None

    def add_source_file(self, filename):
        """
        Returns the ID for the source file.  Raises exception if it
        already exists.
        """
        return self.__db.table('SOURCE_FILE').insert(filename)

    def get_source_file_id(self, filename):
        """
        Returns the ID for the source file, or None if not present.
        """
        c = self.__db.query(
            "SELECT source_file_id FROM SOURCE_FILE WHERE source_location = ?",
            filename
        )
        ret = None
        for r in c:
            ret = r[0]
            c.close()
            break
        return ret

    def get_source_file_for_id(self, source_file_id):
        c = self.__db.query(
            "SELECT source_location FROM SOURCE_FILE WHERE source_file_id = ?",
            source_file_id
        )
        ret = None
        for r in c:
            ret = r[0]
            c.close()
            break
        return ret

    def add_tag(self, file_id, tag_name, tag_value):
        """
        Returns the ID of the tag.
        """
        return self.__db.table('TAG').insert(
            file_id, tag_name, tag_value
        )

    def add_keyword(self, file_id, keyword):
        """
        Returns the ID of the keyword.
        """
        return self.__db.table('FILE_KEYWORD').insert(
            file_id, keyword
        )

    def delete_keywords_for_source_id(self, file_id):
        return self.__db.table('FILE_KEYWORD').delete_where(
            'source_file_id = ?',
            file_id
        )

    def get_keywords_for_id(self, file_id):
        ret = set()
        c = self.__db.query(
            'SELECT keyword FROM FILE_KEYWORD WHERE source_file_id = ?',
            file_id
        )
        for r in c:
            ret.add(r[0])
        return ret

    def get_tags_for_id(self, file_id):
        ret = {}
        c = self.__db.query(
            'SELECT tag_name, tag_value FROM TAG WHERE source_file_id = ?',
            file_id
        )
        for r in c:
            ret[r[0]] = r[1]
        return ret

    def add_target_file(self, source_file_id, target_filename):
        """
        Returns the ID of the target file.
        """
        return self.__db.table('TARGET_FILE').insert(
            source_file_id, target_filename
        )

    def get_target_file(self, source_file_id):
        ret = None
        c = self.__db.query(
            'SELECT target_location FROM TARGET_FILE WHERE source_file_id = ?',
            source_file_id
        )
        for r in c:
            ret = r[0]
            c.close()
            break
        return ret

    def get_source_id_for_target_file(self, target_filename):
        ret = None
        c = self.__db.query(
            'SELECT source_file_id FROM TARGET_FILE WHERE target_location = ?',
            target_filename
        )
        for r in c:
            ret = r[0]
            c.close()
            break
        return ret

    def get_source_file_for_target_file(self, target_filename):
        ret = None
        c = self.__db.query(
            """
            SELECT source_location FROM SOURCE_FILE sf
            INNER JOIN TARGET_FILE tf ON sf.source_file_id = tf.source_file_id
            WHERE target_location = ?
            """,
            target_filename
        )
        for r in c:
            ret = r[0]
            c.close()
            break
        return ret

    def find_target_files(self, target_match=None):
        ret = set()
        if target_match is None:
            c = self.__db.query('SELECT target_location FROM TARGET_FILE')
        else:
            c = self.__db.query(
                'SELECT target_location FROM TARGET_FILE WHERE target_location LIKE ?',
                target_match
            )
        for r in c:
            ret.add(r[0])
        return ret

    def get_source_files_with_tags(self, tags):
        """
        Returns the source file names that has the matching tag keys to tag values.
        If none are found, then an empty list is returned.
        """
        # This is a messy query that really doesn't work with sqlite.
        # So instead we'll do multiple queries and shrink the result
        # down in code.
        tag_keys = []
        tag_values = []
        for k, v in tags.items():
            tag_keys.append(k)
            tag_values.append(v)
        if len(tag_keys) <= 0:
            return []

        matching_file_ids = set()
        c = self.__db.query(
            'SELECT source_file_id FROM TAG WHERE tag_name = ? and tag_value = ?',
            tag_keys[0], tag_values[0]
        )
        for r in c:
            matching_file_ids.add(str(r[0]))
        if len(matching_file_ids) <= 0:
            return []

        for i in range(1, len(tag_keys)):
            c = self.__db.query(
                'SELECT source_file_id FROM TAG WHERE tag_name = ? AND tag_value = ? AND source_file_id in ({0})'.format(
                    ','.join('?' * len(matching_file_ids))),
                tag_keys[i], tag_values[i], *matching_file_ids
            )
            matching_file_ids = set()
            for r in c:
                matching_file_ids.add(str(r[0]))
            c.close()
            if len(matching_file_ids) <= 0:
                return []

        c = self.__db.query(
            'SELECT source_location FROM SOURCE_FILE WHERE source_file_id in ({0})'.format(
                ','.join('?' * len(matching_file_ids))),
            *matching_file_ids
        )
        ret = []
        for r in c:
            ret.append(r[0])
        return ret

    def get_source_files_with_matching_keywords(self, keywords):
        """
        Returns a list of [source file name, keyword],
        possibily with duplicate source files, for any keyword.
        """
        ksql = []
        for k in keywords:
            ksql.append('?')
        c = self.__db.query(
            '''SELECT source_location, keyword FROM FILE_KEYWORD fk
            INNER JOIN SOURCE_FILE sf
                ON fk.source_file_id = sf.source_file_id
            WHERE keyword IN ({0})'''.format(','.join(ksql)),
            *keywords
        )
        ret = []
        for r in c:
            ret.append((r[0], r[1]))
        return ret

    def add_duplicate(self, source_id, duplicate_of_id):
        return self.__db.table('DUPLICATE_FILE').insert(
            source_id, duplicate_of_id
        )

    def get_duplicate_of_id(self, source_id):
        """
        Returns the source file ID of the file marked as a duplicate of the
        source file.
        """
        c = self.__db.query(
            'SELECT duplicate_of_source_file_id FROM DUPLICATE_FILE WHERE source_file_id = ?',
            source_id
        )
        ret = None
        for r in c:
            ret = r[0]
            c.close()
            break
        return ret

    def get_duplicate_ids_for_id(self, duplicate_of_id):
        """
        Get the source id for the duplicate_of_id.
        """
        ret = set()
        c = self.__db.query(
            'SELECT source_file_id FROM DUPLICATE_FILE WHERE duplicate_of_source_file_id = ?',
            duplicate_of_id
        )
        for r in c:
            ret.add(r[0])
        return ret

    def get_duplicate_filenames_for_id(self, source_id):
        """
        Get the filenames for any duplicate of the source id.  Does not
        look for duplicates of duplicates.
        """
        ret = []
        for d in self.get_duplicate_data_for_id(source_id):
            ret.append(d['location'])
        return ret

    def get_duplicate_data_for_id(self, source_id):
        """
        Returns any duplicate of the source id as get_duplicate_filenames_for_id.
        Each value in the returned collection is a dictionary.
        Does not look for duplicates of duplicates.
        """
        dup_ids = set()
        ret = []
        c = self.__db.query(
            """SELECT
                sf.source_file_id, sf.source_location, d.duplicate_id, d.duplicate_of_source_file_id
            FROM SOURCE_FILE sf
            INNER JOIN DUPLICATE_FILE d
                ON sf.source_file_id = d.source_file_id
            WHERE d.duplicate_of_source_file_id = ?
            """,
            source_id
        )
        for r in c:
            if r[0] not in dup_ids and r[0] != source_id:
                dup_ids.add(r[0])
                ret.append({
                    'source_file_id': r[0],
                    'source_location': r[1],
                    'duplicate_id': r[2],
                    'duplicate_of_source_file_id': r[3],

                    # User meaningful data
                    'filename': r[1]
                })
        c = self.__db.query(
            """SELECT
                sf.source_file_id, sf.source_location, d.duplicate_id, d.duplicate_of_source_file_id
            FROM SOURCE_FILE sf
            INNER JOIN DUPLICATE_FILE d
                ON sf.source_file_id = d.duplicate_of_source_file_id
            WHERE d.source_file_id = ?
            """,
            source_id
        )
        for r in c:
            if r[2] not in dup_ids and r[2] != source_id:
                dup_ids.add(r[0])
                ret.append({
                    'source_file_id': r[0],
                    'source_location': r[1],
                    'duplicate_id': r[2],
                    'duplicate_of_source_file_id': r[3],

                    # User meaningful data
                    'filename': r[1]
                })
            ret.add(r[0])
        return ret

    def delete_duplicate_id(self, duplicate_id):
        return self.__db.table('DUPLICATE_FILE').delete_by_id(duplicate_id)

    def get_source_files_like(self, name_like=None):
        ret = set()
        if name_like is None:
            c = self.__db.query('SELECT source_location FROM SOURCE_FILE')
        else:
            c = self.__db.query(
                'SELECT source_location FROM SOURCE_FILE WHERE source_location LIKE ?',
                name_like
            )
        for r in c:
            ret.add(r[0])
        return ret

    def remove_tags_for_source_id(self, source_id):
        return self.__db.table('TAG').delete_where(
            "source_file_id = ?",
            source_id
        )

    def delete_source_graph(self, source_id):
        self.__db.table('DUPLICATE_FILE').delete_where(
            "duplicate_of_source_file_id = ? OR source_file_id = ?",
            source_id, source_id
        )
        self.__db.table('FILE_KEYWORD').delete_where(
            "source_file_id = ?",
            source_id
        )
        self.__db.table('TAG').delete_where(
            "source_file_id = ?",
            source_id
        )
        self.__db.table('TARGET_FILE').delete_where(
            "source_file_id = ?",
            source_id
        )
        return self.__db.table('SOURCE_FILE').delete_by_id(source_id)


    def get_source_files_without_tag_names(self, tag_names):
        ret = set()
        c = self.__db.query("""
            SELECT source_location, tag_value FROM SOURCE_FILE sf
            LEFT OUTER JOIN TAG t
                ON sf.source_file_id = t.source_file_id
            WHERE t.tag_name in ({0})
            """.format(', '.join('?' * len(tag_names))), *tag_names)
        for r in c:
            if r[1] is None or len(r[1].strip()) <= 0:
                ret.add(r[0])
        return ret
