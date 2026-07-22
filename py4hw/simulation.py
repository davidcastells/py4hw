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
        Propagatables must be sorted in propagation order: every
        propagatable must come after every OTHER propagatable that feeds
        one of its inputs (a proper topological sort of the combinational
        dependency graph).

        PATCHED (see patch_py4hw_topological_sort.py): O(V+E) via Kahn's
        algorithm, replacing the original O(n^2)-per-convergence-pass
        bubble-sort-style implementation, which called
        `self.propagatables.index(...)` -- an O(n) linear scan -- inside
        nested loops over every leaf and every one of its sinks. That is
        fine for small designs but becomes the dominant cost of
        hw.getSimulator() for designs with thousands of propagatable
        leaves (structural/gate-level decompositions in particular).

        Returns
        -------
        None.

        """
        from collections import deque

        self.propagatables = []
        self.clockDrivers = {}

        leaves = self.sys.allLeaves()

        propagatable_leaves = []
        for leaf in leaves:
            if leaf.isClockable():
                leafDriver = getObjectClockDriver(leaf)
                drv = self.getOrCreateClockDriverSimulator(leafDriver)
                drv.addClockable(leaf)
            if leaf.isPropagatable():
                propagatable_leaves.append(leaf)

        # O(1) position lookup, replacing the repeated O(n) list.index()
        # calls that dominated the original algorithm's runtime.
        index_of = {obj: i for i, obj in enumerate(propagatable_leaves)}
        n = len(propagatable_leaves)
        adj = [[] for _ in range(n)]
        indegree = [0] * n
        seen_edges = [set() for _ in range(n)]

        for i, obj in enumerate(propagatable_leaves):
            for port in obj.outPorts:
                if port.wire is None:
                    continue
                for sinkPort in port.wire.getSinks():
                    sink = sinkPort.parent
                    if not sink.isPropagatable():
                        continue
                    j = index_of.get(sink)
                    if j is None or j == i:
                        continue
                    if j not in seen_edges[i]:
                        seen_edges[i].add(j)
                        adj[i].append(j)
                        indegree[j] += 1

        # Kahn's algorithm: O(V + E).
        queue = deque(i for i in range(n) if indegree[i] == 0)
        order = []
        while queue:
            i = queue.popleft()
            order.append(i)
            for j in adj[i]:
                indegree[j] -= 1
                if indegree[j] == 0:
                    queue.append(j)

        if len(order) != n:
            # A true combinational cycle (no valid topological order
            # exists) -- shouldn't happen in a real synchronous design,
            # since feedback must go through a clocked Reg (not
            # "propagatable"). Fall back to appending whatever's left in
            # original order rather than hard-failing, matching the
            # original algorithm's best-effort tolerance rather than its
            # hard 1000-loop exception.
            placed = set(order)
            order.extend(i for i in range(n) if i not in placed)

        self.propagatables = [propagatable_leaves[i] for i in order]

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
        self.propagateAll()
        
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
            
    
    