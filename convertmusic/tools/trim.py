"""
Trims off time on an audio file.
"""

import os
import re
from .ffmpeg_bin import ffmpeg

def trim_audio(audio_file, dest_file, start_time, end_time):
    """
    Trims the audio in the file so that it fits between the two given times.

    The start and end times are either strings or numbers.  Strings can be int,
    float, or in "[[hh]:mm:]ss[.nn]" format.  Numbers are considered to be in seconds.

    If the time formats are invalid, then this returns False.  Otherwise, it returns True.
    """
    st = None
    if start_time is not None and start_time != '-':
        st = _convert_time(start_time)
        if st is None:
            print('Invalid start time format.')
            return False
        print('Start time will be {0}'.format(st))
    et = None
    if end_time is not None and end_time != '-':
        et = _convert_time(end_time)
        if et is None:
            print('Invalid end time format.')
            return False
        print('End time will be {0}'.format(st))
    if st is None and et is None:
        # Nothing to do!
        return
    
    ffmpeg.trim_audio(audio_file, dest_file, st, et)
    return os.path.isfile(dest_file)

    
TIME_FORMAT = re.compile(r'^\d\d:\d\d:\d\d(.\d\d?)$')
def _convert_time(t):
    if isinstance(t, int):
        seconds = t % 60
        minutes = t // 60
        hours = minutes // 60
        minutes = minutes % 60
        return '{0:02d}:{1:02d}:{2:02d}'.format(hours, minutes, seconds)
    if isinstance(t, float):
        seconds = int(t)
        micros = int(t * 100.0) % 100
        return _convert_time(seconds) + '.{0:02d}'.format(micros)
    if not isinstance(t, str):
        raise Exception('bad type: {0}'.format(type(t)))
    if t.count('.') > 1:
        print("At most 1 decimal can be used.")
        return None
    if t.count('.') > 0:
        pt,micro = t.split('.', 2)
    else:
        pt = t
        micro = '0'
    parts = pt.split(':')
    r = ''
    for p in parts:
        while len(p) < 2:
            p = '0' + p
        if len(r) > 0:
            r = r + ':' + p
        else:
            r = p
    while r.count(':') < 2:
        r = '00:' + r
    r = r + '.' + micro
    if TIME_FORMAT.match(r):
        return r
    print(
        "Tried to convert [{0}] to [{1}], but it doesn't match the expected format.".format(
            t, r))
    return None
