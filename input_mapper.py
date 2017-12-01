#!/usr/bin/env python

from __future__ import print_function
import xml.etree.ElementTree as ET
import sys
import pdb

class InputMapper:

    def __init__(self, file1):
        root = ET.parse(file1).getroot()
        inputs = [x for x in root if x.tag == "inputs"][0]

        self.variable_names = self.__generateVariableNames(inputs)
        self.work(inputs)


    def work(self,inputs):
        import pdb
        traversed_names = {}

        def optionalwrapper(text, opt):
            print("%s%s%s" % (
                "" if not opt else "#if %s\n" % varname,
                text,
                "" if not opt else "\n#end if"
            ))
        
        def recurseParam(node, parentNode=None, tabamount=0):
            name = node.get("name")

            if name == None:
                for subnode in node:
                    return recurseParam(subnode, node, tabamount)

            varname = self.variable_names[name]
            
            if name in traversed_names:
                return ""
            traversed_names[name] = True

            if node.tag == "param":
                ntype = node.get("type")
                noptl = not(node.get("optional") == None)  # False =!= None

                if ntype == "select":
                    # grab all possible values
                    option_value_map = getOptions(node)
                    when_value_map = getWhens(parentNode)

                    if option_value_map.keys() != when_value_map.keys():
                        print("Missing value or when field for", name, file=sys.stderr)
                        exit(-1)

                    for value in when_value_map:
                        print("#if '%s.value' == %s" % (varname, value))
                        recurseParam(value, node, tabamount + 1)
                        print("#end if")

                elif ntype == "data":
                    optionalwrapper("[EDIT FOR file '%s']" % varname, noptl)

                elif ntype == "text":
                    optionalwrapper("#if str('%s') != ""\n[EDIT FOR text '%s']\n#end if" % (varname, name))

                elif ntype == "boolean":
                    print("#if %s != ""\n[EDIT FOR boolean '%s']\n#end if" % (varname, name))

                else: # integer, float
                    optionalwrapper("#[EDIT FOR integer/float '%s']" % (varname, name))


            for no in node:
                recurseParam(no, node, tabamount + 1)

            return ""

        recurseParam(inputs, None, 0)


    def __generateVariableNames(self, inputs):
        param_map = {}

        def recurse(node, parent_array):
            name = node.get("name")

            if node.tag == "param":
                new_path = parent_array + [name]

                if name in param_map:
                    old_path = param_map[name]
                    if old_path != new_path:
                        pdb.set_trace()
                        print("duplicate name", name, old_path, new_path, file=sys.stderr)
                        # cry, debug
                else:
                    param_map[name] = new_path

                return 0

            for subnode in node:
                if node.tag in ["section","conditional"]:
                    recurse(subnode, parent_array + [name])
                else:
                    recurse(subnode, parent_array)

            return 0

        recurse(inputs, [])

        for key in param_map:
            param_map[key] = ".".join(param_map[key])
            
        return param_map
