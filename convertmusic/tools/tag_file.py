
import subprocess
import os
import shutil

BIN_FFMPEG = 'ffmpeg'

def set_tags_on_file(filename, new_tags):
    """
    Assigns the given tags to the file.  Any existing tags are ignored.
    """
    old_file = _find_nonexist(filename)
    try:
        os.rename(filename, old_file)
        cmd = [
            BIN_FFMPEG, '-i', old_file,
            '-vn', '-acodec', 'copy'
        ]
        for k, v in new_tags.items():
            cmd.append('-metadata')
            cmd.append('{0}={1}'.format(k, v))
        cmd.append(filename)

        # force bits per sample = 16.
        subprocess.run(cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE)

        os.unlink(old_file)
    except:
        if os.path.isfile(old_file):
            if os.path.isfile(filename):
                os.unlink(filename)
            os.rename(old_file, filename)
        raise

def _find_nonexist(filename):
    index = 0
    fn = filename
    while os.path.isfile(fn):
        index += 1
        fn = '{0}.{1}.tmp'.format(filename, index)
    return fn
