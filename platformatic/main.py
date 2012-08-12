# Platformatic, puzzle platform game example by Jim MacArthur                  

import pygame
from pygame.locals import *
import levels
from spritenames import spriteNames
import copy

screenwidth = 1280

def init1():
    global screen, clock, background, black, titleScreen
    pygame.init()
    #pygame.font.init()
    screen = pygame.display.set_mode((screenwidth,480))
    pygame.display.set_caption('Platformatic')
    clock = pygame.time.Clock()
# Background is only used during the game over screen
    background = pygame.surface.Surface((screenwidth,256))
# Black is used to fade the background for the game over screen
    black = background.copy()
    black.fill((16,16,16))
    titleScreen = pygame.image.load("titlescreen.png")
    

delay = 0
toCollect = 0

NONE = 0
RIGHT = 1
LEFT = 2

plan = NONE
BS = 32 # Block size (in pixels)
speed = (BS/4)
GSY= 50 # Grid size (in blocks)
GSX= 50
zoom = False
started = False
startx = 3
starty = 6              


def makegrid(x,y,default=0):
    v = [0]*y
    for i in range(0,y):
        v[i] = [default]*x
    return v

def initGrids():
    global blocks, behaviour, frame, maxFrame
    blocks = makegrid(GSX,GSY)
    behaviour = makegrid(GSX,GSY)
    frame = makegrid(GSX,GSY)
    maxFrame = makegrid(GSX,GSY)


def spriteNumber(name):
    for (k,v) in  spriteNames.iteritems():
        if(v==name):
            return k
    return 9999

class Golem(object): # This is the standard enemy
    def __init__(self,x,y):
        self.x = x
        self.y = y 
        self.w = BS
        self.h = BS*2
        self.left = False
        self.frame = 0
    def animate(self):
        global blocks
        self.x += -1 if self.left else 1
        if(behaviour[self.y/BS][self.x/BS]==spriteNumber("reflector")):
            self.left = not self.left
        self.frame = (self.frame+1)%2
    def overlaps(self,x,y,w,h):
        tolerance = -3
        if(x > self.x + self.w + tolerance): return False
        if(x + w + tolerance < self.x): return False
        if(y > self.y + self.h + tolerance): return False
        if(y + h + tolerance < self.y): return False
        return True

class GolemVert(Golem): # Vertical-moving version
    def animate(self):
        global blocks
        self.y += -1 if self.left else 1
        if(behaviour[self.y/BS][self.x/BS]==spriteNumber("reflector")):
            self.left = not self.left
        self.frame = (self.frame+1)%2

levelphysicals = [ None, levels.level1Physical, levels.level2Physical, levels.level3Physical, levels.level4Physical] 
levelbehaviours = [ None, levels.level1Behaviour, levels.level2Behaviour, levels.level3Behaviour, levels.level4Behaviour ] 
        

def loadLevel(levelno): # Loads a level from a text file into blocks etc
    global blocks, startx, starty, behaviour, toCollect
    blocks = copy.deepcopy(levelphysicals[levelno])
    toCollect  = 0
    # Now process for special blocks
    for y in range(0,GSY):
        for x in range(0,GSX):
            if(blocks[y][x] == spriteNumber("player")):
                blocks[y][x] = 0
                startx = x
                starty = y
                print "Found starting position in level: %d,%d"%(startx,starty)
            elif(blocks[y][x] == spriteNumber("updownmonster")):
                g = GolemVert(x*BS,y*BS)
                actives.append(g)
                blocks[y][x] = 0
            elif(blocks[y][x] == spriteNumber("leftrightmonster")):
                g = Golem(x*BS,y*BS)
                actives.append(g)
                blocks[y][x] = 0
            elif(blocks[y][x] == spriteNumber("key")):
                toCollect += 1
    behaviour = levelbehaviours[levelno]

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
        if(flags[blocks[gy][gx]] & SOLID): 
            return False
    return True

def isDeadly(x,y):
    global blocks
    if(x<0 or y<0): return False
    for (gx,gy) in touchingBlocks(x,y):
        if(flags[blocks[gy][gx]] & DEADLY): 
            return True
    for a in actives:
        if(a.overlaps(x,y,BS,BS*2)):
            return True
    return False

def checkCollect(x,y):
    global blocks, collections
    if(x<0 or y<0): return False
    for (gx,gy) in touchingBlocks(x,y):
        if(blocks[gy][gx] == spriteNumber("key")): # TODO
            blocks[gy][gx] = 0
            collections += 1

def nextLevel():
    global level, directions, state
    level += 1
    if(level>4): level=1
    perLifeInit()
    directions = makegrid(GSX,GSY)
    state = WINPAGE


def checkExit(x,y):
    global blocks, collections
    if(x<0 or y<0): return False
    for (gx,gy) in touchingBlocks(x,y):
        if(blocks[gy][gx] == spriteNumber("exit")):
            if(collections >= toCollect):
                nextLevel()


def canDrop(x,y): # Like canEnter, but only checks if we can drop into a space (many platform blocks can be entered but not dropped through)
    global blocks
    if(x<0 or y<0): return False
    if(y%BS != 0): return True
    sgx = x/BS
    egx = (x+BS-1)/BS
    egy = (y+1+BS*2-1)/BS
    gy = egy
    for gx in range(sgx,egx+1):
        if(flags[blocks[gy][gx]] & SUPPORTING): 
            return False
    return True

def loadTransparent(filename):
    i = pygame.image.load("tiles/"+filename)
    i.set_colorkey((0,0,0))
    return i

def loadSpriteSet(name):
    try:
        s = 0
        spriteArray = []
        while True:
            spriteArray.append(loadTransparent("../sprites/%s%d.png"%(name,s)))
            s+=1
    except pygame.error:
        print "[loadSpriteSet] Not found: ../sprites/%s%d.png"%(name,s)
        if(len(spriteArray)>0):
            print "End of sprite set"
            return spriteArray
    print "Warning: No sprite set found for %s"%(name)
    return None

def loadTileSet(name):
    print "Loading sprite set for %s"%name
    try:
        s = 0
        spriteArray = []
        while True:
            spriteArray.append(loadTransparent("%s%d.png"%(name,s)))
            s+=1
    except pygame.error:
        print "Not found: %s.png"%name
        if(len(spriteArray)>0):
            print "Loaded set %s, with %d frames"%(name, len(spriteArray))
            return spriteArray
    print "Warning: No sprite set found for %s"%(name)
    return None


def loadSprite(filename):
    i = pygame.image.load("sprites/"+filename+".png")
    i.set_colorkey((0,0,0))
    return i

def drawBlock(blockNo, x, y):
    global zoom

    bs = BS
    if(zoom): bs = BS/2
    offsetx = 10*BS
    if(spritesByNumber[blockNo] is not None):
        spriteData = spritesByNumber[blockNo]
        if(type(spriteData) is list):
            sprite = spriteData[frame[y][x]];
            screen.blit(sprite, (x*bs-px+10*BS,y*bs-py+6*BS))
            if blockNo == spriteNumber("conveyor"):
                frame[y][x] = (frame[y][x]+1) % (getMaxFrame(spriteNumber("conveyor"))+1)
            if blockNo == spriteNumber("conveyRight"):
                frame[y][x] = (frame[y][x]-1) % (spriteNumber("conveyor")+1)
        else:
            sprite = spriteData
            if(zoom):
                sprite = pygame.transform.scale(sprite,(16,16))
            screen.blit(sprite, (x*bs-px+10*bs,y*bs-py+6*bs))
    else:
        #print "Caution: No sprite for blockNo %d"%blockNo
        pass

def standingEffects():
    # Degenerate platforms etc
    global px,py
    opy = py+(BS*2)
    sgx = px/BS
    egx = (px+BS-1)/BS
    gy = opy/BS
    for x in range(sgx,egx+1):
        if blocks[gy][x] == spriteNumber("breakingledge"):
            frame[gy][x] += 1
            if frame[gy][x] > getMaxFrame(spriteNumber("breakingledge")):
                frame[gy][x] = 0
                blocks[gy][x] = 0
        elif blocks[gy][x] == spriteNumber("conveyor"):
            if canEnter(px+1,py):
                px += 1
        elif blocks[gy][x] == spriteNumber("conveyorr"):
            if canEnter(px-1,py):
                px -= 1

# Per-life initialization things
def perLifeInit():
    global grounded, vel, walkframe, left, dx, px, py, collections, actives, frame, level, directions,plan, started,delay
    actives = []
    frame = makegrid(GSX,GSY)
    loadLevel(level)
    grounded = False
    vel = 0
    walkframe = 0
    left = False
    dx = 0
    px = startx*BS
    py = starty*BS
    print "Level %d: starting position is (%d,%d)\n"%(level,startx,starty)
    collections = 0
    plan = NONE
    started = False
    delay = 0

# Per-game initialization
def perGameInit():
    global lives, level, flash, directions
    flash = 0
    level = 1
    lives = 100
    directions = makegrid(GSX,GSY)


def drawBlocks():
    global zoom
    bs = BS
    if(zoom): bs = BS/2
    for y in range(py/bs-6,py/bs+20):
        for x in range(px/bs-10,px/bs+31):
            if(x<0 or x>=GSX or y<0 or y>=GSY):
                pygame.draw.rect(screen, (0,0,255), (x*bs-px+10*BS,y*bs-py+6*BS,bs,bs))
            else:
                drawBlock(blocks[y][x],x,y)
                if(directions[y][x]>0):
                    d = directions[y][x]
                    if(commandSprites[d] is None):
                        pygame.draw.rect(screen, (255*(d & 1),255*((d >> 1) & 1),255*((d>>2)&1)), (x*bs-px+10*bs,y*bs-py+6*bs,bs,bs))
                    else:
                        if(zoom):
                            blockSprite = pygame.transform.scale(commandSprites[d],(16,16))
                        else:
                            blockSprite = commandSprites[d]
                        screen.blit(blockSprite, (x*bs-px+10*BS,y*bs-py+6*BS))

                    


def drawActives():
    for a in actives:
        if(state==RUNNING): a.animate()
        sprite = monsterSprite[a.frame]
        screen.blit(pygame.transform.flip(sprite,a.left,False), (a.x-px+10*BS,a.y-py+6*BS,BS,2*BS))
        
    #Draw player
    playerSprite = playerSprites[walkframe%4]
    if(state==RUNNING):
        screen.blit(pygame.transform.flip(playerSprite,left,False),(10*BS,6*BS))
    else:
        screen.blit(pygame.transform.flip(playerSprite,left,False), (startx*BS-px+10*BS,starty*BS-py+6*BS,BS,2*BS))


def processUserInput():
    global px, py, dx, left, walkframe, vel, grounded, plan, started, delay, zoom
    key = pygame.key.get_pressed()
    zoom = key[K_z]

    if(delay>0):
        delay -=1 
        return

    if key[K_RETURN]:
        plan = RIGHT
        started = True
    # Left/right movement
    if grounded:
        if plan==RIGHT and canEnter(px+4,py): 
            px+=speed
            walkframe += 1
            dx = 1
            left = False
        elif plan==LEFT and canEnter(px-4,py):
            px-=speed
            walkframe += 1
            dx = -1
            left = True
        else:
            walkframe = 0
            dx = 0
    else:
        if canEnter(px+dx*speed,py):
            px += dx*speed

    if(grounded):
        order = directions[(py+64)/BS][(px+16)/BS]
    else:
        order = 0
    if(order == 1):
        plan = LEFT
    elif(order == 2):
        plan = RIGHT
    elif(order == 4): # Hourglass
        delay = 8

    if (order == 3) and canEnter(px,py-1) and grounded: 
        vel = -16
        grounded = False

def placeTile(tileno, pos):
    (x,y) = pos
    print "Original click at %d,%d\n"%(x,y)
    x += px-10*BS
    y += py-6*BS
    x /= BS
    y /= BS
    print "Placing tile %d at position %d,%d"%(tileno,x,y)
    directions[y][x] = tileno
   

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
        vel += 2
    elif(vel>=0):
        for i in range(0,max(vel,1)):
            if(canDrop(px,py)):
                py += 1
                grounded = False
            else:
                # Landed
                if(vel>24): dead = True
                standingEffects()
                vel = 0
                grounded = True
                break
        vel += 1
    return dead

def displayPlayScreen():
    global flash, state
    if(flash):
        screen.fill((255,0,0))
        flash -= 1
    else:
        screen.fill((0,0,0))
    drawBlocks()
    drawActives()
    
    # Drawing sidebar
    screen.fill((0,0,127),(screenwidth-80,0,80,512))
    startcommand = 0
    if(state == RUNNING):
        startcommand = 5
    for i in range(startcommand,7):
        if(commandSprites[i] is None):
            pygame.draw.rect(screen, (255,0,255), (screenwidth-80+8,8+40*i,32,32))
        else:
            screen.blit(commandSprites[i], (screenwidth-80+8,8+40*i))
    # Highlight current action
    if(state == PLACING):
        pygame.draw.rect(screen, (255,255,255), (screenwidth-80+4,4+40*action,40,40),1)

    # Draw remaining lives
    for i in range(0,lives):
        screen.blit(playerSprites[0],(i*BS,20*BS))

def displayGameOverScreen():
    background.blit(black, (0,0), None, BLEND_SUB)
    screen.blit(background,(0,0))
    #text = font.render("GAME OVER", 1, (255,0,0))
    textpos = text.get_rect(centerx=screenwidth/2,y=64)
    screen.blit(text, textpos)

def displayWinScreen():
    global cycles
    background.blit(black, (0,0), None, BLEND_SUB)
    screen.blit(background,(0,0))
    #text = font.render("LEVEL COMPLETED", 1, (255,0,0))
    textpos = text.get_rect(centerx=screenwidth/2,y=64)
    screen.blit(text, textpos)
    #text = font.render("%d cycles"%cycles, 1, (255,0,0))
    textpos = text.get_rect(centerx=screenwidth/2,y=96)
    screen.blit(text, textpos)


def displayTitleScreen():
    screen.blit(titleScreen, (0,0))


def getMaxFrame(sym):
    global maxFrame
    return maxFrame[sym]

def checkDead(deadFlag):
    global flash, lives, state, background
    if(deadFlag or isDeadly(px,py)):
        lives -= 1
        if(lives < 0):
            state = GAMEOVER
            perGameInit()
            background.blit(screen, (0,0))
        perLifeInit()
        flash = 2
    
def initCommandSprites():
    global commandSprites
    i = 0 
    for c in commands:
        if(c is not None):
            commandSprites[ i ] = loadTransparent(c+".png")
        i += 1

SOLID = 1 ; DEADLY = 2 ; SUPPORTING = 4

def init2():
    global font, blockSpriteMap, commands, commandSprites, spritesByNumber, flags
    global maxFrame
    #font = pygame.font.Font(pygame.font.match_font("Arial"), 36)
    blockSpriteMap = spriteNames
    commands = [ "eraser", "goleft", "goright", "jump", "hourglass", "go", "stop" ]
    commandSprites = [ None ] * 12
    initCommandSprites()
    spritesByNumber = [ None ] *20
    flags = [ 0 ] * 20

    flags [ 1 ] = 0
    for i in range(2,10):
        flags [ i ] = SUPPORTING | SOLID
        flags[spriteNumber("exitsign")] = 0
        flags[spriteNumber("exit")] = 0
        flags[spriteNumber("breakingledge")] = SUPPORTING
        flags[spriteNumber("conveyor")] = SUPPORTING
        flags[spriteNumber("shittytree")] = DEADLY
    for k,v in blockSpriteMap.iteritems():
        try:
            spritesByNumber[k] = loadTransparent("%s.png"%v)
            print "Loading sprite %d: %s\n"%(k,v)
        except pygame.error:
            print "Not found: %s.png"%v
            spriteSet = loadTileSet(v)
            spritesByNumber[k] = spriteSet
            if(spriteSet is not None):
                maxFrame[k] = len(spriteSet)-1
    print "Finished init2"

def init3():
    global playerSprites, monsterSprite
    playerSprites = loadSpriteSet("player")
    monsterSprite = loadSpriteSet("monster")
    print "Finished init3"

# Constants for game state
TITLE=0
PLACING=1
RUNNING=2
PLAYING=2 # Deprecated
GAMEOVER=3
WINPAGE = 4

state = TITLE
flash = 0
gameOverTimeout = 32    

action = 0
drag = False
(dragx,dragy) = (0,0)

def mainLoop():    
    global state, dead, action, px, py, drag, gameOverTimeout, cycles, level
    init1()
    initGrids()
    init2()
    print "Init 2 completed. state=%d"%state
    init3()
    print "All init completed. state=%d"%state

    while True:
        clock.tick(25)
        
        if state==RUNNING or state==PLACING:
            processUserInput()
            displayPlayScreen()
            pygame.display.flip()

        if state==RUNNING:
            cycles += 1
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

        elif state == WINPAGE:
            displayWinScreen()
            gameOverTimeout -= 1
            if(gameOverTimeout < 0):
                gameOverTimeout = 32
                state = PLACING
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
                elif event.key == K_p: # Cheat code, skips all collections
                    collections = 100
                if state==TITLE and event.key == K_3:
                    state = PLACING
                    perGameInit()
                    level = 3
                    perLifeInit()
                if state==TITLE and event.key == K_4:
                    state = PLACING
                    perGameInit()
                    level = 4
                    perLifeInit()
                if state==PLAYING and event.key == K_s:
                    nextLevel()

            elif event.type == MOUSEBUTTONDOWN:
                print "Verify event = click"

                if state==TITLE:
                    state = PLACING
                    perGameInit()
                    perLifeInit()
                else:
                    (x,y) = event.pos
                    (dragx,dragy) = (x,y)
                    if(x>screenwidth-80): 
                        icon = (y-8)/40
                        if(icon == 5):
                            print "Switching to state RUNNING"
                            px = startx*BS
                            py = starty*BS
                            cycles = 0
                            state = RUNNING
                        elif(icon == 6):
                            # Reset. How
                            print "Switching to state PLACING"
                            state = PLACING
                            perLifeInit()
                        elif(icon == 7):
                            # Reset. How
                            print "Switching to state PLACING"
                            state = TITLE
                        elif state==PLACING:
                            action = icon
            elif event.type == MOUSEBUTTONUP:
                (x,y) = event.pos
                if(x<screenwidth-80 and not drag): 
                    if(state == PLACING ):
                        placeTile(action, event.pos)
                drag = False
            elif event.type == MOUSEMOTION and state==PLACING:
                (left,middle,right) = event.buttons
                (x,y) = event.pos
                if(left):
                    if(abs(x-dragx) > 32 or abs(y-dragy)>32 or drag):
                        drag = True
                        px -= (x-dragx)
                        py -= (y-dragy)
                        (dragx,dragy)=(x,y)

def main():
    mainLoop()

# This isn't run on Android.
if __name__ == "__main__":
    main()
