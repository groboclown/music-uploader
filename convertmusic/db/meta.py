
import sqlite3
import os


class Table(object):
    def __init__(self, conn, table_name, columns):
        """
        columns: list of columns, which is itself a list of:
            column name, column SQL type, default value, is index.
            First column is always the primary key (never inserted)
        """
        object.__init__(self)
        self.__name = table_name
        self.__conn = conn
        self.__identity_column_name = columns[0]
        self.__insert_column_names = []
        # skip the unique column id
        for c in columns[1:]:
            self.__insert_column_names.append(c[0])
        upgrade = False
        c = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", [table_name])
        for row in c:
            if row[0] == table_name:
                upgrade = True
        c.close()
        if upgrade:
            # TODO allow upgrade
            pass
        else:
            col_sql = []
            for c in columns:
                s = '{0} {1}'.format(c[0], c[1])
                if len(c) > 2 and c[2] is not None:
                    s += ' DEFAULT {0}'.format(c[2])
                if len(c) > 3 and c[3] is not None:
                    s += ' {0}'.format(c[3])
                col_sql.append(s)
            sql = 'CREATE TABLE {0} ({1})'.format(table_name, ','.join(col_sql))
            conn.execute(sql)
        conn.commit()

    def insert(self, *values):
        vs = []
        for n in values:
            vs.append('?')
        c = self.__conn.execute("INSERT INTO {0} ({1}) VALUES ({2})".format(
            self.__name, ','.join(self.__insert_column_names), ','.join(vs)
        ), values)
        r = c.lastrowid
        c.close()
        self.__conn.commit()
        return r

    def delete_by_id(self, id):
        c = self.__conn.execute("DELETE FROM {0} WHERE {1} = ?".format(
            self.__name, self.__identity_column_name
        ), [id])
        ret = c.rowcount
        c.close()
        self.__conn.commit()
        return ret > 0

    def delete_where(self, where_clause, *values):
        c = self.__conn.execute('DELETE FROM {0} WHERE {1}'.format(
            self.__name, where_clause), values)
        ret = c.rowcount
        c.close()
        self.__conn.commit()
        return ret

    def close(self):
        self.__conn = None

    def __del__(self):
        self.close()


class TableDef(object):
    def __init__(self, name, columns=None):
        object.__init__(self)
        self.__name = name
        self.__columns = []
        if columns is not None:
            self.__columns.extend(columns)

    def with_column(self, name, type, default=None, index=None):
        self.__columns.append([name, type, default, index])
        return self

    @property
    def name(self):
        return self.__name

    @property
    def columns(self):
        return self.__columns


class Db(object):
    def __init__(self, filename, table_defs):
        """
        table_defs: list of TableDef instances.
        """
        object.__init__(self)
        self.__conn = sqlite3.connect(filename)
        self.__tables = {}
        for td in table_defs:
            assert isinstance(td, TableDef)
            t = Table(self.__conn, td.name, td.columns)
            self.__tables[td.name] = t

    def __del__(self):
        self.close()

    def close(self):
        if self.__conn is not None:
            self.__conn.close()
            self.__conn = None

    def query(self, query, *values):
        """
        Returns iterable rows.
        """
        #print("DEUBG query: {0}".format(repr(query)))
        c = self.__conn.execute(query, values)
        for r in c:
            yield r
        c.close()

    def table(self, name):
        return self.__tables[name]
