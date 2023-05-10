# -*- coding: utf-8 -*-
"""
Created on Wed Apr 19 12:44:39 2023

@author: dcr
"""

import math
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
from matplotlib.patches import Ellipse

def drawLine(x0, y0, x1, y1, color):
    plt.plot([x0,x1], [y0,y1], color)

def drawRect(x0, y0, x1, y1, color):
    cx = (x0+x1)/2
    cy = (y0+y1)/2
    w = x1 - x0
    h = y1 - y0
    
    plt.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], color=color)
    
def drawEllipse(x0, y0, x1, y1, color):
    cx = (x0+x1)/2
    cy = (y0+y1)/2
    w = x1 - x0
    h = y1 - y0
    
    circle = Ellipse((cx, cy), w, h, color=color, fill=False)
    plt.gca().add_patch(circle)

def drawPoint(x, y, color):
    circle = plt.Circle((x, y), 3, color=color)
    plt.gca().add_patch(circle)
    


def drawArc(x0, y0, x1, y1, rx0, ry0, rx1, ry1, color):
    cx = (rx0+rx1)/2
    cy = (ry0+ry1)/2
    w = rx1-rx0
    h = ry1-ry0
    vx0 = (x0-cx)
    vy0 = (y0-cy)
    theta0 = math.atan2(vy0, vx0) * (180/math.pi)
    vx1 = (x1-cx)
    vy1 = (y1-cy)
    theta1 = math.atan2(vy1, vx1) * (180/math.pi)
    arc = Arc((cx,cy), w, h, 0, theta1, theta0, color=color)
    plt.gca().add_patch(arc)
    
    #print('theta0', theta0, 'theta1', theta1)
    
def tokenize_strings(line):
    i = 0
    ret = []
    
    s = ''
    instring = False
    
    while (i < len(line)):
        c = line[i]
        
        if (instring):
            if (c == '"'):
                instring = False
                ret.append(s)
                s = ''
            else:
                s += c
        else:
            if (c == '('):
                ret.append(c)
            elif (c == ')'):
                if (len(s) > 0):
                    ret.append(s)
                s = ''
                ret.append(c)
            elif (c == '"'):
                instring = True
            elif (c == ' '):
                if (len(s) > 0):
                    ret.append(s)
                s = ''
            else:
                s += c
            
        i += 1
        
        
    return ret

def listify_tokens(inlist, pos=0, level=0):
    ret = []
    while (pos < len(inlist)):
        token = inlist[pos]
        
        if (token == '('):
            subtokens, newpos = listify_tokens(inlist, pos+1, level+1)
            pos = newpos
            ret.append(subtokens)
        elif (token == ')'):
            return ret, pos+1
        else:
            ret.append(token)
            pos += 1
            
    return ret


class BDFObj():
    def __init__(self):
        self.child = []
        
    def draw(self, ox=0, oy=0, color='black'):
        #print('Draw:', type(self))
        for item in self.child:
            item.draw(ox, oy, color)
            
    def find(self, ty):
        for item in self.child:
            if (isinstance(item, ty)):
                return item
        raise Exception('no {} child '.format(ty))
        
    def findAll(self, ty):
        ret = []
        
        for item in self.child:
            if (isinstance(item, ty)):
                ret.append(item)
                
        return ret
    
    def bbox(self):
        # returns a bounding box of the object
        rx0 = math.inf
        ry0 = math.inf
        rx1 = -math.inf
        ry1 = -math.inf
        
        for item in self.child:
            ix0, iy0, ix1, iy1 = item.bbox()
            
            if (ix0 < rx0):
                rx0 = ix0
            if (iy0 < ry0):
                ry0 = iy0
            if (ix1 > rx1):
                rx1 = ix1
            if (iy1 > ry1):
                ry1 = iy1
                
        return rx0, ry0, rx1, ry1

class BDFTop(BDFObj):
    pass

class BDFPin(BDFObj):
    
    def draw(self, ox=0, oy=0, color='black'):
        r = self.find(BDFRect)
        pt = self.find(BDFPoint)
        
        #ox, oy =  pt.x, pt.y
        ox = r.rx
        oy = r.ry
        
        drw = self.find(BDFDrawing)
        
        for line in drw.findAll(BDFLine):
            line.draw(ox, oy, color)
            
        for text in self.findAll(BDFText):
            text.draw(ox, oy, color)
        
class BDFPort(BDFObj):
    pass
        
class BDFInput(BDFObj):
    pass

class BDFOutput(BDFObj):
    pass

class BDFConnector(BDFObj):
    def draw(self, ox=0, oy=0, color='black'):
        points = self.findAll(BDFPoint)
        x = [ox + pt.x for pt in points]
        y = [oy + pt.y for pt in points]
        plt.plot(x, y, color)
        
        for text in self.findAll(BDFText):
            text.draw(ox, oy, color)

class BDFSymbol(BDFObj):
    def draw(self, ox=0, oy=0, color='black'):
        r = self.find(BDFRect)
        ox, oy = r.rx, r.ry
        
        #r.draw('blue')
        
        for port in self.findAll(BDFPort):
            #pt = port.find(BDFPoint)
            
            port.draw(ox, oy, color)
            #for line in port.findAll(BDFLine):
            #    line.draw(ox, oy)
                
        drw = self.find(BDFDrawing)
        
        for line in drw.findAll(BDFObj):
            #print('draw', type(line))
            line.draw(ox, oy)

class BDFDrawing(BDFObj):
    pass

class BDFRect(BDFObj):
    
    def parse(self, line):
        line = line[5:-1]
        part = line.split()
        self.rx = int(part[0])
        self.ry = int(part[1])
        self.rw = int(part[2]) - self.rx
        self.rh = int(part[3]) - self.ry
        
    def draw(self, ox=0, oy=0, color='black'):
        plt.plot([self.rx,self.rx+self.rw,self.rx+self.rw,        self.rx,self.rx],
                 [self.ry,        self.ry,self.ry+self.rh,self.ry+self.rh,self.ry], color)
        
    def bbox(self):
        return self.rx, self.ry, self.rx + self.rw, self.ry + self.rh

class BDFRectangle(BDFObj):
    def parse(self, line):
        tokens = tokenize_strings(line)
        li = listify_tokens(tokens)[0]
        
        self.x0 = int(li[1][1])
        self.y0 = int(li[1][2])
        self.x1 = int(li[1][3])
        self.y1 = int(li[1][4])
        
    def draw(self, ox=0, oy=0, color='black'):
        drawRect(ox + self.x0, oy + self.y0, ox + self.x1, oy + self.y1, color)

class BDFCircle(BDFObj):
    
    def parse(self, line):
        line = line.split('(rect')[1]
        #print('CIRCLE LINE:', line)
        part = line[:-2].split()
        
        self.rx0 = int(part[0])
        self.ry0 = int(part[1])
        self.rx1 = int(part[2]) 
        self.ry1 = int(part[3]) 
        
    def draw(self, ox=0, oy=0, color='black'):
        drawEllipse(ox + self.rx0, oy + self.ry0, ox + self.rx1, oy + self.ry1, color)

class BDFPoint(BDFObj):
    
    def parse(self, line):
        line = line[3:-1]
        #print('parsing point', line)
        part = line.split()
        self.x = int(part[0])
        self.y = int(part[1])

class BDFLine(BDFObj):
    
    def parse(self, line):
        #print('parse', type(self))
        part = line.split(')')
        part = [x.split() for x in part]
        self.x0, self.y0 = int(part[0][2]), int(part[0][3])
        self.x1, self.y1 = int(part[1][1]), int(part[1][2])
    
    def draw(self, ox=0, oy=0, color='black'):
        plt.plot([ox+self.x0,ox+self.x1], [oy+self.y0,oy+self.y1], color)

class BDFText(BDFObj):
    
    
    def parse(self, line):
        # (text "Pis_7s[3]" (rect 400 464 446 476)(font "Arial" ))
        # (text "OUT" (rect 48 47 65 59)(font "Courier New" (bold))(invisible))
        #print('PARSE TEXT', line)
        tokens = tokenize_strings(line)
        li = listify_tokens(tokens)[0]
        
        assert(li[2][0] == 'rect')
        self.rx0 = int(li[2][1])
        self.ry0 = int(li[2][2])
        self.rx1 = int(li[2][3])
        self.ry1 = int(li[2][4])
        
        self.invisible = 'invisible' in li[-1]
        
        self.text = li[1]
        
    def draw(self, ox=0, oy=0, color='black'):
        #print('DRAW TEXT:', self.text)
        
        if not(self.invisible):
            ax = plt.gca()
            plt.text(ox+self.rx0, oy+self.ry0, self.text , fontsize=8) #, transform=ax.transAxes)
    
class BDFJunction(BDFObj):
    
    def parse(self, line):
        pass
    
    def draw(self, ox=0, oy=0, color='black'):
        pass

class BDFArc(BDFObj):
    def parse(self, line):
        # (arc (pt 8 61)(pt 8 51)(rect -13 40 20 73))
        line = line[4:-1]
        line = line.replace(')', ' ')

        part = line.split('(rect')
        
        pts = part[0].split()
        self.x0 = int(pts[1])
        self.y0 = int(pts[2])
        self.x1 = int(pts[4])
        self.y1 = int(pts[5])
        
        #print('ARC pt:', self.x0, self.y0, self.x1, self.y1)
        
        pr = part[1][:-1].split()
        
        self.rx0 = int(pr[0])
        self.ry0 = int(pr[1])
        self.rx1 = int(pr[2]) 
        self.ry1 = int(pr[3]) 
        
    def draw(self, ox=0, oy=0, color='black'):
        drawArc(ox + self.x0, oy + self.y0, ox + self.x1, oy + self.y1, 
                ox + self.rx0 , oy + self.ry0, ox + self.rx1 , oy + self.ry1, color=color)
        
        #drawPoint(ox + self.x0, oy + self.y0, color)
        #drawPoint(ox + self.x1, oy + self.y1, color)
        #drawLine(ox + self.x0, oy + self.y0, ox + self.x1, oy + self.y1, color)
    
class DrawBDF():
    def __init__(self):
        self.rx = 0
        self.ry = 0
    
    def readfile(self, filename):
        f = open(filename, 'r')
        lines = f.readlines()
        ret = []
        
        # remove comments
        incomment = False
        for line in lines:
            if not(incomment):
                if '/*' in line:
                    part = line.split('/*')
                    ret.append(part[0])
                    incomment = True
                else:
                    if (len(line) > 0):
                        ret.append(line)
            else:
                if '*/' in line:
                    part = line.split('*/')
                    ret.append(part[1])
                    incomment = False
                else:
                    pass
                
        lines = ret
        
        # remove \n
        ret = []
        for line in lines:
            parts = line.split('\n')
            for part in parts:
                if (len(part) > 0):
                    ret.append(part.strip()) 
                    
        return ret
    
    def load(self, filename):
        self.lines = self.readfile(filename)
        self.i =0
        
        self.top = BDFTop()
        self.parseObjects(self.top)
        
        #print('START DRAWING')
        #self.top.draw()

    def draw(self, figsize=None):
        self.top.draw()

        ar = 1
        if not(figsize is None):
            plt.rcParams['figure.figsize'] = figsize
            ar = figsize[0]/figsize[1]
            
        
        x0, y0, x1, y1 = self.top.bbox()

        w = x1-x0
        h = y1-y0

        #print('w', w)
        #print('h', h)

        maxaxis = max(w,h)

        x1 = x0 + maxaxis 
        y1 = y0 + maxaxis / ar

        plt.ylim(y1, y0)
        plt.xlim(x0, x1)

        plt.show()    
        
    def parseObjects(self, obj):
        #print('parse', type(obj))
        while (self.i < len(self.lines)):
            line = self.lines[self.i]
            self.i+=1
            
            #print('{}:{}'.format(self.i, line))
            
            if (line[:7] == '(header' ):
                pass
            elif (line[:4] == '(pin'):
                pin = BDFPin()
                self.parseObjects(pin)
                obj.child.append(pin)
            elif (line[:5] == '(port'):
                port = BDFPort()
                self.parseObjects(port)
                obj.child.append(port)
            elif (line == '(connector'):
                port = BDFConnector()
                self.parseObjects(port)
                obj.child.append(port)
            elif (line[:3] == '(pt'):
                pt = BDFPoint()
                pt.parse(line)
                obj.child.append(pt)
            elif (line[:7] == '(symbol'):
                symbol = BDFSymbol()
                self.parseObjects(symbol)
                obj.child.append(symbol)
            elif (line[:8] == '(drawing'):
                drawing = BDFDrawing()
                self.parseObjects(drawing)
                obj.child.append(drawing)
            elif (line[:5] == '(line'):
                lobj = BDFLine()
                lobj.parse(line)
                obj.child.append(lobj)
            elif (line[:4] == '(arc'):
                lobj = BDFArc()
                lobj.parse(line)
                obj.child.append(lobj)
            elif (line[:10] == '(rectangle'):
                lobj = BDFRectangle()
                lobj.parse(line)
                obj.child.append(lobj)
            elif (line[:5] == '(rect'):
                robj = BDFRect()
                robj.parse(line)
                obj.child.append(robj)
            elif (line[:7] == '(circle'):
                lobj = BDFCircle()
                lobj.parse(line)
                obj.child.append(lobj)
            elif (line == '(input)'):
                lobj = BDFInput()
                obj.child.append(lobj)
            elif (line == '(output)'):
                lobj = BDFInput()
                obj.child.append(lobj)
            elif (line[:5] == '(text'):
                lobj = BDFText()
                lobj.parse(line)
                obj.child.append(lobj)
            elif (line[:9] == '(junction'):
                lobj = BDFJunction()
                lobj.parse(line)
                obj.child.append(lobj)
            elif (line == ')'):
                #print('<<<<<', type(obj))
                return
            else:
                print('?? - ?? - ??', line)
                