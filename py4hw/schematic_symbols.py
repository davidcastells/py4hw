# -*- coding: utf-8 -*-
"""
Created on Fri Jun 18 09:43:48 2021

@author: dcr
"""
from .logic.bitwise import *
from .base import Wire
import math

gridsize = 5
portpitch = 28
cellmargin = 50
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
        
class MulSymbol(BinaryOperatorSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        self.operator = '*'
    
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
        canvas.drawArc(x , y+2, x + 50, y + self.h, start=-90, extent=90) #, style=tkinter.ARC, outline='black', fill='white')

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

        canvas.drawPolygon([x, x + 30, x, x], [y, y + 15, y + 30, y])
        canvas.drawEllipse(x + 30, y + 10, x + 40, y + 20)

    def getHeight(self):
        return 30

    def getWidth(self):
        return 40
    
    def getWireSourcePos(self, wire:Wire):
        return (self.getWidth(), namemargin + 25)
    
    def getWireSinkPos(self, wire:Wire):
        return (0, namemargin + 25)
    
    
class BufSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)

    def draw(self, canvas):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y + namemargin 

        canvas.drawPolygon([x, x + 20, x, x], [y, y + 10, y + 20, y])
        
    def getHeight(self):
        return 20

    def getWidth(self):
        return 20

    def getWireSourcePos(self, wire:Wire):
        return (self.getWidth(), namemargin + 10)
    
    def getWireSinkPos(self, wire:Wire):
        return (0, namemargin + 10)
    
class BitSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)

    def draw(self, canvas):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text='[{}]'.format(self.obj.bit), anchor='w')
        y = y + namemargin 

        canvas.drawLine(x+10,y, x, y+20)
        #canvas.drawPolygon([x, x + 20, x, x], [y, y + 10, y + 20, y])
        
    def getHeight(self):
        return 20

    def getWidth(self):
        return 20

    def getWireSourcePos(self, wire:Wire):
        return (10, namemargin + 10)
    
    def getWireSinkPos(self, wire:Wire):
        return (0, namemargin + 10)
    
class RangeSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)

    def draw(self, canvas):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text='[{}:{}]'.format(self.obj.high, self.obj.low), anchor='w')
        y = y + namemargin 

        canvas.drawLine(x+10,y, x, y+20)
        #canvas.drawPolygon([x, x + 20, x, x], [y, y + 10, y + 20, y])
        
    def getHeight(self):
        return 20

    def getWidth(self):
        return 20

    def getWireSourcePos(self, wire:Wire):
        return (10, namemargin + 10)
    
    def getWireSinkPos(self, wire:Wire):
        return (0, namemargin + 10)
    
class NorSymbol(LogicSymbol):
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

        canvas.drawEllipse(x + 55, y + 15, x + 65, y + 25)

    def getHeight(self):
        return namemargin + self.h

    def getWidth(self):
        return 65
    
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
    
class OrSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        
        if (isinstance(obj, Or2)):
            self.nins = 2
        else:
            self.nins = len(obj.ins)

        self.h = 20 * self.nins
        
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
        #canvas.drawArc(x-30 , y, x + 50+20, y + self.h + (self.nins+1)*40, start=-90, extent=-60) #, style=tkinter.ARC, outline='black', fill='white')
        #canvas.drawArc(x-30 , y - (self.nins+1)*40, x + 50+20, y + self.h, start=60, extent=90) #, style=tkinter.ARC, outline='black', fill='white')
        canvas.drawSpline([x+20, x+30, x+42, x+50], [y,  y+2, y+self.h//4, y+self.h//2])
        canvas.drawSpline([x+20, x+30, x+42, x+50], [y+self.h,  y+self.h-2, y+self.h-self.h//4, y+self.h//2])

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

        y = 10 + selidx * 20

        return (5, namemargin + y)
    
class XorSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        self.h = 40

    def draw(self, canvas):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y + namemargin

        # the and box would be x[0:50] y[0:30]
        canvas.drawLine(x+10, y, x + 20+10, y)
        canvas.drawLine(x+10, y + self.h, x + 20+10, y + self.h)
        canvas.drawArc(x-10 , y, x + 10, y + self.h, start=-90, extent=90) #, style=tkinter.ARC, outline='black', fill='white')
        canvas.drawArc(x , y, x + 20, y + self.h, start=-90, extent=90) #, style=tkinter.ARC, outline='black', fill='white')

        canvas.drawArc(x-30 +10, y, x + 50+20+10, y + self.h*4, start=-90, extent=-60) #, style=tkinter.ARC, outline='black', fill='white')
        canvas.drawArc(x-30 +10, y-self.h*3, x + 50+20+10, y + self.h, start=60, extent=90) #, style=tkinter.ARC, outline='black', fill='white')



    def getHeight(self):
        return namemargin + self.h

    def getWidth(self):
        return 50+10
    
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
        return 15;
    
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
        return 15;
    
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
        
        
class RegSymbol(InstanceSymbol):
    def __init__(self, obj:Logic, x:int, y:int):
        super().__init__(obj, x, y)
        
    def getWidth(self):
        return 65
    
class ScopeSymbol(InstanceSymbol):
    def __init__(self, obj:Logic, x:int, y:int):
        super().__init__(obj, x, y)
        
    def getWidth(self):
        return 80
    
    def getHeight(self):
        return 80
    
    def draw(self, canvas):
        x = self.x 
        y = self.y 
        
        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y+namemargin 

        canvas.setFillcolor('lightsalmon')
        canvas.drawRectangle(x, y, x + self.getWidth(), y + self.getHeight() - namemargin, fill=True)

        ipw = instanceportwidth 
        iph = instanceportheight
        iphh = iph//2
        iptm = instanceporttextmargin

        y = y + portmargin
        
        for inp in self.obj.inPorts:
            canvas.drawPolygon([x, x+ipw, x+ipw+iphh, x+ipw, x,x], [y, y, y+iphh, y+iph, y+iph,y])
            #canvas.drawText(x+ipw+iph, y+iptm, text=inp.name , anchor='w')
            y = y+portpitch
            
        y = self.y + namemargin + portmargin
        
        canvas.setFillcolor('white')
        canvas.drawRoundRectangle(x+25, y+20, x+self.getWidth()-25, y-20+self.getHeight()-namemargin-20, radius=10, fill=True)
        
class Mux2Symbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        self.h = 20*3

    def draw(self, canvas):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y + namemargin

        canvas.setForecolor('blueviolet')  
        canvas.setLineWidth(1)
        canvas.drawLine(x, y+10, x+15, y+10)
        canvas.drawLine(x+15, y+10, x+15, y+25)

        y = y+20
        
        canvas.setForecolor('k')  
        canvas.setLineWidth(2)
        
        # the and box would be x[0:50] y[0:30]
        canvas.drawLine(x, y, x + 20, y+10)
        canvas.drawLine(x, y, x , y+40)
        canvas.drawLine(x, y+40, x + 20, y + 30)
        canvas.drawLine(x+20, y+10, x+20 , y+30)

        canvas.setForecolor('blueviolet')
        canvas.setFillcolor('blueviolet')
        
        ars = 3
        x = x + 15
        y = y + 5
        canvas.drawPolygon([x-ars+1,x+1,x+ars+1, x-ars+1], [y-ars*2, y, y-ars*2, y-ars*2], fill=True)


    def getHeight(self):
        return namemargin + self.h

    def getWidth(self):
        return 20
    
    def getWireSourcePos(self, wire:Wire):
        return (self.getWidth(), namemargin + 40)
    
    def getWireSinkPos(self, wire:Wire):
        selidx = -1
        for idx, port in enumerate(self.obj.inPorts):
            if (port.wire == wire):
                selidx = idx
                
        if (selidx == -1):
            raise Exception('in port not found in {}'.format(self.obj.getFullPath()) )

        if (selidx == 0):
            y = 10
        elif (selidx == 1):
            y = 30 
        else:
            y = 50 

        return (0, namemargin + y)

class PassthroughSymbol(LogicSymbol):
    def __init__(self):
        super().__init__(None, 0, 0)
        
    def getHeight(self):
        return 30
    
    def getWidth(self):
        return 30
    
    def draw(self, canvas):
        x = self.x
        y = self.y
        
        canvas.setForecolor('blueviolet')  
        canvas.setLineWidth(1)
        
        #canvas.drawRectangle(x, y, x+30, y+30)
        canvas.drawLine(x, y+15, x+30, y+15)

        canvas.setForecolor('k')  
        canvas.setLineWidth(2)
        
    def getWireSinkPos(self, wire:Wire):
        return (0, 15);
    
    def getWireSourcePos(self, wire:Wire):
        return (30, 15);
    
class FeedbackStartSymbol(LogicSymbol):
    def __init__(self):
        super().__init__(None, 0, 0)
        
    def getHeight(self):
        return 30
    
    def getWidth(self):
        return 30
    
    def draw(self, canvas):
        x = self.x
        y = self.y
        
        canvas.setForecolor('red')  
        canvas.setLineWidth(1)
        
        #canvas.drawRectangle(x, y, x+30, y+30)
        canvas.drawLine(x, y+15, x+30, y+15)

        canvas.setForecolor('k')  
        canvas.setLineWidth(2)
        
    def getWireSinkPos(self, wire:Wire):
        return (0, 15);
    
    def getWireSourcePos(self, wire:Wire):
        return (30, 15);
    
class FeedbackStopSymbol(LogicSymbol):
    def __init__(self):
        super().__init__(None, 0, 0)
        
    def getHeight(self):
        return 30
    
    def getWidth(self):
        return 30
    
    def draw(self, canvas):
        x = self.x
        y = self.y
        
        canvas.setForecolor('red')  
        canvas.setLineWidth(1)
        
        #canvas.drawRectangle(x, y, x+30, y+30)
        canvas.drawLine(x, y+15, x+30, y+15)

        canvas.setForecolor('k')  
        canvas.setLineWidth(2)
        
    def getWireSinkPos(self, wire:Wire):
        return (0, 15);
    
    def getWireSourcePos(self, wire:Wire):
        return (30, 15);
    
    
class NetSymbol:
    def __init__(self, wire:Wire, source:LogicSymbol, sink:LogicSymbol):
        """
        Constructor of net symbol

        Parameters
        ----------
        wire : Wire
            Associated wire.
        source : LogicSymbol
            source logic symbol.
        sink : LogicSymbol
            sink logic symbol.

        Returns
        -------
        None.

        """
        self.wire = wire
        self.source = source
        self.sink = sink
        self.x = None
        self.y = None
        self.routed = False
        self.arrow = True
        
    def getStartPoint(self):
        objsource = self.source
        portsource = objsource.getWireSourcePos(self.wire)
        return (objsource.x + portsource[0], objsource.y + portsource[1]) 
    
    def getEndPoint(self):
        objsink = self.sink
        portsink = objsink.getWireSinkPos(self.wire)
        return (objsink.x + portsink[0], objsink.y + portsink[1]) 
    
    def setPath(self, x, y):
        self.x = x
        self.y = y
        
    def draw(self, canvas):
        if (self.x == None):
            return
        
        if (self.routed):
            pass
        else:
            canvas.setForecolor('red')
            canvas.setFillcolor('red')
            
        canvas.setLineWidth(1)
        canvas.drawPolygon(self.x, self.y)
        
        # draw the arrow finishing
        x = self.x[len(self.x)-1]
        y = self.y[len(self.y)-1]
        
        ars = 5
        
        if (self.arrow):
            canvas.drawPolygon([x-ars*2, x, x-ars*2, x-ars*2],[y-ars+1,y+1,y+ars+1, y-ars+1], fill=True)