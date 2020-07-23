import os
import shutil
from .probe import MediaProbe
from .filename_util import to_filename


def copy_file(src_file, target_file):
    shutil.copyfile(src_file, target_file)


def transcode_correct_format(history, probe, dest_dir, verbose=False):
    # Supported formats:
    # If the format is not exactly one of these, then re-encode it.
    #   MP3
    #     mpeg1 layer3
    #        frequencies: 32k, 44.1k, 48k
    #        bit rates: 32-320 kbps
    #     mpeg2 lsf layer3
    #        frequencies: 16k, 22.05k, 24k
    #        bit rates: 8-160 kbps
    #   WMA
    #     version 7, 8, 9
    #     frequencies: 32k, 44.1k, 48k
    #     v7,8 bit rates: 48-192 kbps
    #     v9 bit rates: 48-320 kbps
    #   AAC
    #     mpeg4/aac-lc
    #     frequencies: 11.025, 12, 16, 22.05, 24, 32, 44.1, 48
    #     bit rates: 16-320 kbps

    assert isinstance(probe, MediaProbe)
    assert os.path.isdir(dest_dir)

    if probe.codec.lower() == 'mp3':
        if (probe.sample_rate in (32000, 44100, 48000) and
                (probe.bit_rate >= 32000 and probe.bit_rate <= 320000) and
                probe.channels == 2):
            destfile = to_filename(history, probe, dest_dir, '.mp3')
            if verbose:
                print("Transcode: copying original file.")
            copy_file(probe.filename, destfile)
            return destfile
    if probe.codec.lower() == 'wma':
        if (probe.sample_rate in (32000, 44100, 48000) and
                (probe.bit_rate >= 48000 and probe.bit_rate <= 192000) and
                probe.channels == 2):
            destfile = to_filename(history, probe, dest_dir, 'wma')
            if verbose:
                print("Transcode: copying original file.")
            copy_file(probe.filename, destfile)
            return destfile
    if probe.codec.lower() == 'aac':
        if (probe.sample_rate in (11025, 12000, 16000, 22050, 24000, 32000, 44100, 48000) and
                (probe.bit_rate >= 16000 and probe.bit_rate <= 32000) and
                probe.channels == 2):
            destfile = to_filename(history, probe, dest_dir, '.m4a')
            if verbose:
                print("Transcode: copying original file.")
            copy_file(probe.filename, destfile)
            return destfile
    if probe.codec.lower() == 'flac':
        # Best quality AAC conversion
        destfile = to_filename(history, probe, dest_dir, '.m4a')
        probe.transcode(destfile, sample_rate=48000, bit_rate=320000, channels=2, codec='aac', verbose=verbose)
        return destfile

    # Convert to aac, without losing quality.
    bit_rate = probe.bit_rate
    sample_rate = probe.sample_rate
    for sr in (11025, 12000, 16000, 22050, 24000, 32000, 44100, 48000):
        if sample_rate < sr:
            sample_rate = sr
            break
    if bit_rate < 16000:
        bit_rate = 16000
    if bit_rate > 320000:
        bit_rate = 320000
    destfile = to_filename(history, probe, dest_dir, 'm4a')
    probe.transcode(destfile, sample_rate=sample_rate, bit_rate=bit_rate, channels=2, codec='aac', verbose=verbose)
    return destfile
