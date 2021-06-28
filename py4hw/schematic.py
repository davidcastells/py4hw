# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 18:59:19 2021

@author: dcr
"""
import matplotlib.pyplot as plt
import numpy as np
        
from matplotlib.lines import Line2D
from matplotlib.patches import *
from .base import Logic
from .logic import *
from .storage import *
from .schematic_symbols import *

gridsize = 5
cellmargin = 20


class MatplotlibRender:
    def __init__(self):
        f = plt.figure(figsize=(16,16))
        self.canvas = f.add_subplot()
        self.canvas.set_xlim(0, 1440)
        self.canvas.set_ylim(0, 1440)
        self.canvas.invert_yaxis()
        plt.axis('off')
        
        self.color = 'k'
        self.linewidth = 2
        
    def setForecolor(self, color):
        self.color = color
        
    def setFillcolor(self, color):
        self.fillcolor = color
        
    def setLineWidth(self, w):
        self.linewidth = w
        
    def drawText(self, x, y, text, anchor):
        """
        

        Parameters
        ----------
        x : TYPE
            DESCRIPTION.
        y : TYPE
            position of the lower part of the text bounding box
        text : TYPE
            DESCRIPTION.
        anchor : TYPE
            e for east, w for west, c for center.

        Returns
        -------
        None.

        """
        if (anchor == 'w'):
            ha = 'left'
        elif (anchor == 'e'):
            ha = 'right'
        elif (anchor == 'c'):
            ha = 'center'
            
        self.canvas.annotate(text, (x, y), horizontalalignment=ha)
        
    def drawPolygon(self, x, y, fill=False):
        
        lines = Line2D(x,y, color=self.color, linewidth=self.linewidth)

        if (fill):
            self.canvas.fill(x, y, self.fillcolor)

        self.canvas.add_line(lines)

    def drawLine(self, x0, y0, x1, y1):
        self.drawPolygon([x0, x1], [y0, y1])
        
    def drawRectangle(self , x0, y0, x1, y1, fill=False):
        #print('rect', x0, y0, x1, y1)
        self.drawPolygon([x0, x1, x1, x0, x0],[y0,y0, y1,y1, y0], fill)
        
    def drawRoundRectangle(self, x0, y0, x1, y1, radius=5, fill=False):
        box = FancyBboxPatch((x0,y0), width=x1-x0, height=y1-y0,
              boxstyle=BoxStyle("Round", pad=radius), facecolor=self.fillcolor)
        self.canvas.add_patch(box)
        
    def drawArc(self, x0, y0, x1, y1, start, extent):
        arc = Arc(((x0+x1)//2, (y0+y1)//2), x1-x0, y1-y0, angle=0, theta1=start, theta2=extent, linewidth=self.linewidth)
        self.canvas.add_patch(arc)

    def drawEllipse (self, x0, y0, x1, y1, outline=None, fill=None):
        el = Ellipse(((x0+x1)/2, (y0+y1)/2), x1-x0, y1-y0, edgecolor=self.color, facecolor='none', linewidth=self.linewidth)
        self.canvas.add_artist(el)
        
class Schematic:
    
    
    def __init__(self, sys:Logic):
   
        if (len(sys.children) == 0):
            raise Exception('Schematics are only available to structural circuits')

        self.sys = sys
        self.x = 0
        self.y = 0
                
        # frame=Frame(root,width=640,height=480)
        # self.frame =frame
        # frame.pack(expand=True, fill=BOTH) #.grid(row=0,column=0)
        # canvas=Canvas(frame,bg='#FFFFFF',width=300,height=900,scrollregion=(0,0,500,900))
        
        self.canvas = MatplotlibRender()
        
        self.canvas.setForecolor('k')
        # hbar=Scrollbar(frame,orient=HORIZONTAL)
        # hbar.pack(side=BOTTOM,fill=X)
        # hbar.config(command=canvas.xview)
        # vbar=Scrollbar(frame,orient=VERTICAL)
        # vbar.pack(side=RIGHT,fill=Y)
        # vbar.config(command=canvas.yview)
        # canvas.config(width=300,height=900)
        # canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        # canvas.pack(side=LEFT,expand=True,fill=BOTH)

        self.objs = []      # a list of the objects displayed
        self.sources = []   # a list of net sources with tuples [symbol, x, y, wire]
        self.sinks = []     # a list of net sinks with tuples   [symbol, x, y, wire]
        
        self.mapping = {}
        self.mapping[And] = AndSymbol
        self.mapping[Not] = NotSymbol
        self.mapping[Or] = OrSymbol
        self.mapping[Add] = AddSymbol
        self.mapping[Sub] = SubSymbol
        self.mapping[Reg] = RegSymbol
        self.mapping[Scope] = ScopeSymbol
        self.mapping[Buf] = BufSymbol
        
        
        self.placeInputPorts()
        self.placeInstances()
        self.placeOutputPorts()

        self.bruteForceSort()
        self.replaceByAdjacencyMatrix()
        
        # self.replaceByDependency()
        
        self.replaceVerticalCompress()
        # #self.replaceHorizontalCompress()
        
        self.createNets()
        self.routeNets()
        
        
        self.drawAll()
        
        #mainloop()
        
    def replaceByAdjacencyMatrix(self):
        am = self.getAdjacencyMatrix()
        
        x = 0
        y = 0
        
        for i in range(am.shape[0]):
            obj = self.objs[i]
            
            srcs = am[0:i,i]
            if (i == 0 or np.max(srcs) == 0):
                # no source
                obj.x = x
                obj.y = y
                y = y + obj.getHeight() + cellmargin

            else:
                lastsrc_aux = np.where(srcs>0) # more recent source
                pos = len(lastsrc_aux[0])
                lastsrc = lastsrc_aux[0][pos-1]
                
                dep = self.objs[lastsrc]
                obj.x = dep.x + dep.getWidth() + cellmargin
                obj.y = y
                x = obj.x
                y = y + obj.getHeight() + cellmargin
                
            
        
    def replaceVerticalCompress(self):
        """
        Compress instances in the vertical axis, 
        avoiding unused space above

        Returns
        -------
        None.

        """
        grid = self.getOccupancyGrid()
        
        for obj in self.objs:
            # get the occupancy area of this block
            rect = obj.getOccupancy()

            minfree = -1            
            # check if if has free space above in the occupancy grid
            for y in range(rect['y'], (gridsize * 3)-1, -1):
                candidate = grid[y:y+rect['h'],rect['x']:rect['x']+rect['w']]

                if (candidate.shape[0]==0 or candidate.shape[1]==0):
                    #print('y',y,'skip obj', candidate.shape, obj)
                    pass
                elif (np.max(candidate) == 0):
                    minfree = y
                    
            # if so, move it as much as possible
            if (minfree >= 0):
                obj.y = minfree
                
            # compute the occupancy grid again
            grid = self.getOccupancyGrid()
            
    def replaceHorizontalCompress(self):
        """
        Compress instances in the vertical axis, 
        avoiding unused space above

        Returns
        -------
        None.

        """
        grid = self.getOccupancyGrid()
        
        for obj in self.objs:
            # get the occupancy area of this block
            rect = obj.getOccupancy()

            minfree = -1            
            # check if if has free space to the left in the occupancy grid
            for x in range(rect['x'], (gridsize * 3)-1, -1):
                candidate = grid[rect['y']:rect['y']+rect['h'],x:x+rect['w']]

                if (candidate.shape[0]==0 or candidate.shape[1]==0):
                    #print('y',y,'skip obj', candidate.shape, obj)
                    pass
                elif (np.max(candidate) == 0):
                    minfree = x
                    
            # if so, move it as much as possible
            if (minfree >= 0):
                obj.x = minfree
                
            # compute the occupancy grid again
            grid = self.getOccupancyGrid()
        
    def replaceByDependency(self):
        """
        do topological sort, start from sources
        and place sinks be in the right

        Returns
        -------
        None.

        """
        #grid = [[0] * self.grid_xunits] * self.grid_yunits
        
        changed = True
        iterNum = 0
        
        while (changed and iterNum < 2):
            iterNum = iterNum + 1
            changed = False
            for sourceTuple in self.sources:
                sinks = self.findSinkTuples(sourceTuple['wire'])
                sourceObj = sourceTuple['symbol']
                
                
                for sinkTuple in sinks:
                    sinkObj = sinkTuple['symbol']
                    candidatex = sourceObj.x + sourceObj.getWidth() + cellmargin
    
                    
                
                    # check if A -> B, B-> A happens
                    directCount = self.countNetsBetweenSymbols(sourceObj, sinkObj)
                    reverseCount = self.countNetsBetweenSymbols(sinkObj, sourceObj)
                    
                    
                    
                    #if (isinstance(sourceObj, Logic )):
                    #    print(sourceObj.obj.getFullPath())
                    
                    if (candidatex > sinkObj.x and directCount > reverseCount):
                        print('moving to',candidatex + cellmargin, sinkObj.obj.name, 'sink of', sourceObj.obj.name, '({}/{})'.format(directCount, reverseCount))
                        #print('Source Obj:', sourceObj.obj.name)
                        #print('Sink Obj:', sinkObj.obj.name)
                        #print('direct', directCount, 'reverse', reverseCount)
                        sinkObj.x = candidatex + cellmargin
                        changed = True
                
        
    def countNetsBetweenSymbols(self, sourceSym, sinkSym):
        wiresFromSource = [source['wire'] for source in self.sources if source['symbol'] == sourceSym]
        wiresToSink = [sink['wire'] for sink in self.sinks if sink['symbol'] == sinkSym]
        common = [wire for wire in wiresFromSource if wire in wiresToSink ]
        return len(common)
    
    def placeInputPorts(self):
        """
        Place the input ports of the module 

        Returns
        -------
        None.

        """
        self.x = gridsize
        self.y = gridsize * 5
        
        for inp in self.sys.inPorts:
            isym = InPortSymbol(inp, self.x, self.y)
            self.objs.append(isym)
            self.y = self.y + gridsize * portSeparation
            self.sources.append({'symbol':isym, 'x':15, 'y':8+5, 'wire':inp.wire})
        
        if (len(self.sys.inPorts) > 0):
            self.x = self.x + 25 * gridsize
            
        # g = genGraph(self.sources)
        # g.add_edge(self.sources)
        # print("Executed")
        # g.col_assignment()
        # g.print_graph()
        self.numInputs = len(self.objs)
        
    def getSymbol(self, obj, x, y):
        try:
            ret = self.mapping[type(obj)]
    
            print('getSymbol -> good', obj)
                
        except:
            print('getSymbol -> none for object', type(obj))
            return None

        return ret(obj, x, y)
        

    def placeInstances(self):
        maxx = 0
        self.y = gridsize*3
        
        print('placeInstances', self.sys)
        
        for child in self.sys.children:
            print('child', child)
            isym = self.getSymbol(child, self.x, self.y)
            
            if (isym is None):
                isym = InstanceSymbol(child, self.x, self.y)
            
            self.objs.append(isym)
            self.y = self.y + isym.getHeight() + cellmargin * 2 
 
            i = 0
            for inp in child.inPorts:
                print('adding inport ', child, inp.name)
                self.sinks.append({'symbol':isym, 'x':0, 'y':8+8+8+5+i*portpitch, 'wire':inp.wire})
                i = i+1
            i = 0
            for inp in child.outPorts:
                print('adding outport ', child, inp.name)
                self.sources.append({'symbol':isym, 'x':isym.getWidth(), 'y':8+8+8+5+i*portpitch, 'wire':inp.wire})
                i = i+1
                    
    
            maxx = max(maxx, isym.getWidth())
            
        self.x = self.x + maxx + gridsize*10 + cellmargin
        self.grid_yunits = self.y / gridsize
        self.grid_yunits = self.y / gridsize
        
    def placeOutputPorts(self):
        #self.x = 1
        self.y = gridsize * 5
        
        for inp in self.sys.outPorts:
            osym = OutPortSymbol(inp, self.x, self.y)
            self.objs.append(osym)
            self.y = self.y + gridsize * portSeparation
            self.sinks.append({'symbol':osym, 'x':0, 'y':8+5, 'wire':inp.wire})
        
        #self.x = self.x + 3
        
    def findSourceTuple(self, sinkWire:Wire):
        for source in self.sources:
            if (source['wire'] == sinkWire):
                return source
            
        raise Exception('No source to wire {} in {}'.format(sinkWire.name, self.sources) )
            
    def findSinkTuples(self, sourceWire):
        ret = []
        for sink in self.sinks:
            if (sink['wire'] == sourceWire):
                ret.append(sink)
        return ret;
            
    def createNets(self):
        for sink in self.sinks:
            source = self.findSourceTuple(sink['wire'])
            self.objs.append(NetSymbol(source, sink))   

    def getNets(self):
        oa = np.array(self.objs)
        ba = np.array([isinstance(x, NetSymbol) for x in self.objs])
        return list(oa[ba])
    
    def getNonNets(self):
        oa = np.array(self.objs)
        ba = np.array([not isinstance(x, NetSymbol) for x in self.objs])
        return list(oa[ba])
    
    def drawAll(self):
        for obj in self.objs:
            obj.draw(self.canvas)
        
        return self.canvas
    
    def getAdjacencyMatrix(self):
        """
        

        Returns
        -------
        adjacency matrix : numpy 2D array with the connections between 
            circuit instances

        """
        non_nets = self.getNonNets()
        nc = len(non_nets) # number of circuits
        am = np.zeros((nc, nc), dtype=int) # adjacency matrix
        
        for srcidx in range(nc):
            srcobj = non_nets[srcidx]
            
            for trgidx in range(nc):
                trgobj = non_nets[trgidx]
            
                am[srcidx, trgidx] = self.areSourceTarget(srcobj, trgobj)
            
        
        return am
        
    def computeAdjacencyMatrixCost(self):
        am = self.getAdjacencyMatrix()
        cost = 0
        for y in range(am.shape[0]):
            for x in range(y):
                cost = cost + am[y, x]

        return cost
    
    def swap(self, a, b):
        self.objs[a], self.objs[b] = self.objs[b], self.objs[a] 

    def bruteForceSort(self):
        am = self.getAdjacencyMatrix()
        nc = am.shape[0]


        objs = self.objs.copy()
        cost = self.computeAdjacencyMatrixCost()
        
        for k in range(nc):
            anychange = False
            for i in range(nc):
                for j in range(i, nc):
                    if (i != j):
                        self.swap(i,j)
                        newcost = self.computeAdjacencyMatrixCost()
                        
                        #print('swap', i, j, 'cost=', newcost)

                        if (newcost >= cost):
                            # revert swap
                            self.objs = objs
                        else:
                            objs = self.objs.copy()
                            cost = newcost
                            anychange = True

            print('iter', k, 'cost:', cost, anychange)
                         
            if (not anychange):
                break

        am = self.getAdjacencyMatrix()
        return am

    def areSourceTarget(self, srcobj, trgobj):
        if (isinstance(srcobj, InPortSymbol)):
            outwires = [srcobj.obj.wire]
        elif (isinstance(srcobj, OutPortSymbol)):
            outwires = []
        else:
            outwires = [outport.wire for outport in srcobj.obj.outPorts]
        
        if (isinstance(trgobj, InPortSymbol)):
            inwires = []
        elif (isinstance(trgobj, OutPortSymbol)):
            inwires = [trgobj.obj.wire]
        else:
            inwires = [inport.wire for inport in trgobj.obj.inPorts]
        
        inter = Intersection(inwires, outwires)
        
        #print('Intersection ', srcobj.obj.getFullPath(), trgobj.obj.getFullPath(), '=', len(inter))
        
        return len(inter) 
        
    def getOccupancyGrid(self):
        maxh = 0
        maxw = 0
        
        for obj in self.getNonNets():
            w = obj.x + obj.getWidth() #+ cellmargin
            h = obj.y + obj.getHeight() + cellmargin
            if (w > maxw): maxw = w
            if (h > maxh): maxh = h
            
        grid = np.zeros((maxh,maxw))
        
        for obj in self.getNonNets():
            x = obj.x
            y = obj.y
            w = obj.getWidth() #+ cellmargin
            h = obj.getHeight() + cellmargin
            grid[y:y+h,x:x+w]=1
            
        return grid
    
    def routeNets(self):
        nets = self.getNets()
        
        for net in nets:
            # route net
            p0 = net.getStartPoint()
            pf = net.getEndPoint()
            
            mp = ((p0[0]+pf[0])//2, (p0[1]+pf[1])//2)
            
            net.setPath([p0[0], mp[0], mp[0], pf[0]], [p0[1],p0[1],pf[1],pf[1]])
                        

        # for inp in self.obj.outPorts:
        #     canvas.create_text(x+15-2, y, text=inp.name , anchor='e')
        #     y = y+8
        #     canvas.create_polygon(x, y, x+10, y, x+15, y+5, x+10, y+10, x, y+10)
        #     y = y+portpitch-8
        
        
    def getHeight(self):
        return max(len(self.obj.inPorts), len(self.obj.outPorts)) * portpitch + cellmargin * 2
    
    def getWidth(self):
        return 25 * gridsize

class AdjNode:
    def __init__(self, data):
        self.vertex = data
        self.next = None

# Generate graphs based on the ports and nets

rows,cols = (gridsize,gridsize)
matrix = [[0]*cols]*rows

class genGraph:

    def __init__(self,sources):
        self.V = len(sources)
        self.graph = [None]*self.V

    def add_edge(self,sources):
        for i in range(len(sources)-1):
            for j in range(i+1,len(sources)):
                if sources[j].parent == sources[i]:
                    node = AdjNode(sources[j])
                    node.next = self.graph[sources[i]]
                    self.graph[sources[i]] = next

    def print_graph(self):
        for i in range(self.V):
            print("Adjacency list of vertex {}\n head".format(i), end="")
            temp = self.graph[i]
            while temp:
                print(" -> {}".format(temp.vertex), end="")
                temp = temp.next
            print(" \n")
    
    def col_assignment(self):
        for i in range(self.V):
            k=0
            if(self.graph[i].isPrimitive()):
                matrix[0][k] = self.graph[i]
                k+=1
            else:
                matrix[self.graph[i].col][self.graph[i].row+1] = self.graph[i]

    def row_assignment(self):
        
        for i in range(self.V):
            for j in range(matrix.size()):
                count = 0
                count = matrix[j].size()
                for k in range(count):
                    matrix[k][0] = self.graph[i]


    def crossover_calc(self,matrix):
        
        numCross = 0
        
        for i in range(cols-1):
            for j in range(cols):
                for k in range(rows-1):
                    for l in range(rows):
                         numCross += Matrix[j][k]*Matrix[i][l]
        
        return numCross



def Intersection(lst1, lst2):
    return set(lst1).intersection(lst2)
