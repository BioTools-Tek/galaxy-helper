#!/usr/bin/env python

from __future__ import print_function
import xml.etree.ElementTree as ET
import sys
import pdb

class SimpleCheetahVar:  # no 'select'

    def __init__(self, node, cheetah_name):
        self.__node = node

        self.tag_type = node.get("type")
        self.name_global = cheetah_name
        self.name_local = node.get("name")
        
        self.optional = node.get("optional") == "true"
        self.argname = node.get("argument")
                
        self.text = self.__optionalWrapper()

    def __optionalWrapper(self):
        ''' Provides wrapper for all arguments if optional'''
        main_text = self.__typeAll()
        if self.optional:
            main_text = "#if %s\n%s\n#end if" % (
                self.argname if self.argname is not None else self.name_local,
                main_text
            )
        
        return main_text

    def __typeAll(self):
        res = None
        if self.tag_type == "boolean":
            res = self.__typeBool()
        elif self.tag_type == "integer" or self.tag_type == "float":
            res = self.__typeNumber()
        elif self.tag_type == "text":
            res = self.__typeText()
        elif self.tag_type == "data":
            res = self.__typeData()
        elif self.tag_type == "select":
            print("Select should not be used here", file=sys.stderr)
            exit(-1)
            #res = self.__typeSelect()
        else:
            print("Unknown type:", self.tag_type, file=sys.stderr)
            exit(-1)

    def __typeData(self):
        return "#if $%s\n%s $%s\n#end if" % (
            self.name_global,
            self.argname if self.argname is not None else self.name_local,
            self.name_global
        )     

    def __typeBool(self):
        trueval = self._node.get("truevalue")
        falsval = self._node.get("falsevalue")
        argname = self.argname if self.argname is not None else self.name_local

        if None in [trueval, falsval]:
            print("Note: boolean flag '%s' does not have a truevalue or falsevalue."
                  "      Suggest using '-%s' for truevalue and '' for falsevalue "
                  % (self.name_local, argname),
                  file=sys.stderr)
            exit(-1)

        return "$%s" % argname

    def __typeNumber(self):
        valmin = self._node.get("min")
        valmax = self._node.get("max")
        value = self._node.get("value")

        if None in [valmin, valmax, value]:
            print("Note: numeric arg '%s' does not have one of min max or default value."
                  % self.name_local,
                  file=sys.stderr)
            exit(-1)

        if self.argname is not None:
            return "%s $%s" %  (self.argname, self.name_global)

        return "#echo %s" % self.name_local

    def __typeText(self):
        value = self._node.get("value")

        return "#if str($%s.value) != ""\n%s '$%s.value'\n#end if" % (
            self.name_global,
            self.argname if self.argname is not None else "#echo %s" % self.name_local,
            self.name_global
        ) 
        

class InputMapper:

    def __init__(self, file1):
        root = ET.parse(file1).getroot()
        inputs = [x for x in root if x.tag == "inputs"][0]

        self.variable_names = self.__generateVariableNames(inputs)
        self.work(inputs)


    def work(self,inputs):

        traversed_names = {}
        
        def recurseParam(node, parentNode=None):
            name = node.get("name")
            tag  = node.tag     # node.get("tag")

            print(":::", name, tag)

            if (name is None) or (tag in ["section","conditional"]):
                for subnode in node:
                    recurseParam(subnode, node)
                return ""

            varname = self.variable_names[name]
            
            if name in traversed_names:
                return ""
            
            traversed_names[name] = True

            if tag == "param":
                ntype = node.get("type")
                noptl = not(node.get("optional") == None)  # False =!= None

                if ntype == "select":
                    # grab all possible values
                    pdb.set_trace()
                    option_value_map = getOptions(node)
                    when_value_map = getWhens(parentNode)

                    if option_value_map.keys() != when_value_map.keys():
                        print("Missing value or when field for", name, file=sys.stderr)
                        exit(-1)

                    if noptl:
                        print("#if %s\n")

                    for value in when_value_map:
                        print("#if '%s.value' == %s" % (varname, value))
                        recurseParam(value, node)
                        print("#end if")

                    if noptl:
                        print("#end if")

                else:
                    scv = SimpleCheetahVar(node, varname)
                    print(scv.text)

            for no in node:
                recurseParam(no, node)
            return ""

        # _Main_
        for inp in inputs:
            recurseParam(inp, None)


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


dela = InputMapper('allegro.xml')
pdb.set_trace()
