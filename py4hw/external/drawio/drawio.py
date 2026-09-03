# -*- coding: utf-8 -*-
"""
Created for py4hw circuit diagrams export to Draw.io format (.drawio / .xml)
Supports child instances, wires, and top-level circuit I/O pins.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Geometry constants (Pixels)
# ---------------------------------------------------------------------------
BOX_WIDTH = 180
PORT_ROW_HEIGHT = 26
BOX_HEADER_HEIGHT = 32
COLUMN_GAP = 140
ROW_GAP = 40
PORT_LABEL_WIDTH = 60
PAGE_MARGIN = 40
IO_PIN_WIDTH = 90
IO_PIN_HEIGHT = 32
IO_PIN_GAP = 15


class _PortResolver:
    
    

    @classmethod
    def wire_endpoints(
        cls, circuit: Any, wire: Any, instances_by_name: Dict[str, Any]
    ) -> Tuple[Optional[Tuple[str, str]], List[Tuple[str, str]]]:
        source: Optional[Tuple[str, str]] = None
        sinks: List[Tuple[str, str]] = []

        # 1. Top-level circuit IN ports act as wire SOURCES internally
        if circuit is not None:
            for port in circuit.inPorts:
                if port.wire is wire:
                    source = ("__TOP__", port.name)

        # 2. Child instance ports
        for inst_name, inst in instances_by_name.items():
            for port in inst.outPorts:
                if port.wire is wire:
                    source = (inst_name, port.name)
            for port in inst.inPorts:
                if port.wire is wire:
                    sinks.append((inst_name, port.name))

        # 3. Top-level circuit OUT ports act as wire SINKS internally
        if circuit is not None:
            for port in circuit.outPorts:
                if port.wire is wire:
                    sinks.append(("__TOP__", port.name))

        return source, sinks


class DrawIoDiagramGenerator:
    """Generates uncompressed draw.io (.drawio / .xml) diagram files."""

    def __init__(self) -> None:
        self._id_counter = 2

    def _next_id(self) -> str:
        idx = str(self._id_counter)
        self._id_counter += 1
        return idx

    def generate(self, circuit: py4hw.Logic, output_path: str) -> None:
        work_path = (output_path
            if output_path.endswith(".drawio") or output_path.endswith(".xml")
            else output_path + ".drawio"
        )

        mxfile = ET.Element("mxfile", {"host": "Electron", "version": "21.0.0", "type": "device"})
        diagram = ET.SubElement(mxfile, "diagram", {"id": "diagram_1", "name": "Page-1"})
        mx_graph = ET.SubElement(diagram, "mxGraphModel", {
                "dx": "1000",
                "dy": "1000",
                "grid": "1",
                "gridSize": "10",
                "guides": "1",
                "tooltips": "1",
                "connect": "1",
                "arrows": "1",
                "fold": "1",
                "page": "1",
                "pageScale": "1",
                "pageWidth": "1169",
                "pageHeight": "827",
                "math": "0",
                "shadow": "0",
            })
        root = ET.SubElement(mx_graph, "root")

        ET.SubElement(root, "mxCell", {"id": "0"})
        ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

        instances = circuit.children
        
        wires = circuit._wires
        top_in_ports = [port.name for port in circuit.inPorts]            
        top_out_ports = [port.name for port in circuit.outPorts]
        
        for port in circuit.inPorts:
            wires[f'TOP_{port.name}'] = port.wire
        for port in circuit.outPorts:
            wires[f'TOP_{port.name}'] = port.wire
        
        layers = self._layer_instances(instances, wires)

        

        # Layout 1st level: key = instance name, value = another dictionary
        #        2nd level: key = "box_id", "in" or "out", value = an id for box_id, another dictionary for port directions
        layout: Dict[str, Dict[str, Any]] = {
            "__TOP__": {"out": {}, "in": {}},
        }

        # Determine column offsets based on top-level input presence
        start_col = 1 if top_in_ports else 0

        # 1. Render Top-Level Circuit Input Pins (Column 0)
        if top_in_ports:
            in_y = PAGE_MARGIN
            for p_name in top_in_ports:
                pin_id = self._create_io_pin(root, p_name, x=PAGE_MARGIN, y=in_y, is_input=True)
                layout["__TOP__"]["out"][p_name] = pin_id
                in_y += IO_PIN_HEIGHT + IO_PIN_GAP

        # 2. Render Child Instance Blocks & Ports (Columns start_col .. N)
        for col_idx, layer in enumerate(layers):
            actual_col = col_idx + start_col
            target_x = PAGE_MARGIN + actual_col * (BOX_WIDTH + COLUMN_GAP)
            target_y = PAGE_MARGIN

            for inst_name in layer:
                inst = instances[inst_name]
                box_id, port_ids, height = self._create_block(root, inst, inst_name, target_x, target_y)

                layout[inst_name] = {"box_id": box_id, "in": port_ids["in"], "out": port_ids["out"]}
                target_y += height + ROW_GAP

        # 3. Render Top-Level Circuit Output Pins (Far Right Column)
        if top_out_ports:
            out_col = len(layers) + start_col
            out_x = PAGE_MARGIN + out_col * (BOX_WIDTH + COLUMN_GAP)
            out_y = PAGE_MARGIN
            for p_name in top_out_ports:
                pin_id = self._create_io_pin(root, p_name, x=out_x, y=out_y, is_input=False)
                layout["__TOP__"]["in"][p_name] = pin_id
                out_y += IO_PIN_HEIGHT + IO_PIN_GAP

        # 4. Generate Wires
        for wire_name, wire in wires.items():
            print(f'wire: {wire_name}', end=' ')
            
            source, sinks = _PortResolver.wire_endpoints(circuit, wire, instances)
            
            print(source, end=' -> ')
            print(sinks)
            
            if (source is None):
                print('no source')
                continue
                
            src_inst, src_port = source
            from_port_id = layout[src_inst]["out"][src_port]
            
            
            

            for sink_inst, sink_port in sinks:
                to_port_id = layout[sink_inst]["in"][sink_port]
                
                print('   ', f'{from_port_id} -> {to_port_id}')
                
                self._create_edge(root, from_port_id, to_port_id, label=wire_name)

            print()
            
        # 5. Output XML File
        raw_xml = ET.tostring(mxfile, encoding="utf-8")
        pretty_xml = minidom.parseString(raw_xml).toprettyxml(indent="  ")
        with open(work_path, "w", encoding="utf-8") as f:
            f.write(pretty_xml)

    def _create_io_pin(self, root: ET.Element, pin_name: str, x: float, y: float, is_input: bool) -> str:
        pin_id = self._next_id()
        # Input pins connect from right edge; Output pins connect to left edge
        anchor = "[[1,0.5,0,0,0]]" if is_input else "[[0,0.5,0,0,0]]"
        color_style = (
            "fillColor=#e1f5fe;strokeColor=#0288d1;fontColor=#01579b;"
            if is_input
            else "fillColor=#fff3e0;strokeColor=#f57c00;fontColor=#e65100;"
        )
        style = (
            f"rounded=1;whiteSpace=wrap;html=1;{color_style}fontStyle=1;fontSize=11;"
            f"align=center;verticalAlign=middle;points={anchor};"
        )
        label = f"{pin_name}" 
        cell = ET.SubElement(root, "mxCell",{"id": pin_id,"value": label,"style": style,"vertex": "1","parent": "1",})
        ET.SubElement(cell, "mxGeometry", {"x": str(x), "y": str(y), "width": str(IO_PIN_WIDTH), "height": str(IO_PIN_HEIGHT), "as": "geometry"})
        return pin_id

    def _create_block(self, root: ET.Element, inst: Any, inst_name: str, x: float, y: float) -> Tuple[str, Dict[str, Dict[str, str]], float]:
        in_ports = [port.name for port in inst.inPorts]
        out_ports = [port.name for port in inst.outPorts]

        height = BOX_HEADER_HEIGHT + PORT_ROW_HEIGHT * max(len(in_ports), len(out_ports), 1)

        box_id = self._next_id()
        box_style = (
            "rounded=1;whiteSpace=wrap;html=1;align=center;verticalAlign=top;"
            "spacingTop=6;fillColor=#f8f9fa;strokeColor=#333333;fontStyle=1;fontSize=12;"
        )
        box_cell = ET.SubElement(root, "mxCell", { "id": box_id, "value": inst_name, "style": box_style, "vertex": "1","parent": "1",})
        ET.SubElement(box_cell,"mxGeometry",{"x": str(x),"y": str(y),"width": str(BOX_WIDTH),"height": str(height),"as": "geometry",})

        port_ids: Dict[str, Dict[str, str]] = {"in": {}, "out": {}}

        # In-ports
        for i, p_name in enumerate(in_ports):
            port_id = self._next_id()
            port_y = BOX_HEADER_HEIGHT + i * PORT_ROW_HEIGHT
            port_style = (
                "text;html=1;align=left;verticalAlign=middle;resizable=0;"
                "points=[[0,0.5,0,0,0]];autosize=0;strokeColor=none;fillColor=none;"
                "fontSize=10;fontColor=#444444;"
            )
            p_cell = ET.SubElement(root, "mxCell", { "id": port_id, "value": f"► {p_name}", "style": port_style, "vertex": "1", "parent": box_id,})
            ET.SubElement(p_cell, "mxGeometry", { "x": "4", "y": str(port_y), "width": str(PORT_LABEL_WIDTH), "height": str(PORT_ROW_HEIGHT), "as": "geometry", } )
            port_ids["in"][p_name] = port_id

        # Out-ports
        for i, p_name in enumerate(out_ports):
            port_id = self._next_id()
            port_y = BOX_HEADER_HEIGHT + i * PORT_ROW_HEIGHT
            port_x = BOX_WIDTH - PORT_LABEL_WIDTH - 4
            port_style = (
                "text;html=1;align=right;verticalAlign=middle;resizable=0;"
                "points=[[1,0.5,0,0,0]];autosize=0;strokeColor=none;fillColor=none;"
                "fontSize=10;fontColor=#444444;"
            )
            p_cell = ET.SubElement( root, "mxCell", { "id": port_id, "value": f"{p_name} ►", "style": port_style, "vertex": "1", "parent": box_id, } )
            ET.SubElement( p_cell, "mxGeometry", { "x": str(port_x), "y": str(port_y), "width": str(PORT_LABEL_WIDTH), "height": str(PORT_ROW_HEIGHT), "as": "geometry", } )
            port_ids["out"][p_name] = port_id

        return box_id, port_ids, height

    def _create_edge(self, root: ET.Element, source_id: str, target_id: str, label: str = "") -> None:
        edge_id = self._next_id()
        edge_style = (
            "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;"
            "jettySize=auto;html=1;strokeColor=#0055BB;strokeWidth=1.5;"
            "exitX=1;exitY=0.5;exitDx=0;exitDy=0;"
            "entryX=0;entryY=0.5;entryDx=0;entryDy=0;"
        )
        edge_cell = ET.SubElement(
            root,
            "mxCell",
            {
                "id": edge_id,
                "value": label if label and not label.startswith("_") else "",
                "style": edge_style,
                "edge": "1",
                "parent": "1",
                "source": source_id,
                "target": target_id,
            },
        )
        ET.SubElement(edge_cell, "mxGeometry", {"relative": "1", "as": "geometry"})

    def _layer_instances(self, instances: Dict[str, Any], wires: Dict[str, Any]) -> List[List[str]]:
        deps: Dict[str, set] = {name: set() for name in instances}

        for wire in wires.values():
            source, sinks = _PortResolver.wire_endpoints(circuit=None, wire=wire, instances_by_name=instances)
            if source is None:
                continue
            src_inst = source[0]
            for sink_inst, _ in sinks:
                if sink_inst in deps and src_inst in deps and sink_inst != src_inst:
                    deps[sink_inst].add(src_inst)

        level: Dict[str, int] = {}
        visiting: set = set()

        def compute_level(name: str) -> int:
            if name in level:
                return level[name]
            if name in visiting:
                return 0
            visiting.add(name)
            deps_levels = [compute_level(d) for d in deps[name]]
            lvl = (max(deps_levels) + 1) if deps_levels else 0
            visiting.discard(name)
            level[name] = lvl
            return lvl

        for name in instances:
            compute_level(name)

        max_level = max(level.values(), default=0)
        layers: List[List[str]] = [[] for _ in range(max_level + 1)]
        for name, lvl in level.items():
            layers[lvl].append(name)
        for layer in layers:
            layer.sort()
        return layers


if __name__ == "__main__":
    import py4hw

    hw = py4hw.HWSystem()

    a = hw.wire("a")
    b = hw.wire("b")
    c = hw.wire("c")
    r = hw.wire("r", 8)

    mod = py4hw.ModuloCounter(hw, "name", 15, a, b, r, c)

    gen = DrawIoDiagramGenerator()
    gen.generate(mod, r"c:\temp\mod.drawio")