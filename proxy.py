class MethodInvocation(object):
    """Represents a method invocation intercepted by the Proxy."""
    def __init__(self, obj, _callable, method_name, *method_args, **method_kwargs):
        self.obj = obj
        self.callable = _callable
        self.method_name = method_name
        self.method_args = method_args
        self.method_kwargs = method_kwargs

    def invoke(self):
        return self.callable(*self.method_args, **self.method_kwargs)


class ProxyInterceptor(object):
    """Instances of this class can be added to a Proxy instance,
    and methods will then be called when attributes are read, written
    or deleted or method calls made on that Proxy instance."""

    def on_get_attribute(self, obj, name):
        """Called when __getattribute__ is called on the Proxy.
        (NB this is NOT called if callables are retrieved, such
        as a function; see on_get_function().)"""
        pass

    def get_attribute(self, obj, name, value):
        """Called when __getattribute__ is called on the Proxy.
        (NB this is NOT called if callables are retrieved, such
        as a function; see on_get_function().)

        This function allows you to intercept and override the value
        returned. value is the value of the attribute on the
        proxied object."""
        return value

    def on_get_callable(self, obj, name):
        """Called when any callable object is retrieved from the Proxy
        via __getattribute__(). See on_call() for the hook for when a
        callable from the Proxy is subsequently called."""
        pass

    def on_call(self, invocation):
        """Called when a callable (such as a function), previously
        retrieved from the Proxy, is called. invocation is an instance
        of MethodInvocation.

        NOTE: the return value passed back to whatever called the method
        will be the return value of this method. If you want to run
        the real underlying method on the proxied object, use invocation.invoke()."""
        return invocation.invoke()

    def on_set_attribute(self, obj, name, value):
        """Called when __setattribute__ is called on the Proxy."""
        pass

    def on_del_attribute(self, obj, name):
        """Called when __delattr__ is called on the Proxy."""
        pass


class DebugProxyInterceptor(ProxyInterceptor):
    """Example interceptor implementation."""

    def on_get_attribute(self, obj, name):
        print(('oga', name))

    def on_get_callable(self, obj, name):
        print(('ogc', name))

    def on_call(self, invocation):
        print(('oc', invocation.method_name, invocation.method_args, invocation.method_kwargs))
        return invocation.invoke()

    def on_set_attribute(self, obj, name, value):
        print(('osa', name, value))

    def on_del_attribute(self, obj, name):
        print(('oda', name))

class Proxy(object):
    """Construct proxies for Python objects. Based on code at
    http://code.activestate.com/recipes/496741-object-proxying/"""

    __slots__ = ["_obj", "__weakref__", "_interceptor"]

    def __init__(self, obj, interceptor):
        # have to use object.*() methods to ensure we don't trigger our
        # own proxy-esque code below
        object.__setattr__(self, "_obj", obj)
        object.__setattr__(self, "_interceptor", interceptor)

    #
    # proxying (special cases)
    #
    def __getattribute__(self, name):
        # print 'Proxy.__getattribute__(%s)'%(name)
        _obj = object.__getattribute__(self, "_obj")
        _interceptor = object.__getattribute__(self, "_interceptor")

        result = getattr(_obj, name)

        if hasattr(result, '__call__'):

            def call_it(*args, **kwargs):
                invocation = MethodInvocation(_obj, result, name, *args, **kwargs)
                # print 'Proxy.call_it(%s)'%(name)
                return _interceptor.on_call(invocation) #result(*args, **kwargs)
            return call_it

        else:
            _interceptor.on_get_attribute(_obj, name)
            result2 = _interceptor.get_attribute(_obj, name, result)
            return result2

    def __delattr__(self, name):
        # print 'Proxy.__delattr__(%s)'%(name)
        _obj = object.__getattribute__(self, "_obj")
        _interceptor = object.__getattribute__(self, "_interceptor")

        _interceptor.on_del_attribute(_obj, name)
        delattr(_obj, name)

    def __setattr__(self, name, value):
        # print 'Proxy.__setattr__(%s, %s)'%(name, value)
        _obj = object.__getattribute__(self, "_obj")
        _interceptor = object.__getattribute__(self, "_interceptor")

        _interceptor.on_set_attribute(_obj, name, value)
        setattr(_obj, name, value)

    def __bool__(self):
        _obj = object.__getattribute__(self, "_obj")
        return bool(_obj)

    def __str__(self):
        _obj = object.__getattribute__(self, "_obj")
        return str(_obj)

    def __repr__(self):
        _obj = object.__getattribute__(self, "_obj")
        return repr(_obj)

    #
    # factories
    #
    _special_names = [
        '__abs__', '__add__', '__and__', '__call__', '__cmp__', '__coerce__',
        '__contains__', '__delitem__', '__delslice__', '__div__', '__divmod__',
        '__eq__', '__float__', '__floordiv__', '__ge__', '__getitem__',
        '__getslice__', '__gt__', '__hash__', '__hex__', '__iadd__', '__iand__',
        '__idiv__', '__idivmod__', '__ifloordiv__', '__ilshift__', '__imod__',
        '__imul__', '__int__', '__invert__', '__ior__', '__ipow__', '__irshift__',
        '__isub__', '__iter__', '__itruediv__', '__ixor__', '__le__', '__len__',
        '__long__', '__lshift__', '__lt__', '__mod__', '__mul__', '__ne__',
        '__neg__', '__oct__', '__or__', '__pos__', '__pow__', '__radd__',
        '__rand__', '__rdiv__', '__rdivmod__', '__reduce__', '__reduce_ex__',
        '__repr__', '__reversed__', '__rfloorfiv__', '__rlshift__', '__rmod__',
        '__rmul__', '__ror__', '__rpow__', '__rrshift__', '__rshift__', '__rsub__',
        '__rtruediv__', '__rxor__', '__setitem__', '__setslice__', '__sub__',
        '__truediv__', '__xor__', 'next',
    ]

    @classmethod
    def _create_class_proxy(cls, theclass):
        """creates a proxy for the given class"""

        def make_method(name):
            def method(self, *args, **kw):
                print(('Proxy.[class_proxy].method(%s)'%(name)))
                _obj = object.__getattribute__(self, "_obj")
                return getattr(_obj, name)(*args, **kw)
            return method

        namespace = {}
        for name in cls._special_names:
            if hasattr(theclass, name):
                namespace[name] = make_method(name)
        return type("%s(%s)" % (cls.__name__, theclass.__name__), (cls,), namespace)

    def __new__(cls, obj, *args, **kwargs):
        """
        creates an proxy instance referencing `obj`. (obj, *args, **kwargs) are
        passed to this class' __init__, so deriving classes can define an
        __init__ method of their own.
        note: _class_proxy_cache is unique per deriving class (each deriving
        class must hold its own cache)
        """
        # print 'Proxy.__new__()'

        try:
            cache = cls.__dict__["_class_proxy_cache"]
        except KeyError:
            cls._class_proxy_cache = cache = {}
        try:
            theclass = cache[obj.__class__]
        except KeyError:
            cache[obj.__class__] = theclass = cls._create_class_proxy(obj.__class__)
        ins = object.__new__(theclass)
        theclass.__init__(ins, obj, *args, **kwargs)
        return ins

#
# ------ example ------
# >>> p = Proxy(6)
# >>> p
# 6
# >>> type(p)
# <class '__main__.Proxy(int)'>
# >>> p + 2
# 8
# >>> p2 = Proxy([1,2,3])
# >>> p2
# [1, 2, 3]
# >>> dir(p2)
# ['__add__', '__class__', '__contains__', '__delattr__', '__delitem__ #...
# '__getslice__', '__gt__', '__hash__', '__iadd__', '__imul__', '__ini #...
# educe__', '__reduce_ex__', '__repr__', '__reversed__', '__rmul__', ' #...
# 'index', 'insert', 'pop', 'remove', 'reverse', 'sort']
# >>> isinstance(p2, list)
# True
# >>> p2.append(8)
# >>> p2.append(2)
# >>> p2.append(5)
# >>> p2
# [1, 2, 3, 8, 2, 5]
# >>> p2.sort()
# >>> p2
# [1, 2, 2, 3, 5, 8]
# >>> p2[2]
# 2
# >>> p2[-1]
# 8
# >>> type(p2)
# <class '__main__.Proxy(list)'>
# >>> p2.__class__
# <type 'list'>
#
# ----- exceptions -----
# Proxying user-types should work perfectly well. But proxying builtin objects,
# like ints, floats, lists, etc., has some limitation and inconsistencies,
# imposed by the interpreter:
#
# >>> p = Proxy(6)
# >>> p + p
# Traceback (most recent call last):
#   File "<stdin>", line 1, in ?
# TypeError: unsupported operand type(s) for +: 'Proxy(int)' and 'Proxy(int)'
#
#
# >>> Proxy([1,2,3]) + [4,5]
# [1, 2, 3, 4, 5]
# >>> Proxy([1,2,3]) + Proxy([4,5])
# >>> p = Proxy([1,2,3])
# >>> p.extend(Proxy([4,5]))
# >>> p
# [1, 2, 3, 4, 5]
# >>> p + Proxy([6, 7])
# Traceback (most recent call last):
#   File "<stdin>", line 1, in ?
#   File "Proxy.py", line 49, in method
#     return getattr(object.__getattribute__(self, "_obj"), name)(*args, **kw)
# TypeError: can only concatenate list (not "Proxy(list)") to list
#
#
# Also note that the methods of a proxied type return "real objects", not
# proxies. So,
#
# >>> p = Proxy(3)
# >>> type(p)
# <class '__main__.Proxy(int)'>
# >>> p + 1
# 4
# >>> type(_)
# <type 'int'>
# >>> p += 1
# >>> p
# 4
# >>> type(p)
# <type 'int'>
#
# In this case, 'p' was reassigned a real integer, and the proxy was
# garbage-collected. What you might want to do is
#
# >>> p = Proxy(3)
# >>> p = Proxy(p + 1)
# >>> p
# 4
# >>> type(p)
# <class '__main__.Proxy(int)'>
