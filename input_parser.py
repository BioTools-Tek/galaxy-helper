#!/usr/bin/env python3

import sys, re
from input_mapper import InputMapper

#inp_params = [x for x in inputs.iter('param')]
param_map = InputMapper(sys.argv[1]).input_map

#print('\n'.join([" -- ".join([x,".".join(param_map[x])]) for x in param_map]))
#inp = input("convert?")
inp = "y"

if inp[0].lower() == "y":
    config_section = [x for x in root if x.tag == "configfiles"][0]

    for config in config_section:

        full_text = config.text
        matching_inputs = re.findall("\$\{?[^}'\s]+\}?", full_text)

        for inparam in matching_inputs:

            without_tag = re.match("\$\{?([^}'\s]+)\}?", inparam).group(1)
            without_tag = without_tag.split(".value")[0]

            if len(without_tag.split('.')) > 1:
                continue

            try:
                left, right = inparam.split(without_tag)
                resolved_new = ".".join(param_map[without_tag])
                
                old_text = inparam
                new_text = left + resolved_new + right
                
                full_text = full_text.replace(old_text, new_text, 10)
                
                print(old_text, "---", new_text)
            except KeyError:
                print("cannot find", without_tag)


        print(full_text)
