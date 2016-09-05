# General-purpose util module

import os, locale, sys, select, re, types, datetime
from .asrt import *
import imp

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

def print_safely(s):
    """
    Print the given string, hacking the default encoding to ensure
    that we don't balk at UTF-8 strings.

    This is DANGEROUS and should be used for debugging only, not production code,
    as it can break 3rd party code if the default encoding is left at UTF-8.

    see http://www.ianbicking.org/illusive-setdefaultencoding.html
        and http://stackoverflow.com/questions/2276200/changing-default-encoding-of-python
    :param s:
    :return:
    """
    import sys
    orig_encoding = sys.getdefaultencoding()
    imp.reload(sys)
    sys.setdefaultencoding('utf-8')

    print(s)

    sys.setdefaultencoding(orig_encoding)

suppress_py3_unicode_calls = False
def to_unicode(text):
    """ Convert, at all consts, 'text' to a `unicode` object.

    Note: as a last-ditch effort, this function tries to decode the text
          as latin1... Which will always succeed.  If you expect to get
          text encoded with latin[2-9] or some other character set, this
          may not be desierable.
    """
    global suppress_py3_unicode_calls

    if not suppress_py3_unicode_calls and sys.version[0:1] == '3': 
        print('warning: to_unicode() called inside python3 application (subsequent calls will be suppressed)', file=sys.stderr)
        suppress_py3_unicode_calls = True
        return text

    if text is None: return None

    if type(text) is list:
        return [to_unicode(s) for s in text]

    if type(text) is str:
        # verify we can decode to utf8
        text.encode('utf-8')
        return text

    if hasattr(text, '__unicode__'):
        return text.__unicode__()

    text = str(text)

    try:
        return str(text, 'utf-8')
    except UnicodeError:
        pass

    try:
        return str(text, locale.getpreferredencoding())
    except UnicodeError:
        pass

    return str(text, 'latin1')


def to_str(text):
    """ Convert 'text' to a `str` object.

        >>> to_str(u'I\xf1t\xebrn\xe2ti')
        'I\xc3\xb1t\xc3\xabrn\xc3\xa2ti'
        >>> to_str(42)
        '42'
        >>> to_str('ohai')
        'ohai'
        >>> class Foo:
        ...	 def __str__(self):
        ...	     return 'foo'
        ...
        >>> f = Foo()
        >>> to_str()
        'foo'
        >>> f.__unicode__ = lambda: u'I\xf1t\xebrn\xe2ti'
        >>> to_str(f)
        'I\xc3\xb1t\xc3\xabrn\xc3\xa2ti'
        >>> """

    if type(text) is list:
        result = []
        for s in text:
            result.append(to_str(s))

        return result

    if isinstance(text, str):
        return text

    if hasattr(text, '__unicode__'):
        text = text.__unicode__()

    if hasattr(text, '__str__'):
        return text.__str__()

    return text.encode('utf-8')

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

# Get the size of the terminal (char height, char width). This ONLY works on a UNIX-like
# terminal; an empty tuple will be returned for other platforms.
# Taken from http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
def get_terminal_size():
    """
    returns (lines:int, cols:int)
    """
    #    import os, struct
    #    def ioctl_GWINSZ(fd):
    #        import fcntl, termios
    #        return struct.unpack("hh", fcntl.ioctl(fd, termios.TIOCGWINSZ, "1234"))
    #    # try stdin, stdout, stderr
    #    for fd in (0, 1, 2):
    #        try:
    #            return ioctl_GWINSZ(fd)
    #        except:
    #            pass
    #    # try os.ctermid()
    #    try:
    #        fd = os.open(os.ctermid(), os.O_RDONLY)
    #        try:
    #            return ioctl_GWINSZ(fd)
    #        finally:
    #            os.close(fd)
    #    except:
    #        pass
    # try `stty size`
    try:
        return tuple(int(x) for x in os.popen("stty size", "r").read().split())
    except:
        pass
    # try environment variables
    try:
        return tuple(int(os.getenv(var)) for var in ("LINES", "COLUMNS"))
    except:
        pass
    # i give up. return default.
    return (25, 80)

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

def getTerminalSize():
    import platform
    current_os = platform.system()
    tuple_xy=None
    if current_os == 'Windows':
        tuple_xy = _getTerminalSize_windows()
        if tuple_xy is None:
            tuple_xy = _getTerminalSize_tput()
            # needed for window's python in cygwin's xterm!
    if current_os == 'Linux' or current_os == 'Darwin' or  current_os.startswith('CYGWIN'):
        tuple_xy = _getTerminalSize_linux()
    if tuple_xy is None:
        print("default")
        tuple_xy = (80, 25)      # default value
    return tuple_xy

def _getTerminalSize_windows():
    res=None
    try:
        from ctypes import windll, create_string_buffer

        # stdin handle is -10
        # stdout handle is -11
        # stderr handle is -12

        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
    except:
        return None
    if res:
        import struct
        (bufx, bufy, curx, cury, wattr,
         left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
        sizex = right - left + 1
        sizey = bottom - top + 1
        return sizex, sizey
    else:
        return None

def _getTerminalSize_tput():
    # get terminal width
    # src: http://stackoverflow.com/questions/263890/how-do-i-find-the-width-height-of-a-terminal-window
    try:
        import subprocess
        proc=subprocess.Popen(["tput", "cols"],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        output=proc.communicate(input=None)
        cols=int(output[0])
        proc=subprocess.Popen(["tput", "lines"],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        output=proc.communicate(input=None)
        rows=int(output[0])
        return (cols,rows)
    except:
        return None


def _getTerminalSize_linux():
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,'1234'))
        except:
            return None
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            cr = (sys.env['LINES'], sys.env['COLUMNS'])
        except:
            return None
    return int(cr[1]), int(cr[0])

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

# Provides easy-to-ease compare features for Python objects.
#
# To use, create a comparator as a constant:
#   COMPARATOR = util.GenericComparator(['name'])
#
# (The argument should be a list of fields to compare, defining the
#  sort order. They can be any type.)
#
# Then, in your class, implement __lt__ and __gt__:
# 
#	def __gt__(self, other):
#		return COMPARATOR.gt(self, other)
#
#	def __lt__(self, other):
#		return COMPARATOR.lt(self, other)
#
# You can also implement __eq__ and __ne__ but this
# is usually less useful and potentially dangerous
# unless you include every field in your class in the
# sort order.
#
# It's usually better to keep your __eq__ and __ne__ implementations
# separate from this, so that you can sync them with hash and so that
# changing the comparator's sort order in the future doesn't introduce
# strange bugs. (Remember, lists and dicts use eq() and hash() heavily.)
#
class GenericComparator(object):
    def __init__(self, fieldnames = []):
        self.fieldnames = fieldnames

    def _yield_field_values(self, o1, o2):
        for fieldname in self.fieldnames:
            o1val = getattr(o1, fieldname)
            o2val = getattr(o2, fieldname)

            yield (o1val, o2val)

    def _key(self, o):
        return [(getattr(o, x)) for x in self.fieldnames]

    def eq(self, o1, o2):
        return self._key(o1) == self._key(o2)

    def ne(self, o1, o2):
        return self._key(o1) != self._key(o2)

    def lt(self, o1, o2):
        return self._key(o1) < self._key(o2)

    def gt(self, o1, o2):
        return self._key(o1) > self._key(o2)

#	def eq(self, o1, o2):
#		for (o1val, o2val) in self._yield_field_values(o1, o2):
#			if o1val == o2val: continue
#			if o1val != o2val: return False
#			# if they're equal keep running the loop
#
#		return True
#
#	def ne(self, o1, o2):
#		for (o1val, o2val) in self._yield_field_values(o1, o2):
#			if o1val == o2val: return False
#			if o1val != o2val: continue
#			# if they're equal keep running the loop
#
#		return True
#
#	def lt(self, o1, o2):
#		for (o1val, o2val) in self._yield_field_values(o1, o2):
#			if o1val < o2val: return True
#			if o2val > o1val: return False
#			# if they're equal keep running the loop
#
#		return False
#
#	def gt(self, o1, o2):
#		for (o1val, o2val) in self._yield_field_values(o1, o2):
#			if o1val > o2val: return True
#			if o2val < o1val: return False
#			# if they're equal keep running the loop
#
#		return False


# RollerUpper - a Python implementation of fstat's TransactionAnalyser,
# abstracted to be usable with any class containing any fields.
#
RU_COMPARATOR = GenericComparator(['name'])
class RollerUpper(object):
    # name can be anything, including None
    # key can also be anything, including None
    #
    # data should be a list of objects
    # children should be a list of RollerUppers
    #
    # either data or children must be specified
    def __init__(self, name = None, key = None, data = None, children = None):
        asrt(not (data == None and children == None), 'data or children must be specified')
        asrt(not (data and children), 'data or children must be specified, not both')

        self.name = name
        self.key = key

        if data != None:
            self.data = data
            self.children = None

        if children != None:
            self.children = children
            self.data = []
            for c in self.children:
                self.data.extend(c.data)

    def __gt__(self, other):
        return RU_COMPARATOR.gt(self, other)

    def __lt__(self, other):
        return RU_COMPARATOR.lt(self, other)


    # Group a hierarchy of RUs by a named field in each data item.
    #
    # A new RU is created beneath this RU for each unique value of
    # field_name in the items in self.data.
    #
    # Each RU will be given the name equal to str(value of field_name)
    # unless name_field is specified, in which case getattr(name_field)
    # is done on each value, converted to a string and used instead.
    #
    # Note, field_name can also be a code snippet, provided as a string.
    # If field_name contains '.' or '(', this function assumes it is a
    # code snippet of some sort and will exec() it, prepending the item.
    # For example, if the RU contains orders, containing dates, I can call
    # group_hierarchy_by('date.year') to group the orders by year (assuming
    # the date field is called 'date' of course). I could also do
    # group_hierarchy_by('date.year % 2') to split into even/odd years for
    # example.
    #
    # With CGIWeeks, this allows us to do week.month, or week.month.fy.
    #
    def group_hierarchy_by(self, field_name, name_field = None):
        if self.children == None:
            self._group_by(field_name, name_field)

        else:
            for c in self.children:
                c.group_hierarchy_by(field_name, name_field)

    # Clear all groupings
    def reset(self):
        self.children = None

    def _group_by(self, field_name, name_field = None):
        # If field_name contains brackets or full stops, it is
        # probably code making a function call or digging into
        # field values several depths down.
        # In which case we use exec() to execute this code directly.
        # Dangerous but handy.
        do_exec = ('.' in field_name) or ('(' in field_name)

        group = {}

        for d in self.data:
            if do_exec:
                exec('val = d.' + field_name)

            else:
                val = getattr(d, field_name)

            if val not in list(group.keys()):
                group[val] = []

            group[val].append(d)

        unknown_data = []
        self.children = []
        for (k, v) in group.items():
            name = str(k)
            key = k
            if key == None:
                unknown_data.extend(v)

            else:
                if name_field:
                    key = getattr(k, name_field)
                    name = str(key)

                self.children.append(RollerUpper(name=name, key=key, data=v))

        if unknown_data:
            self.children.append(RollerUpper(name='Unknown', key=None, data=unknown_data))

        self.children.sort()

    def get_first(self, field_name):
        if not self.data: return None
        return getattr(self.data[0], field_name)

    def get_all(self, field_name):
        result = []
        for d in self.data:
            val = getattr(d, field_name)
            result.append(val)

        return result

    def __iter__(self):
        for c in self.data:
            yield c

    def __repr__(self):
        return 'RollerUpper[name=' + str(self.name) + \
               ',len_children=' + str(len(max(self.children, []))) + \
               ',len_data=' + str(len(self.data)) + \
               ',children=' + str(self.children) + \
               ',data=' + str(self.data) + \
               ']'

    def get_all_children_names(self):
        return [ x.name for x in self.children ]

    # Get all 'leaf' nodes in this RU tree - i.e. all the children
    # as far down as each line of RUs will go.
    def get_all_children(self):
        result = []
        for c in self.children:
            if c.children != None:
                result.extend(c.get_all_children())

            else:
                result.append(c)

        return result

    # Get all children whose names equal name, as a new RollerUpper.
    #
    # Warning: this does string comparison to compare names
    # _first_only is an internal arg used to implement get_child(),
    # 	it causes the function to return once an item has been found
    def get_children(self, name=None, key=None, recursive = True, _first_only = False):
        result = []
        asrt(not (name == None and key == None), 'must specify name or key')

        # note: currently this will blow up if there are children == None
        for c in self.children:
            # since all names are strings, insist on string comparison
            if name != None:
                if str(c.name) == str(name): result.append(c)
            elif key != None:
                if c.key == key: result.append(c)

            if recursive and c.children != None:
                result.extend(c.get_children(name=name, key=key,
                                             recursive=recursive).children)

            if _first_only and result: break

        return RollerUpper(name=name, key=key, children=result)

    # get_children but returns only the first item found, or None
    # if it wasn't found
    def get_child(self, name, recursive = True):
        result = self.get_children(name, recursive, _first_only=True)

        if result.children: return result.children[0]
        return None

# Like RollerUpper but is immutable. It inherits from RollerUpper but 
# returns new instances for grouping and reset() methods.
#
# The idea is that in your code where you need to use an RU to do 
# analysis, you make a call to this IRU, which gives you a mutable RU, 
# which you can then work with and use however you wish without affecting 
# the IRU's state.
#
# This is handy for objects that want to present their data as RUs for
# easy analysis without having to become mutable.
#
class ImmutableRollerUpper(RollerUpper):
    def __init__(self, name = None, data = None, children = None):
        RollerUpper.__init__(self, name=name, data=data, children=children)

    def group_hierarchy_by(self, field_name, name_field = None):
        # return a new RU instance first
        result = self.mutable()
        result.group_hierarchy_by(field_name, name_field)

        return result

    # return a mutable copy of this IRU
    def mutable(self):
        # return a new RU instance first
        return RollerUpper(name=self.name, data=self.data, children=self.children)

    def reset(self):
        # do nothing
        pass

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
