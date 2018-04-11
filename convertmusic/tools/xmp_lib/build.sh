#!/bin/bash

if [ ! -f "$1" ]; then
  echo "Usage: $0 (path/to/include/xmp.h)"
  exit 1
fi

if [ ! -d "ctypesgen" ]; then
  git clone https://github.com/davidjamesca/ctypesgen.git || exit 1
  ( cd ctypesgen && git checkout python-3 ) || exit 1
fi
python2 ctypesgen/ctypesgen.py -x XMP_VER.* -lxmp "$1" -o libxmp.py --insert-file=interface.py || exit 1

# BSD sed *requires* an extension argument to -i
sed -i.bak "s/^xmp_context = String/xmp_context = c_long/;s/ \* 1)/ * 256)/;s/\'xpo\', c_char/\'xpo\', c_byte/;s/\t/        /;s/sys.maxint/sys.maxsize/" libxmp.py || exit 1
