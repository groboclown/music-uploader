"""
Normalizes the audio.
"""

import os
from .ffmpeg_bin import ffmpeg, ffprobe


EPSILON = 0.0001

def normalize_audio(audio_file, dest_file, headroom=0.1):
    """
    Attempts to normalize the audio.  It does so through a two-pass
    approach of first finding the peak level, then estimating an
    "almost" peak level to amplify the volume to.  "Almost" here
    means giving the audio a 'headroom' amount of loudness space.
    Clipped files - those where the existing headroom is 0, will
    not be adjusted, because it's already at a volume where nothing
    can be done to save it, or it's one of those "loudness contest"
    songs, where the volume is calculated to make it sound louder
    than the speakers can handle.

    This will not overwrite the source file, so that errors or
    bad normalizations don't corrupt the source.

    Returns None if no action is performed, otherwise returns the
    volume adjustment level (float), in dB (positive means increased
    level, negative decreased).
    """
    if headroom < 0:
        # Can't do anything with this.
        return None
    if os.path.samefile(audio_file, dest_file):
        return None
    # Find the current audio settings
    probe = ffprobe.probe(audio_file)
    if probe is None:
        raise Exception('Could not inspect {0}'.format(audio_file))
    volume_levels = ffmpeg.find_volume_levels(audio_file)
    if volume_levels is None:
        raise Exception('Could not read volume levels for {0}'.format(audio_file))
    
    # Now estimate the right peak level.  Peak level is the
    # amount *below* 0, so these are negative numbers.
    max_peak = volume_levels.max
    if max_peak >= -EPSILON:
        # Woah.  This is a clipped audio.  Changing the volume
        # won't do much for us.
        return None
    # However, we also don't want to go below the mean.  That would be mean.
    # ha ha.
    if -headroom < volume_levels.mean:
        # Just too loud!  Too much!
        return None
    
    # Find the increase that will give us our headroom.
    increase = abs(max_peak) - headroom

    ffmpeg.convert(audio_file, dest_file,
        bit_rate=probe.bit_rate,
        channels=probe.channels,
        sample_rate=probe.sample_rate,
        codec=probe.codec,
        tags=probe.get_tags(),
        volume="{0:#.1f}dB".format(increase))
    return increase
