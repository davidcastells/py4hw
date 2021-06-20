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

class AddSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        
    def draw(self, canvas):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y + namemargin

        canvas.drawText(x+25, y+25+5, '+', anchor='c')
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

    
class AndSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)

    def draw(self, canvas):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y + 8

        y = y + 10

        canvas.drawLine(x, y, x + 40, y)
        canvas.drawLine(x, y + 40, x + 40, y + 40)
        canvas.drawLine(x, y, x, y + 40)
        canvas.drawArc(x + 20, y, x + 50, y + 40, start=-90, extent=180) #, style=tkinter.ARC, outline='black', fill='white')

    def getHeight(self):
        return 30

    def getWidth(self):
        return 50
    

class NotSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)

    def draw(self, canvas):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y + namemargin 

        y = y + 10

        canvas.drawPolygon([x, x + 20, x], [y, y + 10, y + 20], outline='black', fill='white')
        canvas.drawEllipse(x + 20, y + 5, x + 30, y + 15, outline='black', fill='white')

    def getHeight(self):
        return 30

    def getWidth(self):
        return 30
    


class OrSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)

    def draw(self, canvas):
        x = self.x
        y = self.y

        canvas.create_text(x, y, text=self.obj.name, anchor='w')
        y = y + namemargin 

        y = y + 10

        canvas.drawLine(x, y, x + 40, y)
        canvas.drawLine(x, y + 40, x + 40, y + 40)
        canvas.drawLine(x, y, x, y + 40)
        #canvas.drawArc(x + 20, y, x + 50, y + 40, start=-90, extent=180, style=tkinter.ARC, outline='black', fill='white')

    def getHeight(self):
        return 30

    def getWidth(self):
        return 50
    
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
        
        
