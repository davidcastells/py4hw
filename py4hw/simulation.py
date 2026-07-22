from .base import HWSystem
from .base import Wire
from .base import Logic
from .base import ClockDriver
from .base import getObjectClockDriver
from .logic.simulation import Waveform

# =============================================================================
# PATCHED (see patch_py4hw_incremental_propagate.py): detects propagate()
# methods that keep state across calls (e.g. for edge detection), which
# violates the "pure function of current inputs" assumption incremental
# propagation depends on. Instances of such classes are always fully
# re-evaluated by the patched Simulator.propagateAll() above, regardless
# of dirty-wire tracking.
# =============================================================================
import ast as _incremental_ast
import inspect as _incremental_inspect

_incremental_impure_class_cache = {}


def _incremental_propagate_is_impure(cls):
    if cls in _incremental_impure_class_cache:
        return _incremental_impure_class_cache[cls]

    impure = False
    try:
        src = _incremental_inspect.getsource(cls.propagate)
        src = 'if True:\n' + src
        tree = _incremental_ast.parse(src)
        for node in _incremental_ast.walk(tree):
            if isinstance(node, _incremental_ast.Assign):
                for target in node.targets:
                    if (isinstance(target, _incremental_ast.Attribute)
                            and isinstance(target.value, _incremental_ast.Name)
                            and target.value.id == 'self'):
                        impure = True
                        break
            elif isinstance(node, _incremental_ast.AugAssign):
                if (isinstance(node.target, _incremental_ast.Attribute)
                        and isinstance(node.target.value, _incremental_ast.Name)
                        and node.target.value.id == 'self'):
                    impure = True
            if impure:
                break
    except (OSError, TypeError):
        impure = True

    _incremental_impure_class_cache[cls] = impure
    return impure


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
        """
        PATCHED (see patch_py4hw_incremental_propagate.py): event-driven
        ("dirty wire") propagation instead of an unconditional full scan.
        The first call (from __init__) still does one full pass, to
        establish correct initial values -- every call after that only
        re-.propagate()s leaves transitively downstream of a wire in
        Wire.dirty, processed in self.propagatables' existing
        topological order (so a single forward pass is sufficient: newly
        -dirtied output wires found partway through always belong to
        leaves later in that same order). Classes whose propagate()
        keeps state across calls (detected once via source inspection,
        see _incremental_propagate_is_impure below) are always fully
        re-evaluated, matching the original behavior for them exactly.
        """
        from .base import Wire

        if not getattr(self, '_incremental_ready', False):
            for obj in self.propagatables:
                obj.propagate()
            Wire.dirty.clear()
            self._incremental_ready = True
            self._propagatable_set = set(self.propagatables)
            self._always_eval = {obj for obj in self.propagatables
                                  if _incremental_propagate_is_impure(type(obj))}
            return

        dirty = Wire.dirty
        if not dirty and not self._always_eval:
            return
        Wire.dirty = set()

        prop_set = self._propagatable_set
        needs_eval = set(self._always_eval)
        for w in dirty:
            for sink_port in w.sinks:
                comp = sink_port.parent
                if comp in prop_set:
                    needs_eval.add(comp)

        for obj in self.propagatables:
            if obj not in needs_eval:
                continue
            obj.propagate()
            for port in obj.outPorts:
                w = port.wire
                if w is not None and w in Wire.dirty:
                    for sink_port in w.sinks:
                        comp2 = sink_port.parent
                        if comp2 in prop_set:
                            needs_eval.add(comp2)

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

        # PATCHED (see patch_py4hw_incremental_propagate.py): was an
        # unconditional `for obj in self.propagatables: obj.propagate()`
        # here, duplicating (and bypassing) the incremental logic in
        # propagateAll() above. Routing through self.propagateAll()
        # instead means both call sites in clk() (the explicit one at
        # its top and this one) get the same dirty-wire-only benefit.
        self.propagateAll()
            
        self._notifyListeners()
        self.total_clks += 1

    def stop(self):
        self.do_run = False
           
    def addListener(self, listener):
        self.listeners.append(listener)
        
    def _notifyListeners(self):
        for listener in self.listeners:
            listener.simulatorUpdated()
            
    
    