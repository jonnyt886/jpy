# jpy
Group of python utility modules for various useful things

## Asserts
Being from a Java background, I'm used to using assert() in unit tests, as we do in Python. Over the years various Java libraries made available "assert" or "check" methods that could be used in production code for validating variables in one line. The `jpy.asrt` module does exactly this. Thus instead of:

```
def myfunc(input):
    # input has to be not None and a number between 0 and 10
    if not input or input > 10 or input < 0:
        raise ValueError('input is None, or is not between 0 and 10: ' + str(input)

    # perform calculations...
```

You can do:
```
from jpy.asrt import *

def myfunc(input):
    # input has to be not None and a number between 0 and 10
    asrt_nn(input)
    asrt(input > 10 and input < 10)

    # perform calculations
```

Which I find much more readable. If the assertion fails, a ValueError is raised. `asrt` functions allow you to specify a 'warn' argument which causes a message to be printed to stderr and no exception.

## Weakref cache
This allows you to implement a simple in-memory cache. You specify how to load items into the cache given a particular key, and the rest is handled for you. It uses weakrefs, which allows the Python garbage collector to automagically expunge items from the cache when it needs to allocate more memory or when cached objects have not been in use for a period of time.

For example, I make use of this in my pymus project. It loads configuration files from `.pymusrc` files, which could be scattered across the filesystem. I don't want to have to keep going back to the filesystem everytime I need to read data from these files, so I divert them via a cache so that subsequent reads are quick. Here are excerpts from PyMusService, the class I use to orchestrate this (I've simplified it to bring out the cache-specific bits):

```
from jpy import cache

class PyMusService(object):
    def __init__(self, ...):
        # initialise the cache: pass the loader_func, which the cache calls if there is a cache miss (i.e.
        # a request is made for something that isn't yet in the cache) and throw an exception if the
        # loader function ever returns None
        self.cache = cache.WeakRefCache(loader_func = self.__load_pymusrc__, permit_none = False)

    def __load_pymusrc__(self, path):
        # loads configuration file and parses it
        configfile = configfile.ConfigFile(...)   # perform the load... slow and expensive
        ......

    def get_pymusrc(self, path):
        return self.cache.get(path)   # when a client asks for the data, go 'via' the cache. The cache instance
                                                           # checks its state and either returns it immediately from the cache or
                                                           # calls __load_pymusrc__() if it needs to perform an actual load from the
                                                           # filesystem.
```

If you're modifying the data you're loading through the cache, as I do in pymus, you'll need to delete items from the cache in order to force it reload the underlying data. This is done via cache.delete().

## Shell Colours
The colours module allows you to print coloured output on POSIX terminals that support it, including some Cygwin terminals. It's simple to use:

```
from jpy import colours
print(colours.RED + 'URGENT ' + colours.YELLOW + 'Your disks are full')
```

It supports these colours:
BLACK
BLUE
BROWN
CYAN
DBLUE
GREEN
GREY
LCYAN
LGREY
LGREEN
LPURPLE
LRED
NONE
PURPLE
RED
WHITE
YELLOW

I've never needed to add additional escape sequences but for some terminal applications this could be valuable. If you'd like to see additional properties here, submit a patch with your escape sequence and I'll include it.

The module also includes two methods: remove_colours() strips any known colours from a string, and expand_colours() takes a string with shell-style colour variables and replaces them (e.g. "${RED}URGENT ${YELLOW}Your disks are full").

## Running shell commands
Every casual Python scripter relies on external binaries for some things, and I'm sure everyone's written their own wrapper around Python's various in-built modules for doing this. Here's mine:

```
from jpy import command

# run a command and capture its result - running time, stdout, stderr, etc. The returned object is a CommandResult.
free_space = command.execute('df -h /')
print(free_space.stdout.split('\n'))

# run a command and allow it to interact with the terminal (i.e. don't grab its output)
command.execute('ssh-keygen', grab_output=False)

# by default, if a command returns a non-zero exit code an exception is raised, but this can be overridden
command.execute('df -h /non-existent-path', ignore_exit_code=True)

# you can also, if grab_output=True, supply a input to a command, effectively automating it.
# Beware that some binaries won't work with this, for good reason (e.g. ssh-keygen, sudo)
command.execute('read HELLO; echo Hello $HELLO', input_string='Jonny')

# Notice the last example used a shell construct - by default everything goes via /bin/bash.
# You can override this to be a different shell, or no shell:
command.execute('...', shell='/bin/zsh')
command.execute('...', shell=None)
```

## Configuration files
The configfile module gives you the ability to read/write configuration files with reasonable flexibility. I use this for pymus. Python includes the ConfigParser module, which provides a way to easily read configuration files, but I needed configuration files to be able to import one-another, and to have an easy API for writing validation of keys/values in a file.

It's a simple key/value pair format, and supports comments, but not the INI-style sections that ConfigParser does:

```
# comment
key = value1
key2 = value2
```

To use it:

```
# load a file
from jpy import configfile
c = configfile.ConfigFile('/path/to/file')
c.get('key')     # "value1"
c.get('key2')     # "value2"

# load a file with some default settings
c = configfile.ConfigFile('/path/to/file', defaults={'key3':'value3'})
c.get('key3')     # "value3"

# overlay one file over another, for example to import system-wide configuration
c = configfile.Configfile('$HOME/.myapp/config')
c2 = configfile.Configfile('/etc/myapp/config')
c.import(c2, overwrite=False)
```

The language of the config file allows you to import as well:

```
# comment
key = value
import /path/to/anotherfile
```

And when you load the file, /path/to/anotherfile will be loaded and included.

Yet the really useful feature for me is the validation you can add via ConfigValues (don't ask why I chose that name). These allow you to validate the content of your configuration, set default values, and perform type conversions transparently. For example, given this file:

```
filename = /home/jonny/myfile
allow-overwrite = yes
```

and this code:

```
config_values = [
    configfile.ConfigValue('filename'),
    configfile.ConfigValue('allow-overwrite', default_value=False, val_type=bool)
]

# load the file - when config_values is specified, an exception is thrown if the config file
# includes any keys which are not included in config_values
c = configfile.ConfigFile('/path/to/file', config_values = config_values)
c.get('filename')     # "/home/jonny/myfile"
c.get('allow-overwrite', val_type=bool)     # True
```

Notice that I specified val_type for that second call. This is simply there to improve the readability of the code: since get() can return
different datatypes depending on the key, you probably want to include val_type in most of your calls so that when you're debugging
your code you can see which type you were expecting back. If val_type isn't specified in the get(), but is in the ConfigValue, it will cast/convert
for you anyway. If val_type isn't specified anywhere, strings are assumed, which is why I didn't bother specifying a val_type for the 'filename' key anywhere.

Conversion is handled via the configfile.convert_value() function. It's trivial to override this with your own logic if needed. By default, if the desired type to convert to is a bool, it looks for any appropriate string ('y', 'yes', 'true', on') for True, and assumes False otherwise. For all other types it calls the type itself to convert (i.e. if val_type = int, it will call int(value) to perform the conversion).

Lastly, and this was vital for pymus, you can create ConfigFiles against files that do not exist. So, you can assume the existence of a file and
the code will handle it for you. By calling set(), you write the file to disk. I've written set() in such a way that it will preserve comments in the file when you prgrammatically change or add values.

```
c = configfile.ConfigFile('doesnotexist', defaults={'key1':'value1'})
c.get('key1')     # value1
c.set('key1', 'value2')     # writes a new 'doesnotexist' file to disk
```

## Perform checksums on files
The hashes module provides some shortcut methods for perfoming hashes of entire files. For example:

```
from jpy import hashes

hashes.md5_file('/path/to/file')
hashes.sha256_file('/path/to/file')
```

## Proxying
I also include rudimentary code to create your own object proxies, intercepting method calls to an underlying instance without the knowledge of the code around that instance being aware.

To use it, first create an interceptor class. I recommend you subclass the proxy.ProxyInterceptor class but this isn't strictly necessary as long as your def()s are correct (in true Pythonic fashion). If you subclass, you don't need to specify every function, just the ones you want to override.

Via the interceptor you can specify what you want to intercept. For example, to get notified when an attribute is retrieved, you would do this:

```
from jpy import proxy
class MyInterceptor(proxy.ProxyInterceptor):
     def on_get_attribute(self, obj, name):
          print('debug: get_attribute', name)
```

This will work only for non-callables; to do the same for callables, use on_get_callable(self, obj, name). There is also on_set_attribute() and on_del_attribute().

To intercept a getattribute, you would use get_attribute(), below. With this method, the return value matters: it is the value that will be passed back
to the caller. For example, you may want to change all gets for the 'message' attribute to return a string reading 'Hello, world':

```
def get_attribute(self, obj, name, value):
	if name == 'message': return 'Hello, world'
	return value
```

Note that I still need to return a sane value for the attributes I'm not interested in, otherwise every other getattribute() call would return None. This can also be done for function calls via on_call(). For example I may want to override a function called execute() for certain arguments:

```
     def on_call(self, obj, function, name, args, kwargs):
          if name == 'execute' and 'reboot' in args:
               raise ValueError('rebooting not allowed')
          return function(*args, **kwargs)
```

As before, the return value of this method will be the value returned to the caller. Note again how I handle calls other than execute() with a default return value. `function(*args, **kwargs)` simply calls the real underlying method.

To actually use the interceptor around a real object:

```
class A(object):
     def execute(name):
          print(name)

obj = A()
i = MyInterceptor()
p = proxy.Proxy(obj, i)

type(p)     # <class 'jpy.proxy.Proxy(A)'>
p.execute('test')     # "test"
p.execute('reboot')     # ValueError: rebooting not allowed
```
