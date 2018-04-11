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
discovered tags, and the duplicate detections.


# Running

The general conversion is done by:

```
python3 main.py (source music directory) (output directory)
```

The other tools in the root directory are for managing the transcoded
files.


# Dependencies:

Right now, this uses:

* `libxmp.so`
  * for module/tracker files, like `.mod` and `.it`
* `ffmpeg` and `ffprobe`
  * for sampled audio files, like `.mp3` and `.flac`


# To Dos

* Add support for more mod files, like:
  * `.ahx` files (Amiga tracker files)
  * `.mo3` files.
* Improve mod file comment parsing.
* Improve the metadata fixup tool.

