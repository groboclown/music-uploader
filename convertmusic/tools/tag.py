"""
Generic library for tagging files and getting tags from files.
"""

SONG_NAME = 'title'
ARTIST_NAME = 'artist' # author?
ALBUM_NAME = 'album'
YEAR = 'year'
DATE = 'date'
COMMENT = 'comment'
TRACK = 'track'
GENRE_ID = 'genre'
ALBUM_ARTIST = 'album_artist'
LYRICS = 'lyrics'
DESCRIPTION = 'description'
TRACK_TOTAL = 'tracktotal'
SHA1 = 'sha1'
SHA256 = 'sha256'
SIZE_BYTES = 'size_bytes'

TEXT_TAGS = (
    SONG_NAME, ARTIST_NAME, ALBUM_NAME, COMMENT, ALBUM_ARTIST, DESCRIPTION
)
KEY_TAGS = (
    SONG_NAME, ARTIST_NAME
)
SKIPPED_KEY_TAGS = (
    TRACK, GENRE_ID, TRACK_TOTAL, YEAR, DATE, COMMENT
)
# If these match, then the song is a match.
FILE_DUPLICATE_TAGS = (
    SHA1, SHA256, SIZE_BYTES
)
