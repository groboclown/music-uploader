#!/usr/bin/python3

import os
import sys
from convertmusic.db import get_history
from convertmusic.cmd import (
    Cmd, std_main, prompt_key, prompt_value
)

class CmdInteractive(Cmd):
    def __init__(self):
        self.name = 'interactive'
        self.desc = 'Interactive exploration of the catalogue.'
        self.help = ''

    def _cmd(self, history, args):
        count = 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: {0} (output-dir)".format(sys.argv[0]))
        print(("  {0:" + str(max_len) + "s}  {1}").format('output-dir',
            'The directory where the output was generated.  This will contain the media.db file.'))
        sys.exit(1)
    sys.exit(std_main([sys.argv[0], sys.argv[1], 'interactive']), [CmdInteractive()])
