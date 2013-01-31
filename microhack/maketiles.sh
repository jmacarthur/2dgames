#!/bin/bash

convert -size 32x32 xc:#7f7f7f gray1.png
convert -size 32x32 xc:#3f3f3f darkgray1.png
convert -size 32x32 xc:#ffffff white.png
convert -size 32x32 xc:#ff0000 red.png
convert -size 32x32 xc:#7f7fff lightblue.png
convert -size 32x32 xc:#0000ff darkblue.png
convert -size 32x32 xc:#00ff00 brightgreen.png
convert -size 32x32 xc:#007f00 darkgreen.png
convert -size 32x32 xc:#7f0000 darkred.png
convert -size 32x32 xc:#ff00ff pink.png
convert -size 32x32 xc:#ffff00 yellow.png
convert -size 32x32 xc:#00ffff cyan.png

montage gray1.png darkgray1.png white.png red.png lightblue.png darkblue.png brightgreen.png darkgreen.png darkred.png pink.png yellow.png cyan.png -geometry 32x32 -tile 15x1 test.png