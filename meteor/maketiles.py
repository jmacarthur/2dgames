import sys
import os

from blocktypes import blocktypes
sprites = []
reverseMap = {}
maxNum = 0
for (k,v) in blocktypes.iteritems():
    reverseMap[v] = k
    print "%d = %s"%(v,k)
    if(v > maxNum): maxNum = v

for i in range(0,maxNum+1):
    try: 
        sprites.append( reverseMap[i]+".png")
    except KeyError:
        print "Unknown number %d"%(i)

cmd = "montage -tile x1 -geometry +0+0 "+" ".join(sprites)+" tiles.png"
print cmd

os.system(cmd)

