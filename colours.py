import sys
from jpy import util

# Bash colours - taken from http://tldp.org/HOWTO/Bash-Prompt-HOWTO/x329.html
#   Black       0;30     Dark Gray     1;30
#   Blue        0;34     Light Blue    1;34
#   Green       0;32     Light Green   1;32
#   Cyan        0;36     Light Cyan    1;36
#   Red         0;31     Light Red     1;31
#   Purple      0;35     Light Purple  1;35
#   Brown       0;33     Yellow        1;33
#   Light Gray  0;37     White         1;37

# Example usage: echo -e ${COL_GRAY}This is some text${COL_NONE}

colours_dict = {
	"BLACK"	:"\033[0:30m",
	"GRAY"	:"\033[1;30m",
	"RED"	:"\033[0;31m",
	"LRED"	:"\033[1;31m",
	"GREEN"	:"\033[0;32m",
	"LGREEN"	:"\033[1;32m",
	"BROWN"	:"\033[0;33m",
	"YELLOW"	:"\033[1;33m",
	"DBLUE"	:"\033[0;34m",
	"BLUE"	:"\033[1;34m",
	"PURPLE"	:"\033[0;35m",
	"LPURPLE"	:"\033[1;35m",
	"CYAN"	:"\033[0;36m",
	"LCYAN"	:"\033[1;36m",
	"LGRAY"	:"\033[0;37m", # Already declared as 0;0m
	"WHITE"	:"\033[1;37m",
	"NONE"	:"\033[0m", # No colours
}

me = sys.modules[__name__]
for (k, v) in list(colours_dict.items()):
	setattr(me, k, v)

def remove_colours(string):
	string = string.replace(BLACK, '')
	string = string.replace(GRAY, '')
	string = string.replace(RED, '')
	string = string.replace(LRED, '')
	string = string.replace(GREEN, '')
	string = string.replace(LGREEN, '')
	string = string.replace(BROWN, '')
	string = string.replace(YELLOW, '')
	string = string.replace(DBLUE, '')
	string = string.replace(BLUE, '')
	string = string.replace(PURPLE, '')
	string = string.replace(LPURPLE, '')
	string = string.replace(CYAN, '')
	string = string.replace(LCYAN, '')
	string = string.replace(LGRAY, '')
	string = string.replace(WHITE, '')
	string = string.replace(NONE, '')

	return string

# Performs variable-expansion on a string for colour variables
# defined in this file.
# e.g. expand_colours("${GREEN}Hello my name is ${YELLOW}Joe Bloggs${NONE}")
#
# if 'add_none' is True, this method will automatically add ${NONE} to the end
# of the string.
def expand_colours(string, add_none = True):
	result = util.expand(string, colours_dict)

	if add_none:
		result = result + NONE

	return result
