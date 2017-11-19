#!/usr/bin/env python3

import sys
import xml.etree.ElementTree as ET

file1 = sys.argv[1]
root = ET.parse(file1).getroot()

inputs = [x for x in root if x.tag == "inputs"][0]
#inp_params = [x for x in inputs.iter('param')]

param_map = {} #

def recurse(node, parent_array):

    name = node.get("name")

    if node.tag == "param":
        new_path = parent_array + [name]

        if name in param_map:
            old_path = param_map[name]
            if len(old_path) > len(new_path):
                return 0

        param_map[name] = new_path
        #if name == "extra_sun":
        #    print("DEBUG:", name, parent_array)            
        return 0

    if node.tag in ["section","conditional"]:
        for subnode in node:
            recurse(subnode, parent_array + [name])

    for subnode in node:
        recurse(subnode, parent_array)
    
    return 0


recurse(inputs, [])
#import pdb; pdb.set_trace()
print('\n'.join([" -- ".join([x,".".join(param_map[x])]) for x in param_map]))
