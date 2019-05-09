
import os
import subprocess
import re

BIN_FFMPEG = 'ffmpeg'

def convert(srcfile, outfile, bit_rate, channels, sample_rate, codec, tags, volume=None):
    """
    Converts the source file to the outfile with the proper transformations.
    Includes the additional tags.
    """
    if srcfile == outfile:
        raise Exception('Does not support overwriting file')

    if os.path.isfile(outfile):
        os.unlink(outfile)
    
    cmd = [
        BIN_FFMPEG, '-i', srcfile,
        '-vn', '-sn', '-dn',
        '-acodec', codec, '-ar', str(sample_rate),
        '-ac', str(channels), '-b:a', str(bit_rate),
        '-bits_per_raw_sample', '16'
    ]
    if volume:
        cmd.append('-filter:a')
        cmd.append("volume={0}".format(volume))
    for k, v in tags.items():
        cmd.append('-metadata')
        cmd.append('{0}={1}'.format(k, v))
    cmd.append(outfile)

    # force bits per sample = 16.
    subprocess.run(cmd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE)


def trim_audio(srcfile, outfile, start_time, end_time):
    """
    Trims audio.  Start and end time must be in the "hh:mm:ss.nn" format (e.g. 00:01:22.00)
    """
    if srcfile == outfile:
        raise Exception('Does not support overwriting file')

    if os.path.isfile(outfile):
        os.unlink(outfile)
    
    cmd = [
        BIN_FFMPEG, '-i', srcfile,
        #'-movflags', 'use_metadata_tags',
        '-map_metadata', '0:g',
        '-map_metadata:s:a', '0:g',
        '-c', 'copy'
    ]
    if start_time is not None:
        cmd.extend(['-ss', start_time])
    if end_time is not None:
        cmd.extend(['-to', end_time])

    cmd.append(outfile)

    print('Running "{0}"'.format(' '.join(cmd)))
    subprocess.run(cmd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE)


LINE_MEAN_VOLUME = \
    re.compile(r'\[Parsed_volumedetect_\d+ @ ([^\]]+)\] mean_volume: (-?\d+\.?\d*) dB')
LINE_MAX_VOLUME = \
    re.compile(r'\[Parsed_volumedetect_\d+ @ ([^\]]+)\] max_volume: (-?\d+\.?\d*) dB')
LINE_HISTOGRAM_VOLUME = \
    re.compile(r'\[Parsed_volumedetect_\d+ @ ([^\]]+)\] histogram_(\d+)db: (-?\d+\.?\d*)')

class VolumeLevel(object):
    def __init__(self, mean_v, max_v, hist):
        self.mean = mean_v
        self.max = max_v
        self.histogram = hist

def find_volume_levels(srcfile):
    """
    """
    cmd = [
        BIN_FFMPEG, '-i', srcfile,
        '-af', "volumedetect",
        '-vn', '-sn', '-dn',
        '-f', 'null', os.path.devnull
    ]

    # print('DEBUG running [{0}]'.format(' '.join(cmd)))
    proc = subprocess.run(cmd, check=True,
        #capture_output=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        encoding='utf-8', errors='ignore')
    max_volume = None
    mean_volume = None
    histogram = {}
    for line in proc.stdout.splitlines():
        line = line.strip()
        # print('DEBUG output [{0}]'.format(line))
        m = LINE_MEAN_VOLUME.match(line)
        if m:
            mean_volume = float(m.group(2))
            # print('DEBUG mean_volume = {0} / {1}'.format(m.group(2), mean_volume))
        m = LINE_MAX_VOLUME.match(line)
        if m:
            max_volume = float(m.group(2))
            # print('DEBUG max_volume = {0} / {1}'.format(m.group(2), max_volume))
        m = LINE_HISTOGRAM_VOLUME.match(line)
        if m:
            histogram[m.group(2)] = float(m.group(3))
            # print('DEBUG histogram {0}db = {1}'.format(m.group(2), m.group(3)))
    if mean_volume is None or max_volume is None or histogram is None:
        return None
    return VolumeLevel(mean_volume, max_volume, histogram)
