
import os
import subprocess

BIN_FFMPEG = 'ffmpeg'

def convert(srcfile, outfile, bit_rate, channels, sample_rate, codec, tags):
    """
    Converts the source file to the outfile with the proper transformations.
    Includes the additional tags.
    """

    if os.path.isfile(outfile):
        os.unlink(outfile)
    
    cmd = [
        BIN_FFMPEG, '-i', srcfile,
        '-vn', '-acodec', codec, '-ar', str(sample_rate),
        '-ac', str(channels), '-b:a', str(bit_rate),
        '-bits_per_raw_sample', '16'
    ]
    for k, v in tags.items():
        cmd.append('-metadata')
        cmd.append('{0}={1}'.format(k, v))
    cmd.append(outfile)

    # force bits per sample = 16.
    subprocess.run(cmd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE)
