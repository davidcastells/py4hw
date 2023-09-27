from .base import HWSystem
from .base import Wire
from .base import Logic
from .base import ClockDriver
from .base import getObjectClockDriver
from .logic.simulation import Waveform

class ClockDriverSimulator:
    """
    The simulation is organized by clock drivers
    """
    
    def __init__(self, drv:ClockDriver):
        self.driver = drv
        self.clockables = []
        
    def addClockable(self, obj:Logic):
        self.clockables.append(obj)

    def clockAll(self):
        for obj in self.clockables:
            obj.clock()



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
        self.total_clks = 0
        
        if sys.simulator != None:
            return

        self.sys = sys;

        
        self.topologicalSort()
        self.listeners = []

        self.propagateAll()
    
    def propagateAll(self):
        for obj in self.propagatables:
            obj.propagate();

    def __new__(cls, sys:HWSystem):
        if sys.simulator != None:
            sys.simulator.topologicalSort() # Updates existing simulator
            return sys.simulator
        else:
            return super().__new__(cls)

        
    def topologicalSort(self):
        """
        We segment the circuit by clock drivers.
        
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

        self.propagatables = []
        self.clockDrivers = {}
        
        leaves = self.sys.allLeaves()
        
        for leaf in leaves:
            
            if (leaf.isClockable()):
                leafDriver = getObjectClockDriver(leaf)
                drv = self.getOrCreateClockDriverSimulator(leafDriver)
                drv.addClockable(leaf)

            if (leaf.isPropagatable()):
                self.propagatables.append(leaf)
                
        # Now sort the propagatables list
        anyChange = True 
        
        loopcount = 0
        
        while (anyChange):
            loopcount += 1
            anyChange = False
            
            if (loopcount > 1000):
                raise Exception('Excessive loop count in topological count')
                
            for i in range(len(self.propagatables)):
                leaf = self.propagatables[i]
                pos = self.findFirstDependentPosition(leaf)
                
                if (pos >= 0 and pos < i):
                    # exchange position, put dependent last
                    first = self.propagatables[pos]
                    self.propagatables[pos] = leaf
                    self.propagatables[i] = first
                    anyChange = True
        
    
        
    def getOrCreateClockDriverSimulator(self, drv:ClockDriver) -> ClockDriverSimulator:
        try:
            return self.clockDrivers[drv]
        except:
            self.clockDrivers[drv] = ClockDriverSimulator(drv)
            return self.clockDrivers[drv]
            
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
            if (port.wire is None):
                #raise Exception('Unconnected wire to {}'.format(port.getFullPath()))
                # skip unconnected ports
                continue
            
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
        
    def clk(self, cycles:int=1):
        """
        Advance a number of clock cycles

        Parameters
        ----------
        cycles : int
            Number of clock cycles.

        Returns
        -------
        None.

        """
        self.do_run = True
        for i in range(cycles):
            if not(self.do_run):
                # simulation was cancelled by stop
                return
            
            self._clk_cycle();
            
            
    def _clk_cycle(self):
        """
        Advance one clock cycle

        Returns
        -------
        None.

        """
        for drv in self.clockDrivers:
            if (not(drv.enable is None)):
                if (drv.enable.get() == 0):
                    continue;
                    
            self.clockDrivers[drv].clockAll()
            
        Wire.settleAll()
                
        for obj in self.propagatables:
            obj.propagate();
            
        self._notifyListeners()
        self.total_clks += 1

    def stop(self):
        self.do_run = False
           
    def addListener(self, listener):
        self.listeners.append(listener)
        
    def _notifyListeners(self):
        for listener in self.listeners:
            listener.simulatorUpdated()
            
    
    