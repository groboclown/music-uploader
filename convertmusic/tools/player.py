'''
Plays a music file.
'''

import subprocess

class MediaPlayer(object):
    def __init__(self, args):
        self._active = None
        self._playing = None
        self._args = args

    def play_file(self, filename, force=False):
        '''
        Plays the music in the background.  If another song is already playing,
        then an error code is reported.
        '''
        if force:
            self._kill()
        cmds = self._create_cmd_arg_list(filename)
        self._fork(filename, cmds)

    def _create_cmd_arg_list(self, filename):
        cmds = []
        for a in self._args:
            cmds.append(a.format(filename))
        return cmds

    def _kill(self):
        if self._active is not None:
            self._active.terminate()
            self._active.wait()
            self._active = None
            self._playing = None

    def _fork(self, filename, args):
        if self._active is not None:
            res = self._active.poll()
            if res is None:
                raise Exception("still playing {0}".format(self._playing))
            # The command completed.
            self._playing = None
            self._active = None
        self._playing = filename
        # Allow stderr to still go to the output.
        self._active = subprocess.Popen(args, stdout=None)
