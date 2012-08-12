import os

from spritenames import spriteNames

sourceSprites = [  ]

expect = 1
for (k,v) in spriteNames.iteritems():
    if(k != expect):
        print "Sprites out of sequence; expected %s to be %d but was %d"%(v,expect,k)
    singularFilename = "tiles/%s.png"%v
    if os.path.exists(singularFilename):
        sourceSprites.append(singularFilename)
    else:
        multipleFilename = "tiles/%s0.png"%v
        if os.path.exists(multipleFilename):
            sourceSprites.append(multipleFilename)
        else:
            print "No tile found: %s"%v
            exit(1)

    expect += 1

command = "montage -tile x1 -geometry +0+0 "+" ".join(sourceSprites)+" tiles/tileset1.png"

os.system(command)

