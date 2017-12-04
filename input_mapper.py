#!/usr/bin/env python

from __future__ import print_function
import xml.etree.ElementTree as ET
import sys
import pdb


def err(*messages):
    print("Error:", *messages, file=sys.stderr)
    exit(-1)

def warn(*messages):
    print("Warning:", *messages, file=sys.stderr)

def printtab(text, tablevel):
    lines = text.splitlines()
    for line in lines:
        if line[0] == '#':
            print('    ' * tablevel, line, sep="")
            if line.startswith("#end if"):
                print("")
        else:
            print(line)



class SimpleCheetahVar:  # no 'select'

    def __init__(self, node, cheetah_name, tablevel=0):
        self._node = node

        self.tag_type = node.get("type")
        self.name_global = cheetah_name
        self.name_local = node.get("name")

        self.optional = node.get("optional") == "true"
        self.argname = node.get("argument")

        self._text = self.__optionalWrapper()
        self.printAll(tablevel)

    def printAll(self, tablevel):
        if self._text is None:
            pdb.set_trace()
            err("No text to generate for %s" % self.name_local)

        printtab(self._text, tablevel)


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
            res = self.__typeSelect()
            #err("Select should not be used here")
        else:
            err("Unknown type:", self.tag_type)
        return res

    def __typeData(self):
        #return "#if $%s\n%s $%s\n#end if" % (
        #    self.name_global,
        #    self.argname if self.argname is not None else self.name_local,
        #    self.name_global
        #)
        return "FLAGFOR file $%s" % (self.argname if self.argname is not None else self.name_local)

    def __typeBool(self):
        trueval = self._node.get("truevalue")
        falsval = self._node.get("falsevalue")
        argname = self.argname if self.argname is not None else self.name_local

        if None not in [trueval, falsval]:
            if self.argname is not None:
                warn("Note: boolean flag '%s' does not have a truevalue or falsevalue."
                     "\n  Suggest using truevalue='-%s' falsevalue='' "
                     % (self.name_local, argname))
            return "$%s" % argname

        return "#if $%s\nFLAGFOR bool %s\n#end if" % (self.name_global, self.name_local)

    
    def __typeNumber(self):
        valmin = self._node.get("min")
        valmax = self._node.get("max")
        value = self._node.get("value")

        #if None in [valmin, valmax, value]:
        #    warn("numeric arg '%s' does not have one of min max or default value." % self.name_local)

        if self.argname is not None:
            return "%s $%s" %  (self.argname, self.name_global)

        return "FLAGFOR numeric %s" % self.name_local

    def __typeText(self):
        #default_value = self._node.get("value")

        return "#if str($%s.value) != ''\nFLAGFOR text %s '$%s.value'\n#end if" % (
            self.name_global,
            self.argname if self.argname is not None else "#echo %s" % self.name_local,
            self.name_global
        )

    def __typeSelect(self):
        return "FLAGFOR select '$%s.value'" % self.name_global


class InputMapper:

    def __init__(self, file1):
        root = ET.parse(file1).getroot()
        inputs = [x for x in root if x.tag == "inputs"][0]

        self.variable_names = self.__generateVariableNames(inputs)
        self.work(inputs)


    def work(self,inputs):

        traversed_names = {}

        def getOptions(node):
            values = {}
            for opt in node:
                if opt.tag != "option":
                    err("Non-option value given under %s" % node.get("name"))

                val = opt.get("value")
                if val in values:
                    err("Duplicate option value %s under %s" % (val, node.get("name")))

                values[val] = True

            return values.keys()


        def getWhensAndRecurse(cond_node, select_node, expected_whens, tablevel):
            optional = select_node.get("optional") == "true"
            cheetah_name = self.variable_names[select_node.get("name")]

            next_tab = tablevel

            if optional:
                next_tab += 1
                printtab("#if $%s" % cheetah_name, tablevel)

            first_valid_when = True
            for when in cond_node:
                if when.tag == "when":  # must assume all other nodes can be ignored or have already been chomped
                    val = when.get("value")
                    if val not in expected_whens:
                        err("%s value for when not found in expected options" % val, expected_whens)

                    # start per when                   
                    if len(when) > 0 and first_valid_when:
                        printtab("#if '%s.value' == '%s'" % (cheetah_name,val), next_tab)   # when value
                        first_valid_when = False
                    elif len(when) > 0:
                        printtab("#elif '%s.value' == '%s'" % (cheetah_name,val), next_tab)   # when value

                    recurseParam(when, next_tab + 1)

            # end per when
            printtab("#end if", next_tab)

            if optional:
                printtab("#end if", tablevel)


        def recurseParam(node, tablevel):
            name = node.get("name")
            tag  = node.tag     # node.get("tag")

            if tag == "conditional":
                # must assume that first param is the conditional
                main_param = [param for param in node if param.tag == "param"][0]
                if main_param.get("type") != "select":
                    err("%s param for conditional %s is not of select type" % (main_param.get("name"), name))

                getWhensAndRecurse(node, main_param, getOptions(main_param), tablevel)
                return ""


            if tag == "param":
                varname = self.variable_names[name]

                if name in traversed_names:
                    return ""

                traversed_names[name] = True

                ntype = node.get("type")
                noptl = not(node.get("optional") == None)  # False =!= None

                # Normal params, even selects which are not under conditionals
                scv = SimpleCheetahVar(node, varname, tablevel)
                return ""

            for no in node:
                recurseParam(no, tablevel + 1)

            return ""

        # __Main__
        recurseParam(inputs, -1)


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
