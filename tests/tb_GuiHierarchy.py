# -*- coding: utf-8 -*-
# @Time    : 2020/4/2 11:32
# @Author  : 富贵
# @FileName: 简单商店应用程序.py
from py4hw.base import *
from py4hw.logic import *
from py4hw.storage import *
from py4hw.simulation import Simulator
import py4hw.debug


class SerialAdder(Logic):
    def __init__(self, parent:Logic, name:str, a:Wire, r:Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.r = self.addOut("r", r)
        
        d = Wire(self, "d", a.getWidth())
        Add(self, "add", a, r, d)
        
        e = self.wire('e', 1)
        Constant(self, 'e', 1, e)
        Reg(self, "reg", d, e, r)
 


sys = HWSystem()

a = Wire(sys, "a", 4)
r = Wire(sys, "r", 4)

Constant(sys, 'inc', 3, a)
SerialAdder(sys, "sa", a, r)

py4hw.gui.Workbench(sys)
