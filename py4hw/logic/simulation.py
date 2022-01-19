# -*- coding: utf-8 -*-
"""
Created on Wed Jan 19 12:49:00 2022

@author: dcr
"""

from .. import *
from deprecated import deprecated

class Waveform(Logic):

    def __init__(self, parent: Logic, name: str, wires):
        """

        Parameters
        ----------
        parent : Logic
              Parent circuit.
        name : str
            Name of the instance.
        wires
              Wire or list of wire to monitor.

        Returns
        -------
        None.

        """
        super().__init__(parent, name)
        self.waves = {}
        self.prevs = {}
        self.ck = {"name": "CK", "wave": "P"}

        self.wires = wires if isinstance(wires, list) else [wires]
        for x in self.wires:
            self.addIn(x.name, x)
            self.waves[x] = {"name": x.name, "wave": "x", "data": []}
            self.prevs[x] = None

        # Get simulator
        self.sim = parent
        while self.sim.parent != None:
            self.sim = self.sim.parent

        self.sim.getSimulator().addListener(self)

    def simulatorUpdated(self):
        for x in self.wires:
            if self.prevs[x] == x.get():
                self.waves[x]["wave"] += "."
            elif x.getWidth() == 1:
                self.waves[x]["wave"] += str(x.get())
            else:
                self.waves[x]["wave"] += "2"
                self.waves[x]["data"].append(x.get())

            self.prevs[x] = x.get()

        self.ck["wave"] += "."

    def get_waveform(self, with_ck=True):
        signals = list(self.waves.values())
        for x in signals:
            x["wave"] += "x"

        if with_ck:
            ck = self.ck.copy()
            ck["wave"] += "x"
            signals.insert(0, ck)

        waveform = {
            "signal": signals,
            "head": {
                "text": self.name,
                "tock": 0,
            }
        }

        return waveform
    

class Scope(Logic):

    def __init__(self, parent: Logic, name: str, wires):
        """
        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        wires
            Wire or list of wire to monitor.

        Returns
        -------
        None.
        """

        super().__init__(parent, name)
        self.wires = wires if isinstance(wires, list) else [wires]
        for x in self.wires:
            self.addIn(x.name, x)

        # Get simulator
        sim = parent
        while sim.parent != None:
            sim = sim.parent

        sim.getSimulator().addListener(self)

    def simulatorUpdated(self):
        head = f"Scope [{self.name}]:"
        print(head)

        for x in self.wires:
            print(f"{x.name}={x.get()}")

        print("-" * len(head))




class Sequence(Logic):
    """
    A sequence of value
    """

    def __init__(self, parent: Logic, name: str, values: list(), r: Wire):
        super().__init__(parent, name)
        self.r = self.addOut("r", r)

        self.values = values
        self.n = len(values)
        self.i = 0
        
    def clock(self):
        self.r.prepare(self.values[self.i])
        self.i = ( self.i +1 ) % self.n
