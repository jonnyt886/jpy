import weakref

# acts as a placeholder for 'None' in the cache
NONE_OBJECT = object()

def __convert__(obj):
    if obj == None: return NONE_OBJECT
    return obj

def __convert_back__(obj):
    if obj == NONE_OBJECT: return None
    return obj

# implements simple in-memory cache based on weakrefs
#
# stores things in memory in a dict using key/value pairs
# the keys can be anything you like that is a valid dict key
class WeakRefCache(object):
    # create the cache. loader_func should be a function that,
    # given a key, will load the corresponding object from the
    # underlying store.
    #
    # loader_func is called for any keys which are not in the cache
        # if permit_none is False, the cache will throw an exception
        #     if loader_func ever tries to load None into the cache
    def __init__(self, loader_func, permit_none=True):
        self.loader_func = loader_func
        self.permit_none = permit_none
        self.cache = {}

    def get(self, key):
        if key in list(self.cache.keys()):
            resolved_ref = self.cache[key]()
            # if resolved_ref == None, the weakref has gone
            # so we reload the object [later on]
            if resolved_ref is not None:
                return __convert_back__(resolved_ref)


        obj = self.loader_func(key)
        
        if obj == None: 
            if not self.permit_none:
                raise ValueError('loader tried to load None into the cache '+\
                        'but permit_none is False. key: '+str(key))

        self.cache[key] = weakref.ref(__convert__(obj))
        return obj

    def delete(self, key):
        if key in self.cache: del self.cache[key]
