# Exporter - provides function to dump a bash-style export of certain
# variables defined on a python module

import re

exportable = re.compile("[A-Z][\w]+")

# Prints an export of all variables that begin with a capital letter for the given object.
# (FYI, to get the object that represents your python module, try this: sys.modules[__name__] )
def export_values(module, varprefix = '', lineprefix = ''):
	# Make a bash-friendly file containing export statements for all settings, so it can be run from within scripts
	for name in dir(module):
		if exportable.match(name) == None:
			break
		
		value = getattr(module, name)

		if type(value) is list:
			value = ' '.join(value)

		print((lineprefix + varprefix + name + "=\"" + value + "\""))

