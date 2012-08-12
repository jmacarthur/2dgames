import pygame
from pygame.locals import *
import math
import random
import copy
import levels
from blocktypes import blocktypes

def loadTransparent(filename):
    i = pygame.image.load(filename)
    i.set_colorkey((0,0,0))
    return i

try:
    import pygame.mixer as mixer
except ImportError:
    import android_mixer as mixer

# Declare lots of global variables
background = None
shipSprite = None
numbers = None
blockSprites = []
startSpeed = 16 
GSX = 100 # Size of meteor, in blocks
GSY = 100
rotspeed = 4
speed = startSpeed

bulletspeed = 1000
originalGravity = 3
gravity = originalGravity

# Types of originator for bullets
PLAYER=0
TURRET=1

bullets = []
bulletTimeout = 0
particles = []
deadTimeout = 0
fieldOn = False
field = 0
pickUpTarget = (0,0)
pickUpTimeout = 100

mass = 0 # Picked up this session
totalmass = 0 # Picked up in total this game

t = 0 # Used in FPS calculation
cycle = 0
fpsDisplay = None
screen = None

# Game state
PLAYING = 0
DEAD = 1
WON = 2
TITLEPAGE = 3
FINISHEDGAME = 4

timers = []

ssx=0 # Coords the static scene was drawn for
ssy=0

shipPolygon = [ (64,32), (0,64), (8,48), (0,32), (8,16), (0,0), (64,32) ]

class Timer(object):
    pass

class FixGeneratorEvent(Timer):
    def __init__(self, time, x,y):
        self.x = x
        self.y = y
        self.time = time
    def activate(self):
        global timers
        reactivateGenerator(self.x,self.y)

class NearlyFixGeneratorEvent(Timer):
    def __init__(self, time, x,y):
        self.x = x
        self.y = y
        self.time = time
    def activate(self):
        global timers
        timers.append(FixGeneratorEvent(100,self.x,self.y))
        effectChannel.play(generator)

class Bullet(object):
    def __init__(self,xpos,ypos,angle,xvel,yvel,outset):
        self.xvel = bulletspeed*math.cos(math.radians(angle))
        self.yvel = bulletspeed*math.sin(math.radians(angle))
        self.xpos = xpos + outset*math.cos(math.radians(angle)) * 128
        self.ypos = ypos + outset*math.sin(math.radians(angle)) * 128
        self.xvel += xvel
        self.yvel += yvel
        self.ttl = 100
        self.origin = PLAYER
    def advance(self):
        self.xpos += self.xvel
        self.ypos += self.yvel
        self.ttl -= 1

class Particle(object):
    def __init__(self,xpos,ypos,angle,xvel,yvel,vel=50,outset=100,ttl=10):
        self.xvel = vel*math.cos(math.radians(angle))
        self.yvel = vel*math.sin(math.radians(angle))
        self.xpos = xpos + outset*math.cos(math.radians(angle))*128
        self.ypos = ypos + outset*math.sin(math.radians(angle))*128
        self.xvel += xvel
        self.yvel += yvel
        self.ttl = ttl
        self.origttl = ttl
        self.red =1
        self.green = 0
        self.blue = 0
    def advance(self):
        self.xpos += self.xvel
        self.ypos += self.yvel
        self.ttl -= 1
    def setColour(self, (r,g,b)):
        self.red = 1 if r>0 else 0
        self.green = 1 if g>0 else 0
        self.blue = 1 if b>0 else 0
    def col(self):
        return (self.red*(127+127*self.ttl/self.origttl),
                self.green*(127+127*self.ttl/self.origttl),
                self.blue*(127+127*self.ttl/self.origttl))


class Ship(object):
    def __init__(self):
        self.reset()
    def reset(self):
        self.xpos = 128*128
        self.ypos = 128*128
        self.xvel = 0
        self.yvel = 0
        self.angle = -90


def makegrid(x,y,default=0):
    v = [0]*y
    for i in range(0,y):
        v[i] = [default]*x
    return v

def init1():
    pass

def blockRange(x,y):
    global ship
    dx = (ship.xpos/128 - x*32)
    dy = (ship.ypos/128 - y*32)
    return (dx*dx + dy*dy)

# Load Level
def loadLevel(levelNo):
    global blocks

    levelArray = [levels.level1Physical, levels.level2Physical, levels.level3Physical]

    blocks = copy.deepcopy(levelArray[levelNo-1])
    for y in range(0,GSY):
        for x in range(0,GSX):
            blocks[y][x] -= 1

    for y in range(0,GSY):
        for x in range(0,GSX):
            if(blocks[y][x] == 13): # Top pylon
                sparky = y+1
                while(blocks[sparky][x] == 0 and sparky < (GSY-1)):
                    blocks[sparky][x] = 16
                    sparky+=1

def isStatic(x):
    if(x==0): return False
    if(x<6 or (x>=9 and x<=12)): return True
    return False

def regenStaticScene():
    global ship
    xstart = int((ship.xpos/128)/32)
    ystart = int((ship.ypos/128)/32)
    staticScene.fill((0,0,0))
    xo = 10
    yo = 8
    for y in range(0,17):
        for x in range(0,21):
            if(y+ystart-yo > 0):
                bx = (x+xstart-xo)%GSX
                
                try:
                    if(isStatic(blocks[y+ystart-yo][bx])):
                        staticScene.blit(blockSprites[blocks[y+ystart-yo][bx]-1], (x*32,y*32))
                except IndexError:
                    print "Outside blocks grid - requested %d,%d"%(y+ystart-yo,bx)
    

def translate(poly, x, y):
    for i in range(0,len(poly)):
        p = poly[i]
        poly[i] = (p[0] + x, p[1] + y)

def rotate(poly, radians):
    for i in range(0,len(poly)):
        p = poly[i]
        poly[i] = (p[0] * math.cos(radians) - p[1]*math.sin(radians),
             p[0] * math.sin(radians) + p[1]*math.cos(radians))

def drawPoly(poly):
    global screen
    for i in range(0,len(poly)-1):
        pygame.draw.line(screen, (0,255,0), (poly[i][0], poly[i][1]), (poly[i+1][0],poly[i+1][1]))


def linesIntersect(s1,e1,s2,e2):
    A1 = e1[1]-s1[1]
    B1 = s1[0]-e1[0]
    C1 = A1*s1[0]+B1*s1[1]
    A2 = e2[1]-s2[1]
    B2 = s2[0]-e2[0]
    C2 = A2*s2[0]+B2*s2[1]

    determinant = A1*B2-A2*B1
    if(determinant == 0): return False

    #Determine start pos
    x = (B2*C1-B1*C2)/determinant
    y = (A1*C2-A2*C1)/determinant

    intersect = (x,y)

    box1x1 = min(s1[0],e1[0])
    box1x2 = max(s1[0],e1[0])
    box1y1 = min(s1[1],e1[1])
    box1y2 = max(s1[1],e1[1])

    box2x1 = min(s2[0],e2[0])
    box2x2 = max(s2[0],e2[0])
    box2y1 = min(s2[1],e2[1])
    box2y2 = max(s2[1],e2[1])
        
    # Check boundnig boxes actually overlap
    if(box1x2 < box2x1 or box1x1 > box2x2): return False
    if(box1y2 < box2y1 or box1y1 > box2y2): return False

    box3x1 = max(box1x1, box2x1)
    box3x2 = min(box1x2, box2x2)
    box3y1 = max(box1y1, box2y1)
    box3y2 = min(box1y2, box2y2)

    if(x>=box3x1 and y>=box3y1 and x<=box3x2 and y<=box3y2):
        return True
    return False


def getPolyForBlockType(blockType):
    if(blockType == 1 or (blockType >= 7 and blockType <= 15)):
        poly1 = [ (0,0), (32,0), (32,32),(0,32),(0,0) ]
    elif(blockType == 2):
        poly1 = [ (0,0), (32,32),(0,32),(0,0) ]
    elif(blockType == 3):
        poly1 = [ (32,0), (32,32),(0,32),(32,0) ]
    elif(blockType == 4):
        poly1 = [ (0,0), (32,0),(0,32),(0,0) ]
    elif(blockType == 5):
        poly1 = [ (0,0), (32,0),(32,32),(0,0) ]
    elif(blockType == 6):
        poly1 = None
    elif(blockType == 16):
        poly1 = [ (15,0), (16,0), (16,32),(16,32),(15,0) ]
        
    else:
        # Default to solid square
        poly1 = [ (0,0), (32,0), (32,32),(0,32),(0,0) ]
    return poly1

def particleIntersectsBlock(px,py,blockType):
    if(blockType==0): return False
    poly1 = getPolyForBlockType(blockType)
    if(poly1 is None): return False
    px = px % 32
    py = py % 32
    translate(poly1,-px,-py)
    for i in range(0,len(poly1)-1):
        d = poly1[i+1][0]*poly1[i][1] - poly1[i][0]*poly1[i+1][1]
        if(d>0): return False
    return True

def particleIntersectsShip(px,py):
    poly1 = copy.deepcopy(shipPolygon)
    translate(poly1,-32,-32)
    rotate(poly1,math.radians(ship.angle))
    translate(poly1,ship.xpos/128,ship.ypos/128)
    if(poly1 is None): return False
    translate(poly1,-px,-py)
    for i in range(0,len(poly1)-1):
        d = poly1[i+1][0]*poly1[i][1] - poly1[i][0]*poly1[i+1][1]
        if(d>0): return False
    return True

    
def shipIntersectsBlock(blockX,blockY,blockType):
    if((ship.xpos/128)-blockX < -64): return False
    if((ship.xpos/128)-blockX > 64+32): return False
    if((ship.ypos/128)-blockY < -64): return False
    if((ship.ypos/128)-blockY > 64+32): return False

    poly1 = getPolyForBlockType(blockType)
    if(poly1 is None): return False
    translate(poly1,blockX,blockY)
    poly2 = copy.deepcopy(shipPolygon)
    translate(poly2,-32,-32)
    rotate(poly2,math.radians(ship.angle))
    translate(poly2,ship.xpos/128,ship.ypos/128)
    #drawPoly(poly2)
    #drawPoly(poly1)

    for i in range(0,len(poly1)-1):
        for j in range(0,len(poly2)-1):
            if(linesIntersect(poly1[i],poly1[i+1],poly2[j],poly2[j+1])):
                return True
    return False

def restartGame():
    global ship, particles, mass, speed, gravity, turretTimeout,fuel, enginecut, thrusting, frameCounter, state
    loadLevel(level)
    ship.reset()
    particles = []
    mass = 0
    speed = startSpeed
    gravity = originalGravity
    turretTimeout =50
    fuel = 1000
    enginecut = 0
    thrusting = False
    frameCounter = 0
    state = PLAYING

def startGame():
    global lives, level, totalmass
    lives = 2
    level = 1
    totalmass = 0
    restartGame()


def calculateFPS():
    global cycle, newTime, fpsDisplay, numbers, t
    cycle += 1
    if(cycle % 250 == 0):
       newTime = pygame.time.get_ticks()
       FPS = 250000.0/(newTime-t)
       txt = "%.1f"%FPS
       print "FPS: %s"%txt
       t = newTime
       fpsDisplay.fill((255,0,0))
       for i in range(0,4):
           n = ord(txt[i]) - ord('0')
           if(txt[i] == '.'): n = 10
           fpsDisplay.blit(numbers, (i*8,0),(n*8,0,8,8))


# Initialise lots of global variables
def oneTimeInit():
    global fpsDisplay, blockSprites, shipSprite, numbers, background
    global thrust, fire, explode, thrustChannel, effectChannel, generator
    global bulletSplash, tractorSound
    global screen, font, frameCounter
    global blocks, staticScene

    blocks = makegrid(GSX,GSY)
    staticScene = pygame.surface.Surface((640+32,480+64))
    staticScene.set_colorkey((0,0,0))

    frameCounter = 0
    fpsDisplay = pygame.surface.Surface((32,8))
    blockSprites = [None]*32
    blockSprites[0] = loadTransparent("block1.png")
    for (k,v) in blocktypes.iteritems():
        if(v>0):
            blockSprites[v-1] = loadTransparent(k+".png")

    # Conversion of sprites (experimental)
    print "Bit depth of block 1: %d"%blockSprites[0].get_bitsize()


    shipSprite = loadTransparent("ship.png")
    numbers = loadTransparent("8x8numbers.png")
    background = pygame.image.load("background.png")
    mixer.init(channels=2)
    thrust= mixer.Sound("thrust.ogg")
    fire = mixer.Sound("fire.ogg")
    explode = mixer.Sound("explode.ogg")
    generator = mixer.Sound("generator.ogg")
    bulletSplash = mixer.Sound("bulletSplash.wav")
    tractorSound = mixer.Sound("tractor.wav")
    thrustChannel = mixer.Channel(0)
    effectChannel = mixer.Channel(1)
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption('Meteor Miner')
    font = pygame.font.Font(pygame.font.get_default_font(),32)

def processUserInput():
    global dead, frameCounter, enginecut, thrustChannel, thrusting
    global xpos, ypos, particles, bullets, bulletTimeout
    global field, fieldOn, fuel, pickupTarget, turretTimeout, state

    pressed = pygame.key.get_pressed()

    if state==PLAYING:
        if(pressed[pygame.K_LEFT]):
            ship.angle -= rotspeed
            if(frameCounter%4==0): particles.append(Particle(ship.xpos+4096*math.cos(math.radians(ship.angle+180)),ship.ypos+4096*math.sin(math.radians(ship.angle+180)),ship.angle+270+random.randint(-5,5),ship.xvel,ship.yvel,400,40))
        if(pressed[pygame.K_RIGHT]):
            ship.angle += rotspeed
            if(frameCounter%4==0): particles.append(Particle(ship.xpos+4096*math.cos(math.radians(ship.angle+180)),ship.ypos+4096*math.sin(math.radians(ship.angle+180)),ship.angle+90+random.randint(-5,5),ship.xvel,ship.yvel,400,40))
        if(pressed[pygame.K_UP] and fuel>0):
            if(enginecut > 0): 
                enginecut-=1
                thrustChannel.stop()
                thrusting = False

            else:
                ship.xvel += speed*math.cos(math.radians(ship.angle))
                ship.yvel += speed*math.sin(math.radians(ship.angle))
                p = Particle(ship.xpos,ship.ypos,ship.angle+180+random.randint(-25,25),ship.xvel,ship.yvel,400,40)
                particles.append(p)
                if(random.randint(0,1)==0):
                    p.setColour((255,255,0))
                fuel -= 1
                if(not thrusting):
                    thrustChannel.play(thrust,loops=-1)
                    thrusting = True
            if(fuel<100 and random.randint(0,5)==0):
                enginecut = random.randint(0,10)
        else:
            thrustChannel.stop()
            thrusting = False

        
        if(pressed[pygame.K_SPACE] and bulletTimeout <=0):
            effectChannel.play(fire)
            b = Bullet(ship.xpos,ship.ypos,ship.angle,ship.xvel,ship.yvel,40)
            b.origin=PLAYER
            bullets.append(b)
            bulletTimeout = 32
        if pressed[pygame.K_LSHIFT] and not fieldOn:
            effectChannel.play(tractorSound,loops=-1)
        fieldOn = pressed[pygame.K_LSHIFT] and fuel > 0
        if fieldOn: 
            fuel -= 1
        else: 
            pickupTimeout = 100
            pickupTarget = (0,0)
            tractorSound.stop()

        if(bulletTimeout>0):
            bulletTimeout -= 1


def drawBlocks():
    global attachedBlock, closestTarget, blocks, ship, screen
    global bullets, dead, deadTimeout, turretTimeout, state, frameCounter
    global ssx,ssy
    attachedBlock = None
    closest = 10000
    closestTarget = (0,0)
    (bx,by) = ((int(ship.xpos/128/32)), int((ship.ypos/128/32)))
    if(ssx != bx or ssy != by):
        regenStaticScene()
        ssx = bx
        ssy = by
    staticOffX = -int((ship.xpos/128)%32)
    staticOffY = -int((ship.ypos/128)%32)-16
    screen.blit(staticScene, (staticOffX,staticOffY))
    pygame.draw.circle(screen, (255,0,0), (staticOffX, staticOffY), 3)
    xstart = int(ship.xpos/128)/32 - 10
    ystart = int(ship.ypos/128)/32 - 7
    for by in range(0,16):
        for bx in range(0,21):
            x = (bx+xstart) % GSX
            y = (by+ystart)
            if(y<0): next
            blockOffX = xoffset % 32
            
            if(blocks[y][x]==blocktypes["sparkv"]): # Hardwired: sparks animate
                screen.blit(blockSprites[blocks[y][x]-1+(frameCounter/4)%2], (bx*32-blockOffX,y*32-yoffset))
            elif(blocks[y][x] >0 and not isStatic(blocks[y][x]) ): 
                screen.blit(blockSprites[blocks[y][x]-1], (bx*32-blockOffX,y*32-yoffset))

    # This isn't really drawing! Move it
    for by in range(0,16):
        y = (by+ystart)
        if(y<0): continue
        for bx in range(0,21):
            x = (bx+xstart) % GSX
            if(blocks[y][x]>0):
                if(state == PLAYING):
                    if((blocks[y][x]==6 or blocks[y][x]==8 or blocks[y][x]==blocktypes["gold"]) and blockRange(x,y)<closest):
                        closest = blockRange(x,y)
                        closestTarget = (x,y)
                    if(shipIntersectsBlock(x*32,y*32,blocks[y][x])):
                        effectChannel.play(explode)
                        state = DEAD
                        print "Collision with block at %d,%d"%(x,y)
                        thrustChannel.stop()
                        deadTimeout = 200
                        for i in range(0,50):
                            particles.append(Particle(ship.xpos,ship.ypos,random.randint(0,360),ship.xvel,ship.yvel,random.randint(100,500),0,100))

                if(blocks[y][x]==7 and blockRange(x,y)<100000 and turretTimeout<=0):
                    turretTimeout = 100
                    startx = (x*32+16)*128
                    starty = (y*32+33)*128
                    ang = 270-math.degrees(math.atan2(startx-ship.xpos, starty-ship.ypos))
                    print "Firing angle: %f"%ang
                    if(ang <170 or ang >370):
                        b = Bullet(startx,starty,ang,0,0,0)
                        b.origin=TURRET
                        bullets.append(b)

def deactiveGenerator(px,py):
    blocks[py][px] = blocktypes["brokengenerator"]
    # Find a pylon to the left and recurse down, removing sparks
    if(blocks[py][px-1] == blocktypes["pylont"]):
        dy = 1
        while(blocks[py+dy][px-1] == blocktypes["sparkv"]):
            blocks[py+dy][px-1] = blocktypes["empty"]
            dy += 1
    timers.append(NearlyFixGeneratorEvent(200,px,py))

def reactivateGenerator(px,py):
    blocks[py][px] = blocktypes["generator"]
    # Find a pylon to the left and recurse down, removing sparks
    if(blocks[py][px-1] == blocktypes["pylont"]):
        dy = 1
        while(blocks[py+dy][px-1] == blocktypes["empty"]):
            blocks[py+dy][px-1] = blocktypes["sparkv"]
            dy += 1


def drawBulletsAndParticles():
    global particles, bullets, dead, deadTimeout, state
    newBullets = []
    newParticles = []
    for b in bullets:
        pygame.draw.circle(screen, (255,255,255), (int(b.xpos/128)-xoffset, int(b.ypos/128)-yoffset),2)
        b.advance()
        px = int((b.xpos/128)/32)
        py = int((b.ypos/128)/32)
        if(px<0 or py<0 or px>=GSX or py>=GSY): b.ttl=0
        elif(particleIntersectsBlock(b.xpos/128,b.ypos/128,blocks[py][px])):
            if(blocks[py][px] == 7 and b.origin==PLAYER):
                blocks[py][px] = 0
                for i in range(0,50):
                   particles.append(Particle((px*32+16)*128,(py*32+16)*128,random.randint(0,360),0,0,random.randint(100,1000),0,8))
            if(blocks[py][px] == blocktypes["goldore"] and b.origin==PLAYER):
                blocks[py][px] = blocktypes["gold"]
                for i in range(0,20):
                    p = Particle((px*32+16)*128,(py*32+16)*128,random.randint(0,360),0,0,random.randint(200,1000),0,8)
                    p.setColour((255,255,0))
            elif(blocks[py][px] == blocktypes["generator"] and b.origin==PLAYER):
                for i in range(0,20):
                    p = Particle((px*32+16)*128,(py*32+16)*128,random.randint(0,360),0,0,random.randint(200,1000),0,8)
                    p.setColour((255,255,255))
                    particles.append(p)
                    deactiveGenerator(px,py)
            elif(b.origin==PLAYER):
                print "Bullet hit, type %d"%(blocks[py][px])
            b.ttl = 0
            effectChannel.play(bulletSplash)

        elif(state == PLAYING and particleIntersectsShip(b.xpos/128,b.ypos/128)):
            if not fieldOn:
                state = DEAD
                effectChannel.play(explode)
                thrustChannel.stop()
                deadTimeout = 200
                for i in range(0,50):
                    particles.append(Particle(ship.xpos,ship.ypos,random.randint(0,360),ship.xvel,ship.yvel,random.randint(100,500),0,100))               
            b.ttl = 0

        if(b.ttl > 0):
            newBullets.append(b)
    for b in particles:
        pygame.draw.circle(screen, b.col(), (int(b.xpos/128)-xoffset, int(b.ypos/128)-yoffset),2)
        b.advance()
        if(b.ttl > 0):
            newParticles.append(b)
    bullets = newBullets
    particles = newParticles


def drawShip():
    global field, ship
    #Display ship        
    shipYPos = 240
    if(ship.ypos < 0):
        shipYPos += int(ship.ypos/512)
    rotship = pygame.transform.rotate(shipSprite, -ship.angle)
    w = rotship.get_width()
    h = rotship.get_height()
    screen.blit(rotship, (320-w/2,shipYPos-h/2))

    # Display polygon ship
    #poly1 = copy.deepcopy(shipPolygon)
    #translate(poly1,-32,-32)
    #rotate(poly1,math.radians(angle))
    #translate(poly1,320,240)
    #drawPoly(poly1)

    if(fieldOn):
        field += 1
        pygame.draw.circle(screen, ((field%15)*12,0,0), (320,shipYPos), 40,3)
        pygame.draw.circle(screen, (((field+7)%15)*12,((field+7)%15)*12,0), (320,shipYPos), 43,3)

def drawCentredText(s,y):
    global font
    text = font.render(s, 1, (0,255,0))
    textpos = text.get_rect(centerx = 640/2,y=y)
    screen.blit(text,textpos)

def drawWinText():
    global mass
    drawCentredText("Mission Successful",128)
    if(mass==1):
        drawCentredText("Payload recovered: 1 tonne",256)
    else:
        drawCentredText("Payload recovered: %d tonnes"%mass,256)

init1()
oneTimeInit()
clock = pygame.time.Clock()
state = TITLEPAGE

def processTimerEvents():
    global timers
    newTimers = []
    for t in timers:
        t.time -= 1
        if(t.time <=0):
            t.activate()
        else:
            newTimers.append(t)
    timers = newTimers

def mainLoop():
    global state, frameCounter, gravity, xoffset, yoffset, attachedBlock, turretTimeout, mass, fuel, lives, pickupTarget, level, totalmass, ship
    global deadTimeout

    ship = Ship()

    while 1:

        # FPS Calculation section
        calculateFPS()

        clock.tick(50)
        if(state == PLAYING):
            processUserInput()


        ship.xpos += ship.xvel
        ship.ypos += ship.yvel
        ship.xpos = ship.xpos %(128*32*GSX)
        xoffset = int(ship.xpos/128)-320
        yoffset = int(ship.ypos/128)-240

        if state == PLAYING or state==WON:
            ship.yvel += gravity


        if(state == PLAYING or state == WON or state==DEAD):
            if(state==DEAD and deadTimeout == 199):
                screen.fill((255,255,0))
            else:
                screen.fill((0,0,0))
                screen.blit(background,(0,100-ship.ypos/256))
                screen.blit(fpsDisplay,(640-33,0))
            drawBlocks()

        else:
            screen.fill((0,0,0))

        if(state == TITLEPAGE):
            drawCentredText("METEOR MINER",128)
            drawCentredText("Left, Right arrows to rotate",128+64)
            drawCentredText("Up arrow to thrust",128+96)
            drawCentredText("Left Shift: Shields/Tractor beam",128+128)
            drawCentredText("Press any key to start",128+128+64)

        if(state == FINISHEDGAME):
            drawCentredText("Congratulations",128)
            drawCentredText("on completing Meteor Miner.",128+32)
            if(totalmass==1):
                drawCentredText("Ore collected: %d tonne"%(totalmass),128+96)
            else:
                drawCentredText("Ore collected: %d tonnes"%(totalmass),128+96)

        if(state == PLAYING):
            if(fieldOn and pickupTarget == (0,0)):
                pickupTarget = closestTarget

            if(fieldOn and pickupTarget != (0,0)):
                (x,y) = pickupTarget
                if(blockRange(x,y) > 10000):
                    pickupTarget = (0,0)
                    attachedBlock = (0,0)
                else:
                    pygame.draw.line(screen,(0,0,255),(320,240),(x*32-xoffset+16,y*32-yoffset+16),3)
                    attachedBlock = (x,y)
            if(attachedBlock):
                if(fieldOn):
                    pickUpTimeout -= 1
                    if(pickUpTimeout <= 0):
                        if(blocks[attachedBlock[1]][attachedBlock[0]] == blocktypes["block6"] or blocks[attachedBlock[1]][attachedBlock[0]] == blocktypes["gold"]):
                            mass += 1
                            speed = startSpeed - mass*2
                        else:
                            fuel += 400
                        pickUpTimeout =100
                        blocks[attachedBlock[1]][attachedBlock[0]] = 0
                        attachedBlock = (0,0)
                        pickupTarget = (0,0)
            else:
                pickUpTimeout = 100

        if(state == PLAYING  or state == DEAD):
            if(turretTimeout > 0):
                turretTimeout -= 1


        if(state==PLAYING and ship.ypos < 0 and mass > 0):
            state = WON
            thrustChannel.stop()
            gravity = -3
            #TODO: Play a brief 'win' sound effect
            deadTimeout = 300

        if state == DEAD:
            deadTimeout -= 1
            if(deadTimeout <= 0):
                timers = []
                if(lives > 0):
                    lives -= 1
                    restartGame()            
                else:
                    state = TITLEPAGE

        if state == WON:
            deadTimeout -= 1
            if(deadTimeout <= 0):
                level += 1
                totalmass += mass
                if(level==4):
                    state = FINISHEDGAME
                    deadTimeout = 100
                else:
                    restartGame()            

        if state == FINISHEDGAME:
            deadTimeout -= 1
            if(deadTimeout <= 0):
                timers = []
                state = TITLEPAGE

        if state == PLAYING or state == WON:
            drawShip()

        if state==WON:
            drawWinText()
        
        drawBulletsAndParticles()

        processTimerEvents()

        if state==PLAYING or state==DEAD:
            for m in range(0,mass):
                screen.blit(blockSprites[5], (640-32-m*32,0))        

            if(fuel>100):
                pygame.draw.rect(screen, (255,0,255), (8,8,(fuel-100)/2,8));
            for x in range(0,lives):
                screen.blit(shipSprite, (x*64,0))
            
        frameCounter += 1
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == QUIT:
                exit(0)      
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE or event.key == K_q:
                    exit(0)
                elif state == TITLEPAGE:
                    state = PLAYING
                    startGame()
                    if event.key== K_3:
                        level = 3
                        restartGame()

mainLoop()
