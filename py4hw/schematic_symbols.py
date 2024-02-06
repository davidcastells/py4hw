# -*- coding: utf-8 -*-
"""
Created on Fri Jun 18 09:43:48 2021

@author: dcr
"""
from .logic.bitwise import *
from .base import Wire
import math


 
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
    gridsize = 5
    portpitch = 28
    cellmargin = 50
    portSeparation = 10

    namemargin = 8
    portmargin = 8
    instanceportwidth = 4
    instanceportheight = 10
    instanceporttextmargin = 10

    def __init__(self, obj:Logic, x:int, y:int):
        self.obj = obj
        self.x = x
        self.y = y
        self.instanceWidth = self.computeWidth() 
        #print('instance width:', self.instanceWidth)
        
    def getTextExtend(self, text):
        from matplotlib.textpath import TextPath

        fontsize = 12
        
        path = TextPath((0, 0), text, size=fontsize)
        
        text_width = path.get_extents().width
        #text_height = path.get_extents().height
        return text_width

    def getInPortsWidth(self):
        inMaxWidth = 0
        if (hasattr(self.obj, 'inPorts')):
            for idx, port in enumerate(self.obj.inPorts):
                inMaxWidth = max(inMaxWidth, self.getTextExtend(port.name))
        return inMaxWidth
    
    def getOutPortsWidth(self):
        outMaxWidth = 0
        if (hasattr(self.obj, 'outPorts')):
            for idx, port in enumerate(self.obj.outPorts):
                outMaxWidth = max(outMaxWidth, self.getTextExtend(port.name))
        return outMaxWidth
                                
    
    def computeWidth(self):
        outMaxWidth = self.getOutPortsWidth()
        inMaxWidth = self.getInPortsWidth()
        
        return int(outMaxWidth * 1.5  +  LogicSymbol.gridsize*10 + inMaxWidth * 1.5 )

    def getPortSourcePos(self, refport):
        selidx = -1
        for idx, port in enumerate(self.obj.outPorts):
            if (port.name == refport.name):
                selidx = idx
                
        if (selidx == -1):
            raise Exception('out port {} not found in {}'.format(refport.name, self.obj.getFullPath()) )


        return (self.getWidth(), LogicSymbol.namemargin + LogicSymbol.portmargin + selidx*LogicSymbol.portpitch + LogicSymbol.instanceportheight//2)
        
    def getWireSourcePos(self, wire:Wire):
        # TODO remove
        raise Exception('use port one')
        selidx = -1
        for idx, port in enumerate(self.obj.outPorts):
            if (port.wire == wire):
                selidx = idx
                
        if (selidx == -1):
            raise Exception('out port not found in {}'.format(self.obj.getFullPath()) )


        return (self.getWidth(), LogicSymbol.namemargin + LogicSymbol.portmargin + selidx*LogicSymbol.portpitch + LogicSymbol.instanceportheight//2)

    def getPortSinkPos(self, portref):
        selidx = -1
        for idx, port in enumerate(self.obj.inPorts):
            if (port == portref):
                selidx = idx
                
        if (selidx == -1):
            raise Exception('in port not found in {}'.format(self.obj.getFullPath()) )

        
        return (0, LogicSymbol.namemargin + LogicSymbol.portmargin + selidx*LogicSymbol.portpitch + LogicSymbol.instanceportheight//2)
    
    def getWireSinkPos(self, wire:Wire):
        # TODO remove
        raise Exception('use port one')
        selidx = -1
        for idx, port in enumerate(self.obj.inPorts):
            if (port.wire == wire):
                selidx = idx
                
        if (selidx == -1):
            raise Exception('in port not found in {}'.format(self.obj.getFullPath()) )

        
        return (0, LogicSymbol.namemargin + LogicSymbol.portmargin + selidx*LogicSymbol.portpitch + LogicSymbol.instanceportheight//2)

    def getHeight(self):
        return LogicSymbol.namemargin + 2*LogicSymbol.portmargin + max(len(self.obj.inPorts), len(self.obj.outPorts)) * LogicSymbol.portpitch 
    
    def getWidth(self):
        return self.instanceWidth    

    def getOccupancy(self):
        return {'x':self.x, 'y':self.y, 'w':self.getWidth(), 'h':self.getHeight()}

class BinaryOperatorSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        
    def draw(self, canvas, debug=False):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y + LogicSymbol.namemargin

        canvas.drawText(x+25, y+25+5, self.operator, anchor='c')
        canvas.drawEllipse(x, y, x+50, y+50)
        #canvas.drawLine(x, y, x + 40, y)
        #canvas.drawLine(x, y + 40, x + 40, y + 40)
        #canvas.drawLine(x, y, x, y + 40)
        #canvas.drawArc(x + 20, y, x + 50, y + 40, start=-90, extent=180) #, style=tkinter.ARC, outline='black', fill='white')

    def getHeight(self):
        return 50 + LogicSymbol.namemargin

    def getWidth(self):
        return 50 
    
    def gePortSourcePos(self, wire:Wire):
        return (self.getWidth(), LogicSymbol.namemargin + 25)
    
    def getPortSinkPos(self, refport):
        selidx = -1
        for idx, port in enumerate(self.obj.inPorts):
            if (port.name == refport.name):
                selidx = idx
                
        if (selidx == -1):
            raise Exception('in port {} not found in {}'.format(self.obj.getFullPath()) )

        x = int(math.cos(math.pi/4)*25)
        y = int(math.sin(math.pi/4)*25)

        if (selidx == 0):
            y = -y

        return (25-x, LogicSymbol.namemargin + 25 + y)


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

        if (isinstance(obj, And2)):
            self.nins = 2
        else:
            self.nins = len(obj.ins)

        self.h = 20 * self.nins

    def draw(self, canvas, debug=False):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y + LogicSymbol.namemargin

        # the and box would be x[0:50] y[0:30]
        canvas.drawLine(x, y, x + 25, y)
        canvas.drawLine(x, y + self.h, x + 25, y + self.h)
        canvas.drawLine(x, y, x, y + self.h)
        canvas.drawArc(x , y+2, x + 50, y + self.h, start=-90, stop=90) #, style=tkinter.ARC, outline='black', fill='white')

    def getHeight(self):
        return LogicSymbol.namemargin + self.h

    def getWidth(self):
        return 50
    
    def getPortSourcePos(self, refport):
        return (self.getWidth(), LogicSymbol.namemargin + self.h//2)
    
    def getPortSinkPos(self, refport):
        selidx = -1
        inlist = []
        for idx, port in enumerate(self.obj.inPorts):
            inlist.append(port.name)
            if (port.name == refport.name):
                selidx = idx
                
        if (selidx == -1):
            raise Exception('in port {} not found in {}. Object in ports: {}'.format(refport.name, self.obj.getFullPath(), inlist) )

        y = 10 + selidx * 20

        return (5, LogicSymbol.namemargin + y)

class NotSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)

    def draw(self, canvas, debug=False):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y + LogicSymbol.namemargin 

        y = y + 10

        canvas.drawPolygon([x, x + 30, x, x], [y, y + 15, y + 30, y])
        canvas.drawEllipse(x + 30, y + 10, x + 40, y + 20)

    def getHeight(self):
        return 30

    def getWidth(self):
        return 40
    
    def getPortSourcePos(self, port):
        return (self.getWidth(), LogicSymbol.namemargin + 25)
    
    def getPortSinkPos(self, port):
        return (0, LogicSymbol.namemargin + 25)
    
    
class BufSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)

    def draw(self, canvas, debug=False):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y + LogicSymbol.namemargin 

        canvas.drawPolygon([x, x + 20, x, x], [y, y + 10, y + 20, y])
        
    def getHeight(self):
        return 20

    def getWidth(self):
        return 20

    def getWireSourcePos(self, port):
        return (self.getWidth(), LogicSymbol.namemargin + 10)
    
    def getWireSinkPos(self, port):
        return (0, LogicSymbol.namemargin + 10)
    
class BitSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)

    def draw(self, canvas, debug=False):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text='[{}]'.format(self.obj.bit), anchor='w')
        y = y + LogicSymbol.namemargin 

        canvas.drawLine(x+10,y, x, y+20)
        #canvas.drawPolygon([x, x + 20, x, x], [y, y + 10, y + 20, y])
        
    def getHeight(self):
        return 20

    def getWidth(self):
        return 20

    def getPortSourcePos(self, port):
        return (10, LogicSymbol.namemargin + 10)
    
    def getPortSinkPos(self, port):
        return (0, LogicSymbol.namemargin + 10)
    
class RangeSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)

    def draw(self, canvas, debug=False):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text='[{}:{}]'.format(self.obj.high, self.obj.low), anchor='w')
        y = y + LogicSymbol.namemargin 

        canvas.drawLine(x+10,y, x, y+20)
        #canvas.drawPolygon([x, x + 20, x, x], [y, y + 10, y + 20, y])
        
    def getHeight(self):
        return 20

    def getWidth(self):
        return 20

    def getPortSourcePos(self, port):
        return (10, LogicSymbol.namemargin + 10)
    
    def getPortSinkPos(self, port):
        return (0, LogicSymbol.namemargin + 10)
    
class NorSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        self.h = 40

    def draw(self, canvas, debug=False):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y + LogicSymbol.namemargin

        # the and box would be x[0:50] y[0:30]
        canvas.drawLine(x, y, x + 20, y)
        canvas.drawLine(x, y + self.h, x + 20, y + self.h)
        canvas.drawArc(x-10 , y, x + 10, y + self.h, start=-90, extent=90) #, style=tkinter.ARC, outline='black', fill='white')

        #canvas.drawLine(x, y, x, y + self.h)
        canvas.drawArc(x-30 , y, x + 50+20, y + self.h*4, start=-90, extent=-60) #, style=tkinter.ARC, outline='black', fill='white')
        canvas.drawArc(x-30 , y-self.h*3, x + 50+20, y + self.h, start=60, extent=90) #, style=tkinter.ARC, outline='black', fill='white')

        canvas.drawEllipse(x + 55, y + 15, x + 65, y + 25)

    def getHeight(self):
        return LogicSymbol.namemargin + self.h

    def getWidth(self):
        return 65
    
    def getPortSourcePos(self, port):
        return (self.getWidth(), LogicSymbol.namemargin + self.h//2)
    
    def getPortSinkPos(self, refport):
        selidx = -1
        for idx, port in enumerate(self.obj.inPorts):
            if (port.name == refport.name):
                selidx = idx
                
        if (selidx == -1):
            raise Exception('in port not found in {}'.format(self.obj.getFullPath()) )

        if (selidx == 0):
            y = self.h//2 - 10
        else:
            y = self.h//2 + 10 

        return (5, LogicSymbol.namemargin + y)
    
class OrSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        
        if (isinstance(obj, Or2)):
            self.nins = 2
        else:
            self.nins = len(obj.ins)

        self.h = 20 * self.nins
        
    def draw(self, canvas, debug=False):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y + LogicSymbol.namemargin

        # the and box would be x[0:50] y[0:30]
        canvas.drawLine(x, y, x + 20, y)
        canvas.drawLine(x, y + self.h, x + 20, y + self.h)
        canvas.drawArc(x-10 , y, x + 10, y + self.h, start=-90, stop=90) #, style=tkinter.ARC, outline='black', fill='white')

        #canvas.drawLine(x, y, x, y + self.h)
        #canvas.drawArc(x-30 , y, x + 50+20, y + self.h + (self.nins+1)*40, start=-90, extent=-60) #, style=tkinter.ARC, outline='black', fill='white')
        #canvas.drawArc(x-30 , y - (self.nins+1)*40, x + 50+20, y + self.h, start=60, extent=90) #, style=tkinter.ARC, outline='black', fill='white')
        canvas.drawSpline([x+20, x+30, x+42, x+50], [y,  y+2, y+self.h//4, y+self.h//2])
        canvas.drawSpline([x+20, x+30, x+42, x+50], [y+self.h,  y+self.h-2, y+self.h-self.h//4, y+self.h//2])

    def getHeight(self):
        return LogicSymbol.namemargin + self.h

    def getWidth(self):
        return 50
    
    def getPortSourcePos(self, port):
        return (self.getWidth(), LogicSymbol.namemargin + self.h//2)
    
    def getPortSinkPos(self, refport):
        selidx = -1
        for idx, port in enumerate(self.obj.inPorts):
            if (port.name == refport.name):
                selidx = idx
                
        if (selidx == -1):
            raise Exception('in port not found in {}'.format(self.obj.getFullPath()) )

        y = 10 + selidx * 20

        return (5, LogicSymbol.namemargin + y)
    
class XorSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        self.h = 40

    def draw(self, canvas, debug=False):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y + LogicSymbol.namemargin

        # the and box would be x[0:50] y[0:30]
        canvas.drawLine(x+10, y, x + 20+10, y)
        canvas.drawLine(x+10, y + self.h, x + 20+10, y + self.h)
        canvas.drawArc(x-10 , y, x + 10, y + self.h, start=-90, stop=90) #, style=tkinter.ARC, outline='black', fill='white')
        canvas.drawArc(x , y, x + 20, y + self.h, start=-90, stop=90) #, style=tkinter.ARC, outline='black', fill='white')

        #canvas.drawArc(x-30 +10, y, x + 50+20+10, y + self.h*4, start=-90, stop=-60) #, style=tkinter.ARC, outline='black', fill='white')
        #canvas.drawArc(x-30 +10, y-self.h*3, x + 50+20+10, y + self.h, start=60, stop=90) #, style=tkinter.ARC, outline='black', fill='white')
        canvas.drawSpline([x+20+10, x+30+10, x+42+10, x+50+10], [y,  y+2, y+self.h//4, y+self.h//2])
        canvas.drawSpline([x+20+10, x+30+10, x+42+10, x+50+10], [y+self.h,  y+self.h-2, y+self.h-self.h//4, y+self.h//2])



    def getHeight(self):
        return LogicSymbol.namemargin + self.h

    def getWidth(self):
        return 50+10
    
    def getPortSourcePos(self, port):
        return (self.getWidth(), LogicSymbol.namemargin + self.h//2)
    
    def getPortSinkPos(self, refport):
        selidx = -1
        for idx, port in enumerate(self.obj.inPorts):
            if (port.name == refport.name):
                selidx = idx
                
        if (selidx == -1):
            raise Exception('in port not found in {}'.format(self.obj.getFullPath()) )

        if (selidx == 0):
            y = self.h//2 - 10
        else:
            y = self.h//2 + 10 

        return (5, LogicSymbol.namemargin + y)
    
class InPortSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        
    def draw(self, canvas, debug=False):
        x = self.x 
        y = self.y 
        canvas.drawText(x, y, text=self.obj.name , anchor='w')
        y = y+LogicSymbol.namemargin 
        
        canvas.drawPolygon([x, x+10, x+15, x+10,x,x], [y, y, y+5, y+10, y+10, y])

    def getWidth(self):
        return 15;
    
    def getHeight(self):
        return 20;
    
    def getPortSourcePos(self, port):
        return (self.getWidth(), LogicSymbol.namemargin +5)
    
class OutPortSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        
    def draw(self, canvas, debug=False):
        x = self.x 
        y = self.y 
        canvas.drawText(x, y, text=self.obj.name , anchor='w')
        y = y+LogicSymbol.namemargin 
        
        canvas.drawPolygon([x, x+10, x+15, x+10, x, x], [y, y, y+5, y+10, y+10, y])

    def getWidth(self):
        return 15;
    
    def getHeight(self):
        return 20;
    
    def getPortSinkPos(self, port):
        return (0, LogicSymbol.namemargin + 5)

class InOutPortSymbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        
    def draw(self, canvas, debug=False):
        x = self.x 
        y = self.y 
        canvas.drawText(x, y, text=self.obj.name , anchor='w')
        y = y+LogicSymbol.namemargin 
        
        canvas.drawPolygon([x, x+5, x+10, x+15, x+10, x+5, x], [y+5, y, y, y+5, y+10, y+10, y+5])

    def getWidth(self):
        return 20;
    
    def getHeight(self):
        return 20;
    
    def getPortSinkPos(self, port):
        return (0, LogicSymbol.namemargin + 5)
    
    def getPortSourcePos(self, port):
        return (self.getWidth(), LogicSymbol.namemargin +5)

    
class InstanceSymbol(LogicSymbol):
    def __init__(self, obj:Logic, x:int, y:int):
        super().__init__(obj, x, y)
    
    def draw(self, canvas, debug=False):
        x = self.x 
        y = self.y 
        
        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y + LogicSymbol.namemargin 
        
        #print('instance symbol width:', self.getWidth())
        canvas.drawRectangle(x, y, x + self.getWidth(), y + self.getHeight() - LogicSymbol.namemargin)

        ipw = LogicSymbol.instanceportwidth 
        iph = LogicSymbol.instanceportheight
        iphh = iph//2
        iptm = LogicSymbol.instanceporttextmargin

        y = y + LogicSymbol.portmargin
        
        for inp in self.obj.inPorts:
            canvas.drawPolygon([x, x+ipw, x+ipw+iphh, x+ipw, x,x], [y, y, y+iphh, y+iph, y+iph,y])
            canvas.drawText(x+ipw+iph, y+iptm, text=inp.name , anchor='w')
            y = y+LogicSymbol.portpitch
            
        y = self.y + LogicSymbol.namemargin + LogicSymbol.portmargin
        

        for inp in self.obj.outPorts:
            x = self.x + self.getWidth() - ipw - iphh 
            canvas.drawPolygon([x, x+ipw, x+ipw+iphh, x+ipw, x, x], [y, y, y+iphh, y+iph, y+iph, y])
            x = self.x + self.getWidth() - ipw - iph -iphh
            canvas.drawText(x, y+iptm, text=inp.name , anchor='e')
            y = y+LogicSymbol.portpitch

        for inp in self.obj.inOutPorts:
            x = self.x + self.getWidth() - ipw - iphh 
            canvas.drawPolygon([x, x+ipw, x+ipw+iphh, x+ipw, x, x], [y, y, y+iphh, y+iph, y+iph, y])
            x = self.x + self.getWidth() - ipw - iph -iphh
            canvas.drawText(x, y+iptm, text=inp.name , anchor='e')
            y = y+LogicSymbol.portpitch
        
        
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
    
    def draw(self, canvas, debug=False):
        x = self.x 
        y = self.y 
        
        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y+LogicSymbol.namemargin 

        canvas.setFillcolor('lightsalmon')
        canvas.drawRectangle(x, y, x + self.getWidth(), y + self.getHeight() - LogicSymbol.namemargin, fill=True)

        ipw = LogicSymbol.instanceportwidth 
        iph = LogicSymbol.instanceportheight
        iphh = iph//2
        iptm = LogicSymbol.instanceporttextmargin

        y = y + LogicSymbol.portmargin
        
        for inp in self.obj.inPorts:
            canvas.drawPolygon([x, x+ipw, x+ipw+iphh, x+ipw, x,x], [y, y, y+iphh, y+iph, y+iph,y])
            #canvas.drawText(x+ipw+iph, y+iptm, text=inp.name , anchor='w')
            y = y+LogicSymbol.portpitch
            
        y = self.y + LogicSymbol.namemargin + LogicSymbol.portmargin
        
        canvas.setFillcolor('white')
        canvas.drawRoundRectangle(x+25, y+20, x+self.getWidth()-25, y-20+self.getHeight()-LogicSymbol.namemargin-20, radius=10, fill=True)
        
class Mux2Symbol(LogicSymbol):
    def __init__(self, obj, x, y):
        super().__init__(obj, x, y)
        self.h = 20*3

    def draw(self, canvas, debug=False):
        x = self.x
        y = self.y

        canvas.drawText(x, y, text=self.obj.name, anchor='w')
        y = y + LogicSymbol.namemargin

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
        return LogicSymbol.namemargin + self.h

    def getWidth(self):
        return 20
    
    def getPortSourcePos(self, port):
        return (self.getWidth(), LogicSymbol.namemargin + 40)
    
    def getPortSinkPos(self, refport):
        selidx = -1
        for idx, port in enumerate(self.obj.inPorts):
            if (port.name == refport.name):
                selidx = idx
                
        if (selidx == -1):
            raise Exception('in port not found in {}'.format(self.obj.getFullPath()) )

        if (selidx == 0):
            y = 10
        elif (selidx == 1):
            y = 30 
        else:
            y = 50 

        return (0, LogicSymbol.namemargin + y)

class PassthroughSymbol(LogicSymbol):
    def __init__(self):
        super().__init__(None, 0, 0)
        
    def getHeight(self):
        return 30
    
    def getWidth(self):
        return 30
    
    def draw(self, canvas, debug=False):
        x = self.x
        y = self.y

        if (debug):       
            canvas.setFillcolor('yellow')  
            canvas.drawRectangle(x, y, x+30, y+30, fill=True)
        else:
            canvas.setForecolor('blueviolet')  
            canvas.setLineWidth(1)
            
            canvas.drawLine(x, y+15, x+30, y+15)
    
            canvas.setForecolor('k')  
            canvas.setLineWidth(2)
        
    def getPortSinkPos(self, port):
        return (0, 15);
    
    def getPortSourcePos(self, port):
        return (30, 15);
    
class FeedbackStartSymbol(LogicSymbol):
    def __init__(self):
        super().__init__(None, 0, 0)
        
    def getHeight(self):
        return 30
    
    def getWidth(self):
        return 30
    
    def draw(self, canvas, debug=False):
        x = self.x
        y = self.y

        if (debug):       
            canvas.setFillcolor('lightgreen')  
            canvas.drawRectangle(x, y, x+30, y+30, fill=True)
        else:            
            # canvas.setForecolor('red')  
            # canvas.setLineWidth(1)
            
            # canvas.drawLine(x, y+15, x+30, y+15)
        
            # canvas.setForecolor('k')  
            # canvas.setLineWidth(2)
            pass
        
    def getPortSinkPos(self, port):
        return (0, 15);
    
    def getPortSourcePos(self, port):
        return (30, 15);
    
class FeedbackStopSymbol(LogicSymbol):
    def __init__(self):
        super().__init__(None, 0, 0)
        self.debug = False
        
    def getHeight(self):
        return 30
    
    def getWidth(self):
        return 30
    
    def draw(self, canvas, debug=False):
        x = self.x
        y = self.y

        if (debug):       
            canvas.setFillcolor('red')  
            canvas.drawRectangle(x, y, x+30, y+30, fill=True)
        else:
            # canvas.setForecolor('red')  
            # canvas.setLineWidth(1)
            
            # #canvas.drawRectangle(x, y, x+30, y+30)
            # canvas.drawLine(x, y+15, x+30, y+15)
    
            # canvas.setForecolor('k')  
            # canvas.setLineWidth(2)
            pass
        
    def getPortSinkPos(self, port):
        return (0, 15);
    
    def getPortSourcePos(self, port):
        return (30, 15);
    
    
class NetSymbol:
    def __init__(self, wire:Wire, sourcePort, sinkPort, source:LogicSymbol, sink:LogicSymbol):
        """
        A net symbol connects two entities.

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
        self.sourcePort = sourcePort
        self.sinkPort = sinkPort
        self.source = source
        self.sink = sink
        self.x = None
        self.y = None
        self.routed = False
        self.arrow = True
        self.color = 'blueviolet'
        self.sourcecol = -1
        # self.sinkcol will be assigned later
        
    def getStartPoint(self):
        objsource = self.source
        portsource = objsource.getPortSourcePos(self.sourcePort)
        return (objsource.x + portsource[0], objsource.y + portsource[1]) 
    
    def getEndPoint(self):
        objsink = self.sink
        portsink = objsink.getPortSinkPos(self.sinkPort)
        return (objsink.x + portsink[0], objsink.y + portsink[1]) 
    
    def setPath(self, x, y):
        self.x = x
        self.y = y
        
    def draw(self, canvas, debug=False):
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