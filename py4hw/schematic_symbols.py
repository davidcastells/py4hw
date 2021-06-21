# -*- coding: utf-8 -*-
"""
Created on Fri Jun 18 09:43:48 2021

@author: dcr
"""
from .logic import Logic
from .base import Wire
import math

gridsize = 5
portpitch = 28
cellmargin = 20
portSeparation = 10

namemargin = 8
portmargin = 8
instanceportwidth = 4
instanceportheight = 10
instanceporttextmargin = 10
 
#
#  name              name margin
#  +------------+
#  |            |   portmargin          \
#  | i0      o0 |   instanceportheight  |
#  |            |                       |
#  | i1         |                       /- port pitch
#  |            |
#  +------------+

class LogicSymbol:
    def __init__(self, obj:Logic, x:int, y:int):
        self.obj = obj
        self.x = x
        self.y = y
                
        
    def getWireSourcePos(self, wire:Wire):
        selidx = -1
        for idx, port in enumerate(self.obj.outPorts):
            if (port.wire == wire):
                selidx = idx
                
        if (selidx == -1):
            raise Exception('out port not found in {}'.format(self.obj.getFullPath()) )


        return (self.getWidth(), namemargin + portmargin + selidx*portpitch + instanceportheight//2)
    
    def getWireSinkPos(self, wire:Wire):
        selidx = -1
        for idx, port in enumerate(self.obj.inPorts):
            if (port.wire == wire):
                selidx = idx
                
        if (selidx == -1):
            raise Exception('in port not found in {}'.format(self.obj.getFullPath()) )

        
        return (0, namemargin + portmargin + selidx*portpitch + instanceportheight//2)

    def getHeight(self):
        return namemargin + 2*portmargin + max(len(self.obj.inPorts), len(self.obj.outPorts)) * portpitch 
    
    def getWidth(self):
        return 25 * gridsize    

    def getOccupancy(self):
        return {'x':self.x, 'y':self.y, 'w':self.getWidth(), 'h':self.getHeight()}

class BinaryOperatorSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        
    def draw(self, canvas):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y + namemargin

        canvas.drawText(x+25, y+25+5, self.operator, anchor='c')
        canvas.drawEllipse(x, y, x+50, y+50)
        #canvas.drawLine(x, y, x + 40, y)
        #canvas.drawLine(x, y + 40, x + 40, y + 40)
        #canvas.drawLine(x, y, x, y + 40)
        #canvas.drawArc(x + 20, y, x + 50, y + 40, start=-90, extent=180) #, style=tkinter.ARC, outline='black', fill='white')

    def getHeight(self):
        return 50 + namemargin

    def getWidth(self):
        return 50 
    
    def getWireSourcePos(self, wire:Wire):
        return (self.getWidth(), namemargin + 25)
    
    def getWireSinkPos(self, wire:Wire):
        selidx = -1
        for idx, port in enumerate(self.obj.inPorts):
            if (port.wire == wire):
                selidx = idx
                
        if (selidx == -1):
            raise Exception('in port not found in {}'.format(self.obj.getFullPath()) )

        x = int(math.cos(math.pi/4)*25)
        y = int(math.sin(math.pi/4)*25)

        if (selidx == 0):
            y = -y

        return (25-x, namemargin + 25 + y)


class AddSymbol(BinaryOperatorSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        self.operator = '+'

class SubSymbol(BinaryOperatorSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        self.operator = '-'
    
class AndSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        self.h = 40

    def draw(self, canvas):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y + namemargin

        # the and box would be x[0:50] y[0:30]
        canvas.drawLine(x, y, x + 25, y)
        canvas.drawLine(x, y + self.h, x + 25, y + self.h)
        canvas.drawLine(x, y, x, y + self.h)
        canvas.drawArc(x , y, x + 50, y + self.h, start=-90, extent=90) #, style=tkinter.ARC, outline='black', fill='white')

    def getHeight(self):
        return namemargin + self.h

    def getWidth(self):
        return 50
    
    def getWireSourcePos(self, wire:Wire):
        return (self.getWidth(), namemargin + self.h//2)
    
    def getWireSinkPos(self, wire:Wire):
        selidx = -1
        for idx, port in enumerate(self.obj.inPorts):
            if (port.wire == wire):
                selidx = idx
                
        if (selidx == -1):
            raise Exception('in port not found in {}'.format(self.obj.getFullPath()) )

        if (selidx == 0):
            y = self.h//2 - 10
        else:
            y = self.h//2 + 10 

        return (0, namemargin + y)

class NotSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)

    def draw(self, canvas):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y + namemargin 

        y = y + 10

        canvas.drawPolygon([x, x + 20, x], [y, y + 10, y + 20])
        canvas.drawEllipse(x + 20, y + 5, x + 30, y + 15)

    def getHeight(self):
        return 30

    def getWidth(self):
        return 30
    


class OrSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        self.h = 40

    def draw(self, canvas):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y + namemargin

        # the and box would be x[0:50] y[0:30]
        canvas.drawLine(x, y, x + 20, y)
        canvas.drawLine(x, y + self.h, x + 20, y + self.h)
        canvas.drawArc(x-10 , y, x + 10, y + self.h, start=-90, extent=90) #, style=tkinter.ARC, outline='black', fill='white')

        #canvas.drawLine(x, y, x, y + self.h)
        canvas.drawArc(x-30 , y, x + 50+20, y + self.h*4, start=-90, extent=-60) #, style=tkinter.ARC, outline='black', fill='white')
        canvas.drawArc(x-30 , y-self.h*3, x + 50+20, y + self.h, start=60, extent=90) #, style=tkinter.ARC, outline='black', fill='white')

    def getHeight(self):
        return namemargin + self.h

    def getWidth(self):
        return 50
    
    def getWireSourcePos(self, wire:Wire):
        return (self.getWidth(), namemargin + self.h//2)
    
    def getWireSinkPos(self, wire:Wire):
        selidx = -1
        for idx, port in enumerate(self.obj.inPorts):
            if (port.wire == wire):
                selidx = idx
                
        if (selidx == -1):
            raise Exception('in port not found in {}'.format(self.obj.getFullPath()) )

        if (selidx == 0):
            y = self.h//2 - 10
        else:
            y = self.h//2 + 10 

        return (5, namemargin + y)
    
class InPortSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        
    def draw(self, canvas):
        x = self.x 
        y = self.y 
        canvas.drawText(x, y, text=self.obj.name , anchor='w')
        y = y+namemargin 
        
        canvas.drawPolygon([x, x+10, x+15, x+10,x,x], [y, y, y+5, y+10, y+10, y])

    def getWidth(self):
        return 10;
    
    def getHeight(self):
        return 20;
    
    def getWireSourcePos(self, wire:Wire):
        return (self.getWidth(), namemargin +5)
    
class OutPortSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        
    def draw(self, canvas):
        x = self.x 
        y = self.y 
        canvas.drawText(x, y, text=self.obj.name , anchor='w')
        y = y+namemargin 
        
        canvas.drawPolygon([x, x+10, x+15, x+10, x, x], [y, y, y+5, y+10, y+10, y])

    def getWidth(self):
        return 10;
    
    def getHeight(self):
        return 20;
    
    def getWireSinkPos(self, wire:Wire):
        return (0, namemargin + 5)
    
class InstanceSymbol(LogicSymbol):
    def __init__(self, obj:Logic, x:int, y:int):
        super().__init__(obj, x, y)
    
    def draw(self, canvas):
        x = self.x 
        y = self.y 
        
        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y+namemargin 
        
        canvas.drawRectangle(x, y, x + self.getWidth(), y + self.getHeight() - namemargin)

        ipw = instanceportwidth 
        iph = instanceportheight
        iphh = iph//2
        iptm = instanceporttextmargin

        y = y + portmargin
        
        for inp in self.obj.inPorts:
            canvas.drawPolygon([x, x+ipw, x+ipw+iphh, x+ipw, x,x], [y, y, y+iphh, y+iph, y+iph,y])
            canvas.drawText(x+ipw+iph, y+iptm, text=inp.name , anchor='w')
            y = y+portpitch
            
        y = self.y + namemargin + portmargin
        

        for inp in self.obj.outPorts:
            x = self.x + self.getWidth() - ipw - iphh 
            canvas.drawPolygon([x, x+ipw, x+ipw+iphh, x+ipw, x, x], [y, y, y+iphh, y+iph, y+iph, y])
            x = self.x + self.getWidth() - ipw - iph -iphh
            canvas.drawText(x, y+iptm, text=inp.name , anchor='e')
            y = y+portpitch
        
        

class NetSymbol:
    def __init__(self, source, sink):
        self.source = source
        self.sink = sink
        
    def getStartPoint(self):
        objsource = self.source['symbol']
        portsource = objsource.getWireSourcePos(self.source['wire'])
        return (objsource.x + portsource[0], objsource.y + portsource[1]) 
    
    def getEndPoint(self):
        objsink = self.sink['symbol']
        portsink = objsink.getWireSinkPos(self.source['wire'])
        return (objsink.x + portsink[0], objsink.y + portsink[1]) 
    
    def setPath(self, x, y):
        self.x = x
        self.y = y
        
    def draw(self, canvas):
        canvas.setForecolor('blueviolet')
        canvas.setLineWidth(1)
        canvas.drawPolygon(self.x, self.y)
        
        # draw the arrow finishing
        x = self.x[len(self.x)-1]
        y = self.y[len(self.y)-1]
        
        ars = 5
        
        canvas.drawPolygon([x-ars*2, x, x-ars*2, x-ars*2],[y-ars,y,y+ars, y-ars], fill=True)