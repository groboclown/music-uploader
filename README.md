# Convert Your Music Library

I have a messy music library, and I want to make a USB stick of my music
that's in a compatible format for my car.  This project contains tools that
converts the files to a compatible format, puts them into a shallow directory
structure that the limited file manager can deal with, simplifies the names
of the files so that they don't contain weirdness, tries to fix or guess
the media file tagging, and so on.

If the media file is already in a compatible format, then it is simply
copied to the output directory, rather than transcoded.

It keeps a database in the output directory of the visited files, their
discovered tags, their generated files, and the detected duplicates.


# Running

The general conversion is done by:

```
python3 main.py (source music directory) (output directory)
```

The other tools in the root directory are for managing the transcoded
files.

You can add a file `.skip` in any directory you want to skip.  Those will not
be scanned for audio files.

# Dependencies:

Right now, this uses:

* `libxmp.so`
  * for module/tracker files, like `.mod` and `.it`
* `ffmpeg` and `ffprobe`
  * for sampled audio files, like `.mp3` and `.flac`


# About the Conversion

The conversion attempts to transcode the audio files to meet several
standards.

The first is the file names.  File names are assumed to be limited to 32
characters long, only ASCII names, and with a file extension that matches
the codec's standard extension.  Additionally, the files are sorted into
shallow directories (1 deep), with a maximum of 1000 files per directory.

The second standard is the allowed file types.

* MP3
  * mpeg1 layer3
    * frequencies: 32k, 44.1k, 48k
    * bit rates: 32-320 kbps
  * mpeg2 lsf layer3
    * frequencies: 16k, 22.05k, 24k
    * bit rates: 8-160 kbps
* WMA
  * version 7, 8, 9
    * frequencies: 32k, 44.1k, 48k
    * v7,8 bit rates: 48-192 kbps
    * v9 bit rates: 48-320 kpbs
* AAC
    * mpeg4/aac-lc
        * frequencies: 11.025, 12, 16, 22.05, 24, 32, 44.1, 48
        * bit rates: 16-320


# To Dos

* Add support for more mod files, like:
  * `.ahx` files (Amiga tracker files)
  * `.mo3` files.
* Improve mod file comment parsing.
* Improve the metadata fixup tool.
