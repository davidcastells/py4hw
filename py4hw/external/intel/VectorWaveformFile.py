# -*- coding: utf-8 -*-
"""
Created on Wed Apr 19 16:59:12 2023

@author: dcr
"""

def tokenize_strings(line):
    i = 0
    ret = []
    
    s = ''
    instring = False
    
    while (i < len(line)):
        c = line[i]
        
        if (instring):
            if (c == '"'):
                instring = False
                ret.append(s)
                s = ''
            else:
                s += c
        else:
            if (c == '('):
                ret.append(c)
            elif (c == ')'):
                if (len(s) > 0):
                    ret.append(s)
                s = ''
                ret.append(c)
            elif (c == '"'):
                instring = True
            elif (c == ' '):
                if (len(s) > 0):
                    ret.append(s)
                s = ''
            else:
                s += c
            
        i += 1
        
        
    return ret

def listify_tokens(inlist, pos=0, level=0):
    ret = []
    while (pos < len(inlist)):
        token = inlist[pos]
        
        if (token == '('):
            subtokens, newpos = listify_tokens(inlist, pos+1, level+1)
            pos = newpos
            ret.append(subtokens)
        elif (token == ')'):
            return ret, pos+1
        else:
            ret.append(token)
            pos += 1
            
    return ret

def startsWith(line, st):
    return (line[0:len(st)] == st)

def convertTransitionsToValues(lines, period):
    ret = []
    
    for line in lines:
        if (isinstance(line, VWFNode)):
            ret2 = convertTransitionsToValues(line.value, period)
            ret.extend(ret2)
            
        elif (startsWith(line, 'REPEAT')):
            part = line.split('=')
            repeat = part[1].strip()
        elif (startsWith(line, 'LEVEL')):
            part = line.split()
            level = part[1]
            assert(part[2] == 'FOR')
            dur = int(float(part[3]) / period)
            
            for i in range(dur):
                ret.append(level)
                
    return ret;

class VWFObj():
    def __init__(self):
        self.child = []
        
            
    def find(self, ty):
        for item in self.child:
            if (isinstance(item, ty)):
                return item
        raise Exception('no {} child '.format(ty))
        
    def findAll(self, ty):
        ret = []
        
        for item in self.child:
            if (isinstance(item, ty)):
                ret.append(item)
                
        return ret
    

class VWFTop(VWFObj):
    pass

class VWFHeader(VWFObj):
    pass

class VWFTimeBar(VWFObj):
    pass

class VWFDisplayLine(VWFObj):
    pass

class VWFSignal(VWFObj):
    
    def parse(self, line):
        line = line[len('SIGNAL('):-1] # trim 
        
        if (line[0] == '"'):
            line = line[1:-1] # remove quotes
                    
        self.name = line
        
class VWFTransitionList(VWFObj):
    
    def parse(self, line):
        line = line[len('TRANSITION_LIST('):-1] # trim 
        
        if (line[0] == '"'):
            line = line[1:-1] # remove quotes
                    
        self.name = line
    
class VWFNode(VWFObj):
    pass

class ConvertVWF():
    def __init__(self):
        self.verbose = True
    
    def readfile(self, filename):
        f = open(filename, 'r')
        lines = f.readlines()
        ret = []
        
        # remove comments
        incomment = False
        for line in lines:
            if not(incomment):
                if '/*' in line:
                    part = line.split('/*')
                    ret.append(part[0])
                    incomment = True
                else:
                    if (len(line) > 0):
                        ret.append(line)
            else:
                if '*/' in line:
                    part = line.split('*/')
                    ret.append(part[1])
                    incomment = False
                else:
                    pass
                
        lines = ret
        
        # remove \n
        ret = []
        for line in lines:
            parts = line.split('\n')
            for part in parts:
                if (len(part) > 0):
                    ret.append(part.strip()) 
                    
        return ret
    
    def load(self, filename):
        self.lines = self.readfile(filename)
        self.i =0
        
        self.top = VWFTop()
        self.parseObjects(self.top)
        
        #print('START DRAWING')
        #self.top.draw()
        
    
        
    def parseDict(self, obj):
        ret = {}
        
        line = self.lines[self.i].strip()
        self.i+=1
        
        if (self.verbose):
            print('{}:{}'.format(self.i, line))
        
        assert(line == '{')
        
        while (self.i < len(self.lines)):
            line = self.lines[self.i].strip()
            self.i+=1
            
            print('{}:{}'.format(self.i, line))
            
            if (line == '}'):
                obj.value = ret
                return 
            else:
                line = line[:-1] # trip final ;
                part = line.split('=')
                key = part[0].strip()
                value = part[1].strip()
                if (value[0] == '"'):
                    value = value[1:-1] # remove quotes
                    
                ret[key] = value
        
        assert(False)
           
    def parseList(self, obj):
        ret = []
        
        line = self.lines[self.i].strip()
        self.i+=1
        
        if (self.verbose):
            print('{}:{}'.format(self.i, line))
        
        assert(line == '{')
        
        while (self.i < len(self.lines)):
            line = self.lines[self.i].strip()
            self.i+=1
            
            print('{}:{}'.format(self.i, line))
            
            if (line == '}'):
                obj.value = ret
                return 
            else:
                if (startsWith(line, 'NODE')):
                    lobj = VWFNode()
                    self.parseList(lobj)
                    ret.append(lobj)                    
                else:
                    line = line[:-1] # trip final ;
                    ret.append(line)
        
        assert(False)
    
    def parseObjects(self, obj):
        if (self.verbose):
            print('parse', type(obj))

        while (self.i < len(self.lines)):
            line = self.lines[self.i].strip()
            self.i+=1
            
            if (self.verbose):
                print('{}:{}'.format(self.i, line))
            
            if (line == 'HEADER' ):
                lobj = VWFHeader()
                self.parseDict(lobj)
                obj.child.append(lobj)
            elif (line[0:7] == 'SIGNAL('):
                lobj = VWFSignal()
                lobj.parse(line)
                self.parseDict(lobj)
                obj.child.append(lobj)
            elif (line == 'TIME_BAR'):
                lobj = VWFTimeBar()
                self.parseDict(lobj)
                obj.child.append(lobj)
            elif (line == 'DISPLAY_LINE'):
                lobj = VWFDisplayLine()
                self.parseDict(lobj)
                obj.child.append(lobj)
            elif (line == 'NODE'):
                lobj = VWFNode()
                self.parseList(lobj)
                obj.child.append(lobj)
            elif (startsWith(line, 'TRANSITION_LIST(')):
                lobj = VWFTransitionList()
                lobj.parse(line)
                self.parseObjects(lobj)
                obj.child.append(lobj)
            elif (line == '{'):
                pass # ignore the start
            elif (line == '}'):
                #print('<<<<<', type(obj))
                return
            else:
                print('?? - ?? - ??', line)
                
    
    def draw_wavedrom(self):
        import nbwavedrom as wave
        return wave.draw(self.get_wavedrom())
    
    def get_wavedrom(self):
        
        header = self.top.find(VWFHeader)
        period = float(header.value['GRID_PERIOD'])
        
        #signals = [{"name": "clk", 'wave': 'P'}]
        signals = [] 
        
        for idx, tran in enumerate(self.top.findAll(VWFTransitionList)):
            node = tran.find(VWFNode)
            
            fmt = ''
            wavedata = 'x'
            wavedatadata = []
            
            data = convertTransitionsToValues(node.value, period)
            last = 'x'
            numclks = len(data)
            for i in range(numclks):
                v = data[i]
                if (v != last):
                    wavedata += '{}'.format(v)
                else:
                    wavedata += '.'
                last = v
                    
            wavedata += 'x'
            
            name = tran.name
                
            signals.append({'name': name, 'wave':wavedata, 'data':wavedatadata})

        #wavedata = 'P'
        #for i in range(numclks):
        #    wavedata += '.'
        #wavedata += 'x'

        #signals[0]['wave'] = wavedata
        
        ret = {
            "signal": signals,
            "head": {
                "text": 'Waveform',
                "tock": 0,
            }
        }
        
        return ret