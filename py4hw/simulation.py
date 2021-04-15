from .base import HWSystem
from .base import Wire
from .base import Logic

class Simulator:

    def __init__(self, sys:HWSystem):
        """
        Simulator Construction

        Parameters
        ----------
        sys : HWSystem
            Hardware system to simulate.

        Returns
        -------
        None.

        """
        self.sys = sys;
        
        self.topologicalSort()
        self.listeners = []
        
        for obj in self.propagatables:
            obj.propagate();
        

        
    def topologicalSort(self):
        """
        Sorts all the elements of the circuit so that cycle-base 
        simlation is possible.
        
        Clockables do not require any order.
        Propagatables must be sorted in propagation order, so when we insert
        we should check if there are elements in the list that depend on 
        the current item, and in this case we should place it before them

        Returns
        -------
        None.

        """
        
        self.clockables = []
        self.propagatables = []
       
        leaves = self.sys.allLeaves()
        
        for leaf in leaves:
            if (leaf.isClockable()):
                self.clockables.append(leaf)
            if (leaf.isPropagatable()):
                self.propagatables.append(leaf)
                
        # Now sort the propagatables list
        anyChange = True 
        
        while (anyChange):
            anyChange = False
            for i in range(len(self.propagatables)):
                leaf = self.propagatables[i]
                pos = self.findFirstDependentPosition(leaf)
                
                if (pos >= 0 and pos < i):
                    # exchange position, put dependent last
                    first = self.propagatables[pos]
                    self.propagatables[pos] = leaf
                    self.propagatables[i] = first
                    anyChange = True
        
    def findFirstDependentPosition(self, obj:Logic) -> int:
        """
        We look at the outputs of the provided circuit and find
        all the dependent cells, then we locate them in 

        Parameters
        ----------
        obj : Logic
            DESCRIPTION.

        Returns
        -------
        the position of the first dependent circuit in the propagatables list

        """
        
        sinks = []
        
        for port in obj.outPorts:
            sinkPorts = port.wire.getSinks()
            
            for sinkPort in sinkPorts:
                sink = sinkPort.parent

                if (sink.isPropagatable()):
                    sinks.append(sink)
        
        if (len(sinks) == 0):
            return -1;
        
        minPos = self.propagatables.index(sinks[0])
        
        for i in range(len(sinks)):
            pos = self.propagatables.index(sinks[i])
            if (pos < minPos):
                minPos = pos
                
        return minPos
        
    def clk(self, cycles:int):
        """
        Advance a number of clock cycles

        Parameters
        ----------
        cycles : int
            DESCRIPTION.

        Returns
        -------
        None.

        """
        for i in range(cycles):
            self._clk_cycle();
            
            
    def _clk_cycle(self):
        """
        Advance one clock cycle

        Returns
        -------
        None.

        """
        for obj in self.clockables:
            obj.clock()
            
        Wire.settleAll()
                
        for obj in self.propagatables:
            obj.propagate();
            
        self._notifyListeners()
            
    def addListener(self, listener):
        self.listeners.append(listener)
        
    def _notifyListeners(self):
        for listener in self.listeners:
            listener.simulatorUpdated()