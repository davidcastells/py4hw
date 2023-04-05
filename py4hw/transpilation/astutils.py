# -*- coding: utf-8 -*-
"""
Created on Tue Apr  4 19:45:20 2023

@author: dcastel1
"""

import ast
import inspect
import textwrap

def getMethod(obj, methodname):
    methods = inspect.getmembers(obj, inspect.ismethod)
    method = [x[1] for x in methods if x[0] == methodname ][0]

    source = textwrap.dedent(inspect.getsource(method))
    node = ast.parse(source)
    return node
