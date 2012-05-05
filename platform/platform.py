# Grid-based platform game skeleton by Jim MacArthur                                                

import pygame
from pygame.locals import *

pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption('2D Platform Framework')
clock = pygame.time.Clock()

GSY = 100 # Grid size (in blocks)
GSX = 100
BS = 32   # Block size (in pixels)

def makegrid(x,y,default=0):
    v = [0]*y
    for i in range(0,y):
        v[i] = [default]*x
    return v

background = pygame.Surface(screen.get_size())
background = background.convert()
background.fill((0, 0, 0))

# Load Level                                                                          
blocks = makegrid(GSX,GSY)
startx = 0
starty = 0              

def loadLevel(filename):
    global blocks, startx, starty
    fp = open(filename,'r')
    y = 0
    l = fp.readline()
    while(l != '' and y<GSY):
        print "Reading line %d: %s"%(y,l)
        for x in range(0,min(GSX,len(l))):
            if(l[x] == '#'):
                blocks[y][x] = 1
            elif(l[x] == 'v'):
                blocks[y][x] = 0
                startx =x
                starty =y
            else:
                blocks[y][x] = 0
        l = fp.readline()
        y+=1

loadLevel("level1.txt")

px = startx*BS
py = starty*BS

def canVisit(x,y): # True if the player can exist at (x,y) without being inside scenery
    global blocks
    if(x<0 or y<0): return False
    sgx = x/BS
    egx = (x+BS-1)/BS
    sgy = y/BS
    egy = (y+BS*2-1)/BS
    for gx in range(sgx,egx+1):
        for gy in range(sgy,egy+1):
            if(blocks[gy][gx] >0): 
                return False
    return True
    
grounded = False
vel = 0
while 1:
    clock.tick(25)
    screen.blit(background, (0, 0))
    for y in range(py/BS-6,py/BS+10):
        for x in range(px/BS-10,px/BS+11):
            if(x<0 or x>=GSX or y<0 or y>=GSX):
                pygame.draw.rect(screen, (0,0,255), (x*BS-px+10*BS,y*BS-py+6*BS,BS,BS))
            elif(blocks[y][x]==1):
                pygame.draw.rect(screen, (255,255,255), (x*BS-px+10*BS,y*BS-py+6*BS,BS,BS))

    #Draw player
    pygame.draw.rect(screen, (255,0,0), (10*BS,6*BS,BS,BS*2))

    pygame.display.flip()

    key = pygame.key.get_pressed()

    # Left/right movement
    if key[K_x] and canVisit(px+4,py): px+=4
    elif key[K_z] and canVisit(px-4,py): px-=4

    # Jumping
    if key[K_UP] and canVisit(px,py-1) and grounded: 
        vel = -8
        grounded = False


    # Deal with gravity and vertical movement
    if(vel<0):
        for i in range(0,vel,-1):
            if(canVisit(px,py-1)):
                py -=1
            else:
                vel = 0
        vel += 1
    elif(vel>=0):
        for i in range(0,max(vel,1)):
            if(canVisit(px,py+1)):
                py += 1
                grounded = False
            else:
                if(vel>1): print "Landing velocity "+str(vel)
                vel = 0
                grounded = True
        vel += 1

    for event in pygame.event.get():
        if event.type == QUIT:
            exit(0)
        elif event.type == KEYDOWN and event.key == K_ESCAPE:
            exit(0)
        elif event.type == KEYDOWN and event.key == K_q:
            exit(0)


