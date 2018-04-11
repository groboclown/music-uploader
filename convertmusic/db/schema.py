
from .meta import TableDef


SCHEMA = (
    TableDef('SOURCE_FILE')
        .with_column('source_file_id', 'INTEGER', None, 'PRIMARY KEY')
        .with_column('source_location', 'VARCHAR', None, 'UNIQUE'),
    TableDef('TARGET_FILE', columns=[
        ['target_file_id', 'INTEGER', None, 'PRIMARY KEY'],
        ['source_file_id', 'INTEGER', None, 'UNIQUE'],
        ['target_location', 'VARCHAR', None, 'UNIQUE']
    ]),
    TableDef('TAG', columns=[
        ['tag_id', 'INTEGER', None, 'PRIMARY KEY'],
        ['source_file_id', 'INTEGER'],
        ['tag_name', 'VARCHAR(100)'],
        ['tag_value', 'VARCHAR']
    ]),

    # Rather than normalize the table into KEYWORD and adding the index here,
    # we'll just shove them all into this one table to eliminate the extra
    # join.
    TableDef('FILE_KEYWORD', [
        ['file_keyword_id', 'INTEGER', None, 'PRIMARY KEY'],
        ['source_file_id', 'INTEGER'],
        ['keyword', 'NVARCHAR']
    ]),

    TableDef('DUPLICATE_FILE', [
        ['duplicate_id', 'INTEGER', None, 'PRIMARY KEY'],
        ['source_file_id', 'INTEGER', None, 'UNIQUE'],
        ['duplicate_of_source_file_id', 'INTEGER']
    ])
)
