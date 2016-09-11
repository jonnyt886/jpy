#!/usr/bin/env python2
# Represents a simple config file system, supporting importing, comments,
# type-validate and pattern validation.
#

# TODO
# - add support for lists (i.e. if importing another file with a list of values, merge the lists rather than overwrite)
#		-> some code to support this is commented out in _set_attr

import re, os
from jpy.util import expand, match_groups
from jpy.asrt import *

# Regex for values (e.g. "mykey = myval")
VALUE_REGEX = re.compile('\s*([^\s]+)\s*=\s*(.*)\s*')

# Comment regex (e.g. "# some comment")
COMMENT_REGEX = re.compile('^\s*#')

# Import regex (e.g. "import somefile")
IMPORT_REGEX = re.compile('^import (.+)$')

# Used to match trailing slashes (for line-continuation)
NEWLINE = re.compile('.*(\\\\[\\r\\n]+)$')


def convert_to_bool(s):
    """Intelligently converts a string to a bool.
    All of 'yes', 'true', 'on', '1' convert to True.
    All of 'no', 'false', 'off', '0' convert to False.
    """
    # values for booleans
    TRUE = [ 'yes', 'true', 'on', '1' ]
    FALSE = [ 'no', 'false', 'off', '0' ]

    t = type(s)

    # deliberately don't handle None as we want to preserve
    # the distinction between a bool being set and not being set

    if t is bool:
        return s

    elif t in [list, tuple]:
        if len(s) == 0: return False
        s = s[0].lower()

    # if we get here it must be a string, otherwise die
    asrt(t in [str, str])
    if s in TRUE: return True
    elif s in FALSE: return False

    else: raise ValueError('invalid boolean value: ' + str(s))


def convert_value(value, val_type):
    """Convert the given value to the correct type as determined
    by config_value. Assumes that value is a string."""
    # deliberately public so that other modules can call this

    # always preserve None-ness
    if value == None: return None

    # handle bools especially
    if val_type == bool:
        return convert_to_bool(value)
    else:
        return val_type(value)

class ConfigFile(object):
    def __init__(self, config_file, defaults = {},
                 must_exist = True, config_values = None):
        """Initialise the ConfigFile.
        
        config_file is the path to a file that we can parse.
        defaults is an optional dict of default key->value
            pairs to use (added into the config file after the
            file is loaded for unset keys)
        must_exist, if false, allows you to create a blank
            ConfigFile, in which case config_file doesn't need
            to exist.
        config_values, if specified, should be a list of
          ConfigValue instances, which provide configuration
          for settings which will be stored in this ConfigFile.
        
        If config_values is specified:
        - all settings in files loaded into the ConfigFile
          must have a corresponding ConfigValue with the same
          name
        - all return values of get() will be converted according
          to the corresponding ConfigValue's val_type
        - default values will be returned by get() if the
          setting requested is not present and the corresponding
          ConfigValue has a default_value set
        """
        self.items_dict = {}
        self.must_exist = must_exist

        self.config_values = None
        if config_values:
            self.config_values = { x.name.lower(): x for x in config_values }

        # store values in a list too so that we get ordering?
        self.items = []

        self.config_file = config_file
        self.defaults = defaults

        # store the lines in the config file (just the ones
        # directly in this file, not imported files) so that
        # we can save the file back as it was when set() is called
        self.lines = []

        # dict of key -> line number (mapping to items in self.lines)
        # so that set() is able to modify values in specified lines.
        # this dict will not contain mappings for blank lines or comments
        self.line_numbers = {}

        self._read_file()

    def _read_file(self):
        if not self.config_file: return

        exists = os.path.exists(self.config_file)
        if not exists and self.must_exist:
            raise ValueError('file does not exist: ' + \
                             self.config_file)

        if exists:
            previous_line = None

            line_number = -1
            for line in open(self.config_file, 'r'):
                line_number += 1
                self.lines.append(line.rstrip('\n\r'))
                asrt_eq(len(self.lines)-1, line_number)

                if previous_line != None:
                    line = previous_line + line.lstrip()
                    previous_line = None

                newline_match = match_groups(NEWLINE, line)
                if newline_match:
                    previous_line = line[:-len(newline_match[0])]
                    continue

                if line.strip() == '':
                    continue

                comment_match = COMMENT_REGEX.match(line)
                value_match = VALUE_REGEX.match(line)
                import_match = IMPORT_REGEX.match(line)

                if comment_match != None:
                    # Ignore as this line is a comment line
                    pass

                elif value_match != None:
                    groups = value_match.groups()
                    self._set_attr(groups[0], groups[1])

                    self.line_numbers[groups[0]] = line_number

                elif import_match != None:
                    groups = import_match.groups()

                    c = ConfigFile(expand(groups[0]))
                    self.import_configfile(c)

                else:
                    raise ValueError('Line "' + line + \
                                     '" in file "' + self.config_file + \
                                     '" is not in the right format')

        for (k, v) in list(self.defaults.items()):
            if not self.has(k):
                self._set_attr(k, v)

    def import_configfile(self, configfile, overwrite = False):
        """Import the items in another configfile into this configfile
        
        If overwrite is True, any values that exist in this
        instance and also in configfile are overwritten by the ones in
        configfile. if overwrite is False, the values in this instance
        are preserved.
        """
        asrt(type(configfile) is ConfigFile, 'configfile must be a ConfigFile instance (was ' + str(type(configfile)) + ', ' + str(configfile) + ')')

        for name, value in list(configfile.get_all().items()):
            if self.has(name) and not overwrite: continue

            self._set_attr(name, value)

    def _set_attr(self, name, value):
        if name.startswith('_'):
            raise ValueError('Bad property name "' + name + '", cannot set attributes starting with _')

        cv = self.get_configvalue(name)
        if cv:
            value = convert_value(value, cv.val_type)

        self.items_dict[name] = value

    def get_configvalue(self, name):
        """look up a ConfigValue
        
        returns None if ConfigValues have not been set for this ConfigFile
        """
        if not self.config_values: return None

        n = name.lower()
        if not n in list(self.config_values.keys()):
            raise ValueError('Error in ' + self.config_file + ', property "' + name + '" invalid; no corresponding ConfigValue')

        return self.config_values[n]


    def get(self, name, val_type = None):
        """Retrieve a setting from the ConfigFile.
        
        If this ConfigFile has been configured with ConfigValues,
        and the corresponding ConfigValue for `name` has a default_value
        set, that value is returned if it does not exist in the ConfigFile.
        
        val_type can be specified, in which case the type of the value
        returned can be specified. This is most useful in cases where
        ConfigValues are being used to specify different datatypes; val_type
        can be specified to make the code more readable and to give you
        assurance that you'll get a certain type back.
        NB In practice setting val_type does not cause conversions to be
        performed. If set, the val_type is compared with the actual return
        type and an exception is thrown if they do not match.
        """
        result = None

        if name in self.items_dict:
            result = self.items_dict[name]
        else:
            cv = self.get_configvalue(name)
            if cv: result = cv.default_value

        # validate type against val_type
        if val_type and (val_type != type(result)):
            raise ValueError('Value for "' + name + '" is wrong type.' + \
                             'Expected: ' + str(val_type) + ', actual: ' + str(type(result)))

        return result

    def get_bool(self, name):
        """get as a boolean."""
        if not self.has(name): return False

        s = self.get(name)
        return convert_to_bool(s)

    def has(self, name):
        return name in self.items_dict


    def get_single(self, name):
        """Get a single property by name. An exception is thrown
        if more than one property by this name exists"""
        result = self.get_list(name)
        if len(result) > 1:
            raise ValueError('More than one value has been assigned for setting ' + name)

        # values are already unpacked by get_list()
        return result[0]

    def get_all(self, prefix=None):
        """Get all properties. (Meaning only those defined; for example, those
        where defaults have been set are *not* included in the return value
        for this method.)
        
        If prefix is specified, only return those with that prefix"""
        if prefix is None:
            return dict(self.items_dict)

        else:
            result = {}
            prefixl = prefix.lower()

            for (k, v) in list(self.items_dict.items()):
                if k.lower().startswith(prefixl):
                    result[k] = v

            return result

    def set(self, key, value, write = True):
        """set a value in the config file and write the config file to disk
        
        if write is False, do not write to disk, just keep the new value in
        memory"""
        cv = self.get_configvalue(key)
        self._set_attr(key, value)

        line_number = self.line_numbers.get(key)

        new_line = '%s = %s' % (key, value)

        if line_number is not None:
            self.lines[line_number] = new_line
        else:
            self.lines.append('')
            self.lines.append(new_line)
            self.line_numbers[key] = len(self.lines)-1

        if write:
            with open(self.config_file, 'w') as f:
                for line in self.lines:
                    f.write(line)
                    f.write('\n')

    def set_with_dict(self, values, write = True):
        """set several values in the config file and write the config file to disk
        
        if write is False, do not write to disk, just keep the new value in
        memory
        values should be a dict consisting of keys->values to write
        """
        for key, value in list(values.items()):
            cv = self.get_configvalue(key)
            self._set_attr(key, value)

            line_number = self.line_numbers.get(key)

            new_line = '%s = %s' % (key, value)

            if line_number is not None:
                self.lines[line_number] = new_line
            else:
                self.lines.append('')
                self.lines.append(new_line)
                self.line_numbers[key] = len(self.lines)-1

        if write:
            with open(self.config_file, 'w') as f:
                for line in self.lines:
                    f.write(line)
                    f.write('\n')

class ConfigValue(object):
    """Represents a configuration value (or rather, the configuration
    of that configuration value)."""
    def __init__(self, name, default_value = None, val_type = str):
        self.name = name
        self.default_value = default_value
        self.val_type = val_type

        # ensure the ConfigValue's default_value is the right type
        if type(self.default_value) != self.val_type:
            self.default_value = convert_value(self.default_value, self.val_type)
