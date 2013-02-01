import xml.etree.ElementTree as ET

TILELAYER = "world"
OBJECTLAYER = "objects"
TILESIZE = 32
actionMap = { "pub": 1, "exit": 2, "magicshop": 3 }

def processTileLayer(layer):
    mapData = []
    for e in layer:
        if(e.tag=="data"):
            if(e.attrib['encoding'] != "csv"):
                print "Tile data is not encoded in CSV (found %s)"%(e.attrib['encoding'])
                exit(1)
            lines = e.text.splitlines()
            for l in lines:
                chars = l.split(",")
                if(len(chars)<=1): continue
                mapData.append(map(int,filter(str.isdigit,l.split(","))))
    return mapData

def getProperties(elem):
    props = {}
    for p in elem:
        props[p.attrib['name']] = p.attrib['value']
    return props

def getObjectProperties(elem):
    for p in elem:
        if(p.tag == "properties"):
            return getProperties(p)
    return {}

def addPolyLine(links,obj,polytag,props):
    #TODO: This expects a polyline with only one segment and expects the first point
    # to be 0,0, which is not always the case. This could be improved.
    basex1 = int(obj.attrib['x'])
    basey1 = int(obj.attrib['y'])
    points = polytag.attrib['points'].split(" ")
    (x1,y1) = map(int,points[0].split(","))
    (x2,y2) = map(int,points[1].split(","))
    x1 += basex1
    y1 += basey1
    x2 += basex1
    y2 += basey1
    x1 /= TILESIZE
    y1 /= TILESIZE
    x2 /= TILESIZE
    y2 /= TILESIZE
    links[(x1,y1)] = (x2,y2)
    if('oneway' not in props):
        links[(x2,y2)] = (x1,y1)

def processAction(links, obj,props): # For teleporter like things
    x1 = int(obj.attrib['x'])/TILESIZE
    y1 = int(obj.attrib['y'])/TILESIZE
    if "action" in props and props['action'] in actionMap:
            links[(x1,y1)] = (0,actionMap[props['action']])

def processItem(objects, obj, props): # For cyan things (sword, ship, shield)
    x1 = int(obj.attrib['x'])/TILESIZE
    y1 = int(obj.attrib['y'])/TILESIZE
    objects[(x1,y1)] = props['item']

def processObjectLayer(layer):
    links = {}
    objects = {}
    for e in layer: # e are all 'object'
        props = getObjectProperties(e)
        if "item" in props:
            processItem(objects, e, props)
        elif "action" in props:
            processAction(links, e, props)
        else:
            for p in e:
                if(p.tag == "polyline"):
                    addPolyLine(links,e,p,props)
    return (links,objects)

def readMap(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    for child in root:
        if(child.tag=="layer"):
            if(child.attrib['name']==TILELAYER):
                tiles = processTileLayer(child)
        elif(child.tag=="objectgroup"):
            if(child.attrib['name']==OBJECTLAYER):
                objects = processObjectLayer(child)
    return (tiles,objects)

if __name__ == "__main__":
    m = readMap("level1.tmx")
