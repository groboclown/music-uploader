
"""
Transforms the path of the transcoded file from one base directory
to another.  Not useful for the standard transcode operation, but
necessary when moving the USB mount point from one computer to
another.
"""

_TRANSCODE_ORIGINAL_BASE = None
_TRANSCODE_TRANSFORM_BASE = None


def tform_tcode(original_transcode_file):
    """
    Transform the database stored transcoded filename into the local
    filename.
    """
    assert isinstance(original_transcode_file, str)
    if _TRANSCODE_ORIGINAL_BASE is None or _TRANSCODE_TRANSFORM_BASE is None:
        return original_transcode_file

    if not original_transcode_file.startswith(_TRANSCODE_ORIGINAL_BASE):
        return original_transcode_file
    return _TRANSCODE_TRANSFORM_BASE + original_transcode_file[len(_TRANSCODE_ORIGINAL_BASE):]


def reverse_tcode(current_transcode_file):
    """
    Transform the local transcoded filename into the database stored
    transcoded filename.
    """
    assert isinstance(current_transcode_file, str)
    if _TRANSCODE_ORIGINAL_BASE is None or _TRANSCODE_TRANSFORM_BASE is None:
        return current_transcode_file

    if not current_transcode_file.startswith(_TRANSCODE_TRANSFORM_BASE):
        return current_transcode_file
    return _TRANSCODE_ORIGINAL_BASE + current_transcode_file[len(_TRANSCODE_TRANSFORM_BASE):]


def set_transcode_transform(original_base, transform_base):
    """
    Set the path transformation used for the transcoded filenames.
    """
    assert isinstance(original_base, str) and len(original_base) > 0
    assert isinstance(transform_base, str) and len(transform_base) > 0

    if original_base.endswith('/') or original_base.endswith('\\'):
        assert transform_base.endswith('/') or transform_base.endswith('\\')

    global _TRANSCODE_ORIGINAL_BASE
    _TRANSCODE_ORIGINAL_BASE = original_base
    global _TRANSCODE_TRANSFORM_BASE
    _TRANSCODE_TRANSFORM_BASE = transform_base


_SOURCE_ORIGINAL_BASE = None
_SOURCE_TRANSFORM_BASE = None


def tform_src(original_src_file):
    """
    Transform the database stored source filename into the local
    filename.
    """
    assert isinstance(original_src_file, str)
    if _SOURCE_ORIGINAL_BASE is None or _SOURCE_TRANSFORM_BASE is None:
        return original_src_file

    if not original_src_file.startswith(_SOURCE_ORIGINAL_BASE):
        return original_src_file
    return _SOURCE_TRANSFORM_BASE + original_src_file[len(_SOURCE_ORIGINAL_BASE):]


def reverse_source(current_source_file):
    """
    Transform the local source filename into the database stored
    source filename.
    """
    assert isinstance(current_source_file, str)
    if _SOURCE_ORIGINAL_BASE is None or _SOURCE_TRANSFORM_BASE is None:
        return current_source_file

    if not current_source_file.startswith(_SOURCE_TRANSFORM_BASE):
        return current_source_file
    return _SOURCE_ORIGINAL_BASE + current_source_file[len(_SOURCE_TRANSFORM_BASE):]


def set_source_transform(original_base, transform_base):
    """
    Set the path transformation used for the source filenames.
    """
    assert isinstance(original_base, str) and len(original_base) > 0
    assert isinstance(transform_base, str) and len(transform_base) > 0

    if original_base.endswith('/') or original_base.endswith('\\'):
        assert transform_base.endswith('/') or transform_base.endswith('\\')

    global _SOURCE_ORIGINAL_BASE
    _SOURCE_ORIGINAL_BASE = original_base
    global _SOURCE_TRANSFORM_BASE
    _SOURCE_TRANSFORM_BASE = transform_base
