#!/usr/bin/env python

import sys
from input_mapper import InputMapper

param_map = InputMapper(sys.argv[1]).variable_names
import pdb; pdb.set_trace()
