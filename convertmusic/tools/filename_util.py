

def simplify_name(name_root):
    name_root = to_ascii(name_root)
    ret = ''
    for c in name_root:
        if c.isalnum():
            ret += c
        elif c.isspace():
            if len(ret) > 0 and ret[-1] != '_':
                ret += '_'
        elif c in '-_':
            ret += c
    return ret

def to_filename(probe, dirname, ext):
    artist = probe.tag(tag.ARTIST_NAME)
    song = probe.tag(tag.SONG_NAME)
    name = None
    if artist is None and song is None:
        name = os.path.splitext(os.path.basename(probe.filename))[0]
    elif artist is None:
        name = song.strip()
    elif song is None:
        name = artist.strip() + "-unknown"
    else:
        name = artist.strip() + '-' + song.strip()
    if len(name) <= 0:
        name = 'x'
    if name[0] == '-':
        name = '_' + name[1:]
    # Maximum name length is 32 (roughly), so trim it down to 28 for the
    # extension.
    name = simplify_name(name)[0:31 - len(ext)]
    bn = os.path.join(dirname, name + '.' + ext)
    index = 0
    while os.path.isfile(bn):
        n = '-{0}'.format(index)
        bn = os.path.join(dirname, name[0:31 - len(ext) - len(n)] + n + '.' + ext)
        index += 1

    return bn
