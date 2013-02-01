# Microhack, a PyGame reimplementation of TinyHack.
# Written by Jim MacArthur, January 2013
# TinyHack originally by Rob Beschizza: http://boingboing.net/rob/tinyhack/

import pygame
from pygame.locals import *

from tilereader import readMap
import random

# Enum definition from Alec Thomas on StackOverflow
def enum(**enums):
    return type('Enum', (), enums)

# Some constant globals
tiles = enum(
    GRAY1 = 1, LIGHTGRAY = 2,
    ROCK = 3, DOOR = 4,
    SHALLOWWATER = 5, DEEPWATER = 6,
    GRASS = 7, DARKGRASS = 8,
    MONSTER1 = 9, MONSTER2 = 10,
    GOLD = 11, OBJECT = 12)

cols = [ (0x7f,0x7f,0x7f), (0x3f,0x3f,0x3f), (0xff,0xff,0xff), 
         (0xff,0,0), (0x7f,0x7f,0xff), (0,0,0xff), (0,0xc0,0),
         (0,0x7f,0), (0x7f,0,0), (0xff,0,0xff), (0xff,0xff,0),
         (0x00, 0xff, 0xff)]

enterable = [ tiles.GRAY1, tiles.GRASS, tiles.DARKGRASS, tiles.GOLD, tiles.OBJECT ]

directions = { K_LEFT: (-1,0), K_RIGHT: (1,0), K_UP: (0,-1), K_DOWN: (0,1) }

# Other globals that will be set up in initialization
sounds = {}
level1world = None
teleporters = None
objects = { }
enemyList = []

def cutScene(filename):
    global screen
    img = pygame.transform.scale(pygame.image.load(filename+".png"), (32*9,32*9))
    backup = pygame.surface.Surface((32*9,32*9))
    backup.blit(screen,(0,0))
    screen.blit(img, (0,0))
    pygame.display.flip()
    getKeypress()
    screen.blit(backup,(0,0))

def sound(filename):
    global sounds
    if filename in sounds:
        sounds[filename].play()
        return
    s = pygame.mixer.Sound(filename+".wav")
    s.play()
    sounds[filename] = s

class Entity:
    def __init__(self,x,y):
        self.x = x
        self.y = y 
        self.HP = 10
        self.maxHP = 10
        self.gold = 0
        self.team = "evil"
        self.attack = 1
        self.magic = 0
    def getColour(self):
        halfHP = self.maxHP/2
        if(self.HP < halfHP):
            return (255,255*self.HP/halfHP,0)
        else:
            return (255*(self.maxHP-self.HP)/halfHP,255,0)

def lift(enemyList):
    for y in range(0,len(level1world)):
        for x in range(0,len(level1world[y])):
            if(level1world[y][x] == tiles.MONSTER1):
                level1world[y][x] = tiles.GRAY1
                enemyList.append(Entity(x,y))
            elif(level1world[y][x] == tiles.MONSTER2):
                level1world[y][x] = tiles.GRAY1
                e = Entity(x,y)
                e.HP = 20
                e.maxHP = 20
                enemyList.append(e)

def contents(x,y):
    global enemyList
    for e in enemyList:
        if(e.x == x and e.y==y): return e
    return None

def canMove(x,y):
    return contents(x,y)==None and level1world[y][x] in enterable

def attemptMonsterMove(entity, dx, dy):
    if(canMove(entity.x+dx,entity.y+dy)): 
        entity.x += dx
        entity.y += dy
        return True
    c = contents(entity.x+dx,entity.y+dy)
    if(c is not None and c.team != entity.team):
        attack(entity, c)
        return True
    return False

def monMove(enemyList):
    (xpos, ypos) = (enemyList[0].x,enemyList[0].y)
    for e in enemyList[1:]:
        dx = xpos-e.x
        dy = ypos-e.y
        if(dx>0 and attemptMonsterMove(e,1,0)): return
        elif(dx<0 and attemptMonsterMove(e,-1,0)): return
        elif(dy>0 and attemptMonsterMove(e,0,1)): return
        elif(dy<0 and attemptMonsterMove(e,0,-1)): return

def activateTeleporter(entity,x,y):
    (destx, desty) = teleporters[(x,y)]
    if(destx == 0):
        if(desty == 1): # Pub
            sound("door")
            cutScene("pub")
            entity.HP = entity.maxHP
        elif(desty == 2): # Exit
            sound("powerup")
            cutScene("win")
            print "You escaped the island with %d gold"%entity.gold
            exit(0);
        if(desty == 3): # Magicshop
            sound("door")
            cutScene("magic")
            entity.magic = 1
    else:
        sound("door")
        (entity.x,entity.y) = (destx,desty)

def attack(attacker, defender):
    defender.HP -= random.randint(1,attacker.attack)
    sound("punch")
    
def playerMove((dx,dy)):
    global moved, enemyList
    player = enemyList[0]
    c = contents(player.x+dx,player.y+dy)
    if(canMove(player.x+dx,player.y+dy)):
        player.x+=dx
        player.y+=dy
        if level1world[player.y][player.x]==tiles.GOLD:
            level1world[player.y][player.x]=tiles.GRAY1
            sound("coin")
            player.gold += 1
        elif level1world[player.y][player.x]==tiles.OBJECT:
            level1world[player.y][player.x]=tiles.GRAY1
            if((player.x,player.y) not in objects):
                print "No item type found at %d,%d"%(player.x,player.y)
                exit(2)
            objtype = objects[(player.x,player.y)]
            sound("powerup")
            print "Collected item:",objtype
            if(objtype == "hp"):
                player.maxHP += 10
                player.HP = player.maxHP
                cutScene("shield")
            elif(objtype == "sword"):
                player.attack += 1
                cutScene("sword")
            elif(objtype == "boat"):
                global enterable
                cutScene("boat")
                enterable.append(tiles.SHALLOWWATER)
        moved = True
    elif(c != None):
        attack(player,c)
        moved = True
    elif(level1world[player.y+dy][player.x+dx] == tiles.DOOR and (player.x+dx,player.y+dy) in teleporters):
        activateTeleporter(player,player.x+dx,player.y+dy)
        moved = True

def alive(e): return e.HP>0

def getKeypress():
    while(True):
        event = pygame.event.wait()
        if event.type == QUIT:
            exit(0)
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE or event.key == K_q:
                exit(0)
            else:
                return event.key

def fireBeam(entity):
    x = entity.x
    y = entity.y
    (dx,dy) = directions[entity.dir]
    sound("magic")
    while True:
        x += dx
        y += dy
        if(level1world[y][x] in enterable):
            c = contents(x,y)
            if(c is not None):
                c.HP -= 5
                return
        else:
            return

def main():
    pygame.init()
    global moved, enemyList, level1world, teleporters, objects, screen
    screen = pygame.display.set_mode((32*9, 32*9))
    pygame.display.set_caption("MicroHack")
    clock = pygame.time.Clock()
    moved = False
    (level1world,(teleporters,objects)) = readMap("level1.tmx")
    player = Entity(5,5)
    player.team = "good"
    player.attack = 2
    enemyList = [player]
    lift(enemyList)
    while True:
        screen.fill((0,0,0))
        (xpos,ypos) = (enemyList[0].x,enemyList[0].y)
        if(enemyList[0].HP<=0):
            sound("fail")
            cutScene("lose")
            print "Player killed"
            return
        enemyList = filter(alive,enemyList)
        if(moved):
            monMove(enemyList)
            moved = False
        for x in range(0,9):
            for y in range(0,9):
                val = level1world[y+ypos-4][x+xpos-4]
                if(val>0): col = cols[val-1]
                else: col = (0,0,0)
                pygame.draw.rect(screen, col, (x*32,y*32,32,32))
        for e in enemyList:
            pygame.draw.rect(screen, e.getColour(), ((e.x-xpos+4)*32,(e.y-ypos+4)*32,32,32))
        if(player.magic > 0):
            pygame.draw.rect(screen, (random.randint(0,255),random.randint(0,255),random.randint(0,255)), (8*32,0,32,32))
        pygame.display.flip()
        key = getKeypress()
        if key in directions: 
            playerMove(directions[key])
            # Note that we set direction whether or not the move succeeded.
            player.dir = key
        elif key == K_SPACE:
            if(player.magic>0):
                player.magic -= 1
                fireBeam(player)
                moved = True
main()
