# Object Collector 2D, platform game example by Jim MacArthur                  

import pygame
from pygame.locals import *

pygame.init()
screenwidth = 320
screen = pygame.display.set_mode((screenwidth,256))
pygame.display.set_caption('Object collector 2D')
clock = pygame.time.Clock()

BS = 16 # Block size (in pixels)
GSY= 16 # Grid size (in blocks)
GSX= 32

def makegrid(x,y,default=0):
    v = [0]*y
    for i in range(0,y):
        v[i] = [default]*x
    return v

blocks = makegrid(GSX,GSY)
frame = makegrid(GSX,GSY)
maxFrame = makegrid(GSX,GSY)
startx = 0
starty = 0              

class Golem(object): # This is the standard enemy
    def __init__(self,x,y):
        self.x = x
        self.y = y 
        self.w = 16
        self.h = 32
        self.left = False
        self.frame = 0
    def animate(self):
        global blocks
        self.x += -1 if self.left else 1
        if(blocks[self.y/BS][self.x/BS]==8): self.left = not self.left
        self.frame = (self.frame+1)%2
    def overlaps(self,x,y,w,h):
        tolerance = -3
        if(x > self.x + self.w + tolerance): return False
        if(x + w + tolerance < self.x): return False
        if(y > self.y + self.h + tolerance): return False
        if(y + h + tolerance < self.y): return False
        return True

def loadLevel(filename): # Loads a level from a text file into blocks etc
    global blocks, startx, starty,toCollect
    fp = open(filename,'r')
    y = 0
    l = fp.readline()
    toCollect = 0
    while(l != '' and y<GSY):
        for x in range(0,min(GSX,len(l))):
            if(l[x] == 'v'):
                blocks[y][x] = 0
                startx =x
                starty =y
            if(l[x] == 'g'):
                blocks[y][x] = 0
                actives.append(Golem(x*BS,y*BS))
            elif(symbolToNumber.has_key(l[x])):
                blocks[y][x] = symbolToNumber[l[x]]
            else:
                blocks[y][x] = 0
            if(l[x] == 'o'):
                toCollect += 1
        l = fp.readline()
        y+=1

def touchingBlocks(x,y): # List of blocks a player at x,y touches
    sgx = x/BS
    egx = (x+BS-1)/BS
    sgy = y/BS
    egy = (y+BS*2-1)/BS
    b = []
    for gx in range(sgx,egx+1):
        for gy in range(sgy,egy+1):
            b.append((gx,gy))
    return b

def canEnter(x,y): # True if the player can exist at (x,y) without being inside scenery
    global blocks
    if(x<0 or y<0): return False
    for (gx,gy) in touchingBlocks(x,y):
        if(blocks[gy][gx]==1): 
            return False
    return True

def isDeadly(x,y):
    global blocks
    if(x<0 or y<0): return False
    for (gx,gy) in touchingBlocks(x,y):
        if(deadly[blocks[gy][gx]]): 
            return True
    for a in actives:
        if(a.overlaps(x,y,16,32)):
            return True
    return False

def checkCollect(x,y):
    global blocks, collections
    if(x<0 or y<0): return False
    for (gx,gy) in touchingBlocks(x,y):
        if(blocks[gy][gx] == symbolToNumber['o']):
            blocks[gy][gx] = 0
            collections += 1

def checkExit(x,y):
    global blocks, collections, level
    if(x<0 or y<0): return False
    for (gx,gy) in touchingBlocks(x,y):
        if(blocks[gy][gx] == symbolToNumber['e']):
            if(collections >= toCollect):
                level += 1
                perLifeInit()

def canDrop(x,y): # Like isSolid, but only checks if we can drop into a space (many platform blocks can be entered but not dropped through)
    global blocks
    if(x<0 or y<0): return False
    if(y%BS != 0): return True
    sgx = x/BS
    egx = (x+BS-1)/BS
    egy = (y+1+BS*2-1)/BS
    gy = egy
    for gx in range(sgx,egx+1):
        if(solid[blocks[gy][gx]]): 
            return False
    return True

def loadTransparent(filename):
    i = pygame.image.load(filename)
    i.set_colorkey((0,0,0))
    return i

def loadSpriteSet(name):
    try:
        s = 0
        spriteArray = []
        while True:
            spriteArray.append(loadTransparent("%s%d.png"%(name,s)))
            s+=1
    except pygame.error:
        if(len(spriteArray)>0):
            return spriteArray
    return None

def drawBlock(blockNo, x, y):
    if(spritesByNumber[blockNo] is not None):
        spriteData = spritesByNumber[blockNo]
        if(type(spriteData) is list):
            screen.blit(spriteData[frame[y][x]], (x*BS-px+10*BS,y*BS-py+6*BS))
            if blockNo == symbolToNumber['>']:
                frame[y][x] = (frame[y][x]+1) % (getMaxFrame('>')+1)
        else:
            screen.blit(spriteData, (x*BS-px+10*BS,y*BS-py+6*BS))

def standingEffects():
    # Degenerate platforms etc
    global px,py
    opy = py+32
    sgx = px/BS
    egx = (px+BS-1)/BS
    gy = opy/BS
    for x in range(sgx,egx+1):
        if blocks[gy][x] == symbolToNumber['~']:
            frame[gy][x] += 1
            if frame[gy][x] > getMaxFrame('~'):
                frame[gy][x] = 0
                blocks[gy][x] = 0
        elif blocks[gy][x] == symbolToNumber['>']:
            if canEnter(px+1,py):
                px += 1

# Per-life initialization things
def perLifeInit():
    global grounded, vel, walkframe, left, dx, px, py, collections, actives, frame, level
    actives = []
    frame = makegrid(GSX,GSY)
    loadLevel("level%d.txt"%level)
    grounded = False
    vel = 0
    walkframe = 0
    left = False
    dx = 0
    px = startx*BS
    py = starty*BS
    collections = 0

# Per-game initialization
def perGameInit():
    global lives, level, flash
    flash = 0
    level = 1
    lives = 3

def drawBlocks():
    for y in range(py/BS-6,py/BS+10):
        for x in range(px/BS-10,px/BS+11):
            if(x<0 or x>=GSX or y<0 or y>=GSY):
                pygame.draw.rect(screen, (0,0,255), (x*BS-px+10*BS,y*BS-py+6*BS,BS,BS))
            else:
                drawBlock(blocks[y][x],x,y)


def drawActives():
    for a in actives:
        a.animate()
        sprite = monsterSprite[a.frame]
        screen.blit(pygame.transform.flip(sprite,a.left,False), (a.x-px+10*BS,a.y-py+6*BS,BS,2*BS))
        
    #Draw player
    screen.blit(pygame.transform.flip(playerSprites[walkframe%4],left,False),(10*BS,6*BS))

def processUserInput():
    global px, py, dx, left, walkframe, vel, grounded
    key = pygame.key.get_pressed()

    # Left/right movement
    if grounded:
        if key[K_RIGHT] and canEnter(px+4,py): 
            px+=4
            walkframe += 1
            dx = 1
            left = False
        elif key[K_LEFT] and canEnter(px-4,py):
            px-=4
            walkframe += 1
            dx = -1
            left = True
        else:
            walkframe = 0
            dx = 0
    else:
        if canEnter(px+dx*4,py):
            px += dx*4

    # Jumping
    if key[K_UP] and canEnter(px,py-1) and grounded: 
        vel = -8
        grounded = False

def processGravity():
    global vel, py, grounded
    dead = False
    if(vel<0):
        for i in range(0,vel,-1):
            # Check whether we hit our head on something
            if(canEnter(px,py-1)):
                py -=1
            else:
                vel = 0
        vel += 1
    elif(vel>=0):
        for i in range(0,max(vel,1)):
            if(canDrop(px,py)):
                py += 1
                grounded = False
            else:
                # Landed
                if(vel>12): dead = True
                standingEffects()
                vel = 0
                grounded = True
                break
        vel += 1
    return dead

def displayPlayScreen():
    global flash
    if(flash):
        screen.fill((255,0,0))
        flash -= 1
    else:
        screen.fill((0,0,0))
    drawBlocks()
    drawActives()

    # Draw remaining lives
    for i in range(0,lives):
        screen.blit(playerSprites[0],(i*BS,14*BS))

def displayGameOverScreen():
    screen.fill((0,0,0))
    text = font.render("GAME OVER", 1, (255,0,0))
    textpos = text.get_rect(centerx=screenwidth/2,y=64)
    screen.blit(text, textpos)

def displayTitleScreen():
    screen.fill((0,0,0))
    text = font.render("Object Collector 2D", 1, (255,0,0))
    textpos = text.get_rect(centerx=screenwidth/2,y=32)
    screen.blit(text, textpos)
    line = 96
    for text in ( 'Use arrow keys:', 'left and right to walk',
                  'up to jump','Press Space to start'):
        text = font.render(text, 1, (255,0,0))
        textpos = text.get_rect(centerx=screenwidth/2,y=line)
        line += 32
        screen.blit(text, textpos)


def getMaxFrame(sym):
    global maxFrame
    n = symbolToNumber[sym]
    return maxFrame[n]

def checkDead(deadFlag):
    global flash, lives, state
    if(deadFlag or isDeadly(px,py)):
        lives -= 1
        if(lives < 0):
            state = GAMEOVER
            perGameInit()
        perLifeInit()
        flash = 2

font = pygame.font.Font(None, 36)
symbolToNumber = { '#':1, '=':2, '~':3, '>':4, 't':5, ',': 6, 'o': 7,
                   '|': 8, 'e':9}
blockSpriteMap = { '=':'ledge', '#':'wall', '~':'breakingledge', '>':'convey',
                   't':'tree', ',':'stalactite', 'o':'key',
                   '|':None, 'e':'exit'}

spritesByNumber = [ None ] *10
solid = [ 0 ] * 10

for i in "=#~>":
    solid [ symbolToNumber[i] ] = 1
deadly = [ 0 ] * 10
for i in "t,":
    deadly [ symbolToNumber[i] ] = 1

for k,v in blockSpriteMap.iteritems():
    n = symbolToNumber[k]
    try:
        spritesByNumber[n] = loadTransparent("%s.png"%v)
    except pygame.error:
        spriteSet = loadSpriteSet(v)
        spritesByNumber[n] = spriteSet
        if(spriteSet is not None):
            maxFrame[n] = len(spriteSet)-1

playerSprites = loadSpriteSet("player")
monsterSprite = loadSpriteSet("monster")

# Constants for game state
TITLE=0
PLAYING=1
GAMEOVER=2

state = TITLE
flash = 0
gameOverTimeout = 32    

while 1:
    clock.tick(25)

    if state==PLAYING:
        displayPlayScreen()
        pygame.display.flip()
        processUserInput()
        dead = processGravity()
        checkCollect(px,py)
        checkExit(px,py)
        checkDead(dead)

    elif state == GAMEOVER:
        displayGameOverScreen()
        gameOverTimeout -= 1
        if(gameOverTimeout < 0):
            gameOverTimeout = 32
            state = TITLE
        pygame.display.flip()

    elif state == TITLE:
        displayTitleScreen()
        pygame.display.flip()

    for event in pygame.event.get():
        if event.type == QUIT:
            exit(0)
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE or event.key == K_q:
                exit(0)
            elif event.key == K_SPACE and state==TITLE:
                state = PLAYING
                perGameInit()
                perLifeInit()
