
from .api import MediaFileHistory

def get_history(db_filename):
    from .schema import SCHEMA
    from .meta import Db
    from .impl import Impl
    db = Db(db_filename, SCHEMA)
    return MediaFileHistory(Impl(db))
