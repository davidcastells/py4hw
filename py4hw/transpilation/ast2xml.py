# -*- coding: utf-8 -*-
"""
Created on Sun Apr  2 14:59:36 2023

Reused from https://github.com/flyte/ast-to-xml

@author: dcr
"""
import ast
from lxml import etree as ET

ATTRS = ("lineno", "col_offset", "end_lineno", "end_col_offset")


def ast_node_attrs(ast_node):
    attrs = {}
    for key in ATTRS:
        try:
            attrs[key] = str(getattr(ast_node, key))
        except AttributeError:
            continue
    return attrs

def visit_node(ast_node, parent_xml_node=None, ast_name=None):
    """
    Visits an AST node and creates an XML for it.
    
    AST objects have named parameters, we translate them into XML objects that have 
    xml subentities with the name of the parameter.
    

    Parameters
    ----------
    ast_node : TYPE
        DESCRIPTION.
    parent_xml_node : TYPE, optional
        DESCRIPTION. The default is None.

    Returns
    -------
    xml_node : TYPE
        DESCRIPTION.

    """
    assert(not(ast_node is None))
    
    if (ast_name is None):
        xml_node_name = ast_node.__class__.__name__
    else:
        xml_node_name = ast_name
        
    if parent_xml_node is None:
        #print('New root XML node', xml_node_name)
        xml_node = ET.Element(xml_node_name)
    else:
        xml_node = ET.SubElement(parent_xml_node, xml_node_name)

    xml_node.attrib.update(ast_node_attrs(ast_node))

    # Special case for list of objects
    if isinstance(ast_node, list):
        if all(isinstance(x, ast.AST) for x in ast_node):
            for node in ast_node:
                visit_node(node, xml_node)
        else:
            raise Exception('no pure AST list')
        return xml_node
            
    for key, value in ast_node.__dict__.items():
        if key.startswith("_") or key in ATTRS:
            continue
        if isinstance(value, ast.AST):
            # why 2 subelements ?
            sub_node = ET.SubElement(xml_node, key)
            visit_node(value, sub_node)
            #visit_node(value, xml_node)
        elif isinstance(value, list):
            if all(isinstance(x, ast.AST) for x in value):
                sub_node = ET.SubElement(xml_node, key)
                for node in value:
                    visit_node(node, sub_node)
        else:
            node = ET.SubElement(xml_node, key)
            node.attrib["type"] = type(value).__name__
            node.text = str(value)

    return xml_node

def renderXml(root):
    return (ET.tostring(root, pretty_print=True))