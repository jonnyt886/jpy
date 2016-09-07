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
