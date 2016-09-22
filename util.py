# General-purpose util module

import os, locale, sys, select, re, types, datetime, traceback, pprint
from .asrt import *
import imp

debug = False
debug_filters = []
def debug_enabled(d):
    """
    Enable debugging. This switches on debug output printed
    via dprint().
    """
    global debug
    debug = d

def set_debug_filters(filters):
    """
    Sets the module names which debugging is enabled for.

    Filters should be a list of strings, each string naming
    a module. If filters is None or an empty list, debugging
    is enabled for all modules.
    """
    global debug_filters

    # clear filters so we can dprint() the new filter
    debug_filters = None
    dprint('new debug filters', debug_filters=filters)

    if not filters: filters = []
    debug_filters = filters

def dprint(*args, **kwargs):
    """
    If pymusutil.debug is True, print out the attached to stderr.

    dprint() does a number of funky things you need to be aware of:
     - dprint will look up the stack frame and print out the file, line
       number and function name it was called from
     - lines are indented to indicate stack depth (and hopefully give
       clues as to which functions are calling others)
     - args are printed as would be with print(), and kwargs are then
       printed in key=value pairs, one per line, after args. This allows
       you to do cool things like dprint(**locals()) to print out all local
       vars
     - as with print(), it converts all items to strings, but any kwargs
       that are *not* strings will also have their types printed after
       their values
     - any args or kwargs that look like paths (i.e. os.path.exists() = True)
       will have the path *stripped* (using os.path.basename) and replaced
       '#/' to indicated that has taken place. So, "/path/to/file"
       becomes "#/file". Clearly this behaviour could be undesirable when
       debugging some code, so it can be disabled by adding _no_basenames=True
       to the arg list
     - all output goes to stderr
     - debug statements are filtered according to set_debug_filters(). If
       debug_filters is an empty list, no filtering is performed. Otherwise,
       only modules whose names are included in debug_filters are printed.

     As dprint does all this funky stuff you should assume it is
     very expensive to execute when debug is True. No processing inside
     the function takes place when debug is False.

     Special arguments that can modify debug behaviour:
     - _no_basenames = disable basenaming behaviour (see above)

    """
    global debug
    global debug_filters

    if debug:
        no_basenames=False
        if '_no_basenames' in kwargs and kwargs['_no_basenames']:
            del kwargs['_no_basenames']
            no_basenames=True

        # get the frame representing the calling function
        stack_frame = traceback.extract_stack()[-2] 
        depth = len(traceback.extract_stack())-2

        def basename_if_str_and_path(s):
            if no_basenames: return s
            if type(s) is str and os.path.exists(s):
                suffix = '/' if os.path.isdir(s) else ''
                return '#/' + os.path.basename(s) + suffix
            return s

        module_name = os.path.basename(stack_frame.filename)
        if module_name[-3:] == '.py': module_name = module_name[0:-3]

        if not debug_filters or (debug_filters and module_name in debug_filters):
            prefix = module_name+':'+str(stack_frame.lineno)+' '+stack_frame.name+'() '
            argstring = ' '.join([basename_if_str_and_path(a) if type(a) is str else pprint.pformat(a) for a in args])

            if argstring:
                print(' '*depth+prefix, argstring, file=sys.stderr)

            for k, v in kwargs.items():
                print(' '*depth+prefix, '  ', k, '=', 
                        basename_if_str_and_path(v) if type(v) is str else pprint.pformat(v), 
                        '' if type(v) is str else type(v), file=sys.stderr)



# The familiar 'die' function
def die(msg):
    die_with_code(1, msg)

# The familiar 'die' function, with an exit code parameter
def die_with_code(exit_code, msg):
    print(msg, file=sys.stderr)
    sys.exit(exit_code)


def is_windows():
    return os.name == 'nt'


def is_posix():
    return os.name == 'posix'

# Sort a dict by its keys. Taken from:
# http://code.activestate.com/recipes/52306-to-sort-a-dictionary/
def sortedDict(adict):
    items = list(adict.items())
    items.sort()
    return [value for key, value in items]

# Adds dicts together, creating a new dict and returning it.
def add_dicts(dict1, dict2, add_nested_dicts = True, add_nested_lists = True, add_nested_tuples = True):
    # Create a copy of dict1, then add items in dict2 to it
    result = dict(dict1)

    for elem in dict2:
        if elem in dict1:
            # For each item in dict2, if the items also exists
            # in dict1, attempt to add them together to get the
            # final value.
            dict1value = dict1[elem]
            dict2value = dict2[elem]

            t1 = type(dict1value)
            t2 = type(dict2value)

            # (Use a special add method for nested dicts.)
            if add_nested_dicts and t1 is dict and t2 is dict:
                result[elem] = add_dicts(dict1value, dict2value)

            elif add_nested_lists and t1 is list and t2 is list:
                result[elem] = dict1value + dict2value

            elif add_nested_tuples and t1 is tuple and t2 is tuple:
                result[elem] = dict1value + dict2value

            else:
                # If both dicts contain the element and they're not
                # nested dicts, then dict2's value takes precedence
                #result[elem] = dict1.get(elem) + dict2[elem]
                result[elem] = dict2[elem]

        else:
            # For items not in dict1, just add them in as-is.
            result[elem] = dict2[elem]

    return result

# Adds dicts together, creating a new dict and returning it
def add_4dicts(dict1, dict2, dict3, dict4):
    first_two = add_dicts(dict1, dict2)
    last_two = add_dicts(dict3, dict4)

    return add_dicts(first_two, last_two)


# Strips any newlines (\r, \n or \r\n) from the end of a string
def strip_trailing_newline(s):
    if s.endswith('\r\n'):
        return s[:-2] # Strip trailing \r\n
    if s.endswith('\n'):
        return s[:-1] # Strip trailing \n
    if s.endswith('\r'):
        return s[:-1] # Strip trailing \r

# Acts like strip(), but for non-whitespace.
# For example:
#
# > s = 'aaabbb123456bbbaaa'
# > strip_chars(s, 'ab')
# '123456'
#
# Handy for stripping quotes or other special characters 
# from the edges of strings
def strip_chars(s, strip_chars, strip_whitespace = True):
    if strip_whitespace: s = s.strip()
    for char in strip_chars:
        while s.endswith(char):
            s = s[:-1]
            if strip_whitespace: s = s.strip()

        while s.startswith(char):
            s = s[1:]
            if strip_whitespace: s = s.strip()

    if strip_whitespace: s = s.strip()

    return s

# None-safe expanduser
def expanduser(path):
    if path == None:
        return None
    else:
        return os.path.expanduser(path)

# None-safe expandvars
def expandvars(path):
    if path == None:
        return None
    else:
        return os.path.expandvars(path)

# expanduser+expandvars+expand
def expand(string, var_dict = None):
    if string == None:
        return None

    string = expandvars(string)
    string = expanduser(string)

    if var_dict != None:
        string = _expand(string, var_dict)

    return string

_varprog = None

# expandvars, but with a custom list of variables
# this has been almost completely copied from python's posixpath.py, with the 
# exception of the stuff around 'var_dict'
# var_dict should be a dict of variable names -> values
def _expand(string, var_dict):
    """Expand shell variables of form $var and ${var}.  Unknown variables
    are left unchanged."""

    global _varprog
    if '$' not in string:
        return string
    if not _varprog:
        import re
        _varprog = re.compile(r'\$(\w+|\{[^}]*\})')
    i = 0
    while True:
        m = _varprog.search(string, i)
        if not m:
            break
        i, j = m.span(0)
        name = m.group(1)
        if name.startswith('{') and name.endswith('}'):
            name = name[1:-1]
        if name in var_dict:
            tail = string[j:]
            string = string[:i] + var_dict[name]
            i = len(string)
            string += tail
        else:
            i = j
    return string

# Create enums in python.
# Taken from: 
#  http://stackoverflow.com/questions/36932/whats-the-best-way-to-implement-an-enum-in-python/1695250#1695250
# Usage:
#  >>> Numbers = enum('ZERO', 'ONE', 'TWO')
#  >>> Numbers.ZERO
#  0
#  >>> Numbers.TWO
#  2
# 
def enum(*sequential, **named):
    enums = dict(list(zip(sequential, list(range(len(sequential))))), **named)
    return type('Enum', (), enums)

# Ask for user for input, with a timout. Linux only.
# Taken from:
# http://stackoverflow.com/questions/1335507/keyboard-input-with-timeout-in-python
def input(msg, timeout = 10, out_fd = sys.stdout, in_fd = sys.stdin):
    print(msg, end=' ', file=out_fd)
    out_fd.flush()

    i, o, e = select.select( [in_fd], [], [], timeout )

    if (i):
        return in_fd.readline().strip()
    else:
        return None

# Return the string surrounded in quotes. Handy for quoting filenames.
def quote(s):
    return '"' + s + '"'

# Attempt to match s against the given regex.
# If there's a match, return the list of matched groups.
# If there's no match, return None
def match_groups(regex, s):
    if type(regex) is str:
        regex = re.compile(regex)

    match = regex.match(s)

    if match == None:
        return match

    else:
        return match.groups()

# The same as match_groups above, but expects a list of regexes
# to match against a list of strings. For each item in the strings
# list, the corresponding regex in the regex list is matched against it.
#
# A list of lists (containing any group items matched) is returned.
# If strict is True, the method will return None if *any* regexes
# do not match, otherwise a list is returned with None for any regexes
# that failed to match.
#
# If strict_length is True, the method will return None if
# the lengths of regexes and seq are different. Otherwise,
# it'll carry on and match as much of the supplied regexes as it can.
#
def multi_match_groups(regexes, seq, strict = False, strict_length = True):
    ls = len(seq)
    lr = len(regexes)

    if strict_length and lr != ls: return None


    result = [None]*ls
    for i in range(0, ls):
        # if strict_length was False and len(seq) > len(regexes),
        # we need to check that regexes[i] actually exists here
        if i >= lr: break

        result[i] = match_groups(regexes[i], seq[i])

        if strict and result[i] == None: return None

    return result

# Attempt to match s against the given regex.
# If there's a match, return the list of matched group names.
# If there's no match, return None
def match_groupnames(regex, s):
    if type(regex) is str:
        regex = re.compile(regex)

    match = regex.match(s)

    if match == None:
        return match

    else:
        return match.groupdict()
        
def match_regexes(regexes, strings, fail_on_no_match = True):
    """
    Given a group of regexes and a group of strings, this function
    will try to match each regex against each string in turn.
    
    It returns a list where each item is a tuple representing the
    (regex, matched_groups) for the string in strings that corresponds.
    
    regexes should be a list of patterns.
    
    This is handy for parsing where each line may match one of several
    patterns. For example, suppose I have:
    
    patterns = [
        re.compile('^#.*'),
        re.compile('^(\d+) = (\d+)'),
        re.compile('^(\w+) = (\w+)')
        ]
    
    strings = [
        '# this is line 1',
        '1 = 2',
        'thisisline = three',
        '# this is line 4'
    ]
    
    result = match_regexes(patterns, strings)
    
    result will be:
        [ (patterns[0], []),
          (patterns[1], ['1', '2']),
          (patterns[2], ['thisisline', 'three']),
          (patterns[0], []) ]
          
    If fail_on_no_match is True, then if a string does not match any
    of the supplied patterns, an exception is thrown. If it is False,
    then the resulting tuple for that string will be (None, []).
    """
    result = []
    
    for s in strings:
        for r in regexes:
            match = False
            result_tuple = (None, [])
        
            matches = match_groupnames(r, s)
            if matches:
                result_tuple = (r, matches)
                match = True
                break
                
        if not match and fail_on_no_match:
            raise ValueError('String "%s" did not match any patterns'%(s))
        result.append(result_tuple)
        
    return result

# ask for password on a Cygwin terminal
# here because getpass doesn't seem to work
def ask_for_pw(prompt = 'Enter password: '):
    os.system("stty -echo")
    password = input(prompt)
    os.system("stty echo")
    print("\n")
    return password

# Prompts the user for a yes/no answer.
#
# Prompt is just the prompt (suffixed by a "[y/n]" style string).
# Default can be None (ie user must specifically type y or n),
# 'y' or True (ie if the user presses enter 'y' is assumed)
# 'n' or False (ie if the user presses enter 'n' is assumed).
def ask_yn(prompt, default = None):
    prompt_suffix = None

    if default in [ False, 'n', 'N' ]:
        prompt_suffix = '[y/N]'
        default = False

    elif default in [ True, 'y', 'Y' ]:
        prompt_suffix = '[Y/n]'
        default = True

    else:
        prompt_suffix = '[y/n]'
        default = None

    while True:
        answer = input(prompt + ' ' + prompt_suffix + ' ')
        if answer.lower() in ['y', 'yes']:
            return True
        elif answer.lower() in ['n', 'no']:
            return False
        elif answer.lower().strip() == '' and default != None:
            return default

        else:
            # loop again
            continue

# Instance that marks a line
LINE = object()
class Column(object):
    # Create a column instance.
    #
    # name is the name of the column.
    # format is a printf-style format string that is applied to every value;
    #	this can be used in conjunction with formatters to support custom
    #	format strings.
    # width is the width of the column. every value is padded to this length
    #	so that the column has a fixed width when printed by the ColumnPrinter.
    #	If zero, no padding is done and the ColumnPrinter will size the column
    #	according to the longest value entered.
    # index is the column index as it appears in the ColumnPrinter
    # formatters is a list of functions which should take two arguments, and
    #	can be used to support custom format strings.
    #
    # Example of formatter function:
    #
    # def custom_fmt(format, value):
    #   if format == '%date':
    #		asrt(type(value) is datetime, 'value must be datetime')
    #		return value.strftime('yyyymmdd')
    #	else: return None
    #
    # If the formatter function returns None the next formatter (and ultimately
    # the default formatter, which delegates to printf) is used. You should
    # use asserts to check the type of value before formatting it, and give
    # helpful error messages if the type is wrong.
    #
    def __init__(self, name, fmt, width, index, formatters = [], auto_shorten = True):
        self.name = name
        self.fmt = fmt
        self.width = width
        self.index = index
        self.auto_width = True
        self.auto_shorten = auto_shorten

        if width > 0: self.auto_width = False

        self.formatters = formatters
        self.values = []
        self.no_format = []

    def __len__(self):
        return len(self.values)

    def add_value(self, value):
        self.values.append(value)

    def add_value_no_format(self, value):
        self.values.append(value)
        self.no_format.append(len(self.values)-1)

    def add_line(self):
        self.values.append(LINE)

    def get_values_printable(self):
        # now we have all the values, render them as strings
        # with the correct widths and formatting

        result = []
        for i in range(0, len(self.values)):
            if self.values[i] == LINE:
                value = '-'*self.width

            elif i in self.no_format:
                value = self.values[i]
                value = self._format_width(value)

            else:
                value = self.values[i]
                value = self._format(value)
                value = self._format_width(value)

            if self.auto_shorten and self.width > 0:
                value = shorten(value, self.width)

            result.append(value)

        return result

    def _format(self, value):
        if value == None: return ''

        for formatter in self.formatters:
            asrt(type(formatter) is types.FunctionType, 'formatter is not a function')
            new_val = formatter(self.fmt, value)

            if new_val != None: return new_val

        # if we get here none of the formatters returned anything,
        # so fall back to default
        return self.fmt % (value)

    def _format_width(self, value):
        s = value
        if self.width > 0:
            wfmt = '%' + str(self.width) + 's'
            s = wfmt % (s)
        return s

class ColumnPrinter(object):
    # Create a ColumnPrinter.
    #
    # See constructor docs for Column for info on the formatters argument.
    #
    def __init__(self, formatters = [], column_padding = '|'):
        self.columns = []
        self.formatters = formatters
        self.column_padding = column_padding

    # Create a ColumnPrinter.
    #
    # If auto_header is True and name is not None, the column returned will have
    # the name automatically added as the first value.
    #
    # See constructor docs for Column for info on the arguments.
    #
    def add_column(self, name = None, fmt = None, width = 0, auto_header = True, auto_shorten = True):
        new_index = len(self.columns)
        new_column = Column(name, fmt, width, new_index, self.formatters, auto_shorten)

        self.columns.append(new_column)

        if auto_header and name: new_column.add_value_no_format(name)

        return new_column

    # Adds a line across all columns
    def add_line(self):
        for c in self.columns:
            c.add_line()

    # Adds a blank line across all columns
    def add_blank_line(self):
        for c in self.columns:
            c.add_line()

    # Print out all the columns with all their values.
    #
    def print_table(self):
        longest_column = 0
        for c in self.columns:
            longest_column = max(longest_column, len(c))

        lines = ['']*longest_column

        for c in self.columns:
            line_number = 0
            for line in c.get_values_printable():
                lines[line_number] += self.column_padding + line
                line_number += 1

        for line in lines:
            print(line)

# Shortens a string to the specified length
def shorten(s, length, shortened_suffix = '..'):
    if s == None: return ''
    if len(s) <= length: return s

    result = s[0:length - len(shortened_suffix)]
    result += shortened_suffix

    return result

# convert a string coming from excel into a float
#
# All of None, '', '0.0', '0', '-' will become 0.0f.
# (123) is converted to -123.
# Parsing of thousands separators is supported.
# Trailing % signs are stripped.
def to_float(s):
    if s == None: return 0.0
    if type(s) is float: return s
    if type(s) is int: return float(s)

    # we assume at this point s is a string-like object
    if s.strip() == '': return 0.0
    if s.strip() == '-': return 0.0

    # replace '123,456,789.00' to '123456789.00'
    result = re.sub('(\d{1,3}),', '\\1', s.strip())

    # change '(xx)' to '-xx'
    result = re.sub('^\((.+)\)$', '-\\1', result)

    # remove trailing % signs
    result = re.sub('%$', '', result)

    return float(result)

def splitpath(path):
    # use os.path to split a path into each of its requisite bits
    result = []
    current_path = path
    while current_path != '/':
        result.append(os.path.basename(current_path))
        current_path = os.path.normpath(current_path + '/..')

    result.reverse()
    return result

# like os.path.join, but can handle any number
# of items
def join(*paths):
    result = ''
    for path in paths:
        if type(path) in [ list, tuple ]:
            # call recursively to try to
            # flatten out
            for ppath in path:
                path = join(path)

        # assume that here path is string or unicode
        result = os.path.join(result, str(path))

    return result

class DataHolder(object):
    """
    Implementation of a 'DataHolder' pattern to simulate
    assignment in if statements, as demonstrated here:
    http://stackoverflow.com/questions/2603956/can-we-have-assignment-in-a-condition

    To use:

    data = DataHolder()

    if data.set(my_expression()):
        x = data.get()
        # use x...

    elif data.set(my_other_expression()):
        x = data.get()
        # use x...

    Note that data.get() clears the DataHolder to protect against
    get() being called accidentally later on later in the cycle.
    Thus, calling get() twice in succession will result in an exception
    on the second call.
    """
    def set(self, x):
        self.data = x
        return x

    def get(self):
        x = self.data
        delattr(self, 'data')
        return x

def convert_datetime_to_seconds_since_epoch(d):
    # http://stackoverflow.com/a/11743262
    return (d - datetime.datetime(1970,1,1)).total_seconds()
