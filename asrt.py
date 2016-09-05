# Methods to perform assertions.
#
# We support three warn levels used when an assertion fails
# 0 (or False)	= throw an exception
# 1 (or True) 	= emit a message on stderr
# 2				= do nothing
#
# We default to False.
#

import sys

def _failed(message, warn):
	if warn == 2:
		pass
	elif warn == 1:
		print(message, file=sys.stderr)
	else:
		raise ValueError(message)

def fail(message):
    _failed(message, 0)

# Asserts that e1 == e2. (or rather, that not e1 != e2, so __ne__ may need implementing)
# If warn is true, an error message is printed to stderr when the assertion
# fails; otherwise an exception is thrown.
def asrt_eq(e1, e2, message = "Assertion failed", warn = False):
	if e1 != e2:
		msg = message + " (e1 = '" + str(e1) + "' (" +\
			str(type(e1)) + "), e2 = '" + str(e2) + "' (" + str(type(e2)) + ") )"

		_failed(msg, warn) # __ne__ may need implementing
		return False

	return True

# Asserts that e1 != e2. (nb __ne__ may need implementing)
# If warn is true, an error message is printed to stderr when the assertion
# fails; otherwise an exception is thrown.
def asrt_ne(e1, e2, message = "Assertion failed", warn = False):
	if not e1 != e2:
		msg = message + " (e1 = '" + str(e1) + "' (" +\
			str(type(e1)) + "), e2 = '" + str(e2) + "' (" + str(type(e2)) + ") )"

		_failed(msg, warn) # __ne__ may need implementing
		return False

	return True

# asrt_eq with floats-fudge
# gives false positives if two floats are equal to about 10 significant figures
# as it uses type comparison and str() comparison to perform matching for floats
# If warn is true, an error message is printed to stderr when the assertion
# fails; otherwise an exception is thrown.
def asrt_eq_ff(e1, e2, message = "Assertion failed", warn = False):
	if e1 != e2:
		# I've seen floats that look the same but are in fact different.
		# If the types are the same and the string representations match,
		# that is good enough for us. Note that this may give false positives
		# when dealing with floats that are different only after a huge 
		# number of significant figures.
		if type(e1) is type(e2) and type(e1) is float and \
				str(e1) == str(e2):
					return True

		else:
			msg = message + "(e1 = '" + str(e1) + "' (" +\
					str(type(e1)) + "), e2 = '" + str(e2) + "' (" + str(type(e2)) + ") )"
			_failed(msg, warn)
			return False

	return True

# Asserts that e1 is e2. (i.e. identity-equals)
# If warn is true, an error message is printed to stderr when the assertion
# fails; otherwise an exception is thrown.
def asrt_same(e1, e2, message = "Assertion failed", warn = False):
	if e1 is not e2:
		msg = message + " (e1 = '" + str(e1) + "' (" +\
			str(type(e1)) + "), e2 = '" + str(e2) + "' (" + str(type(e2)) + ") )"

		_failed(msg, warn)
		return False

	return True

# Basic assert method
# If warn is true, an error message is printed to stderr when the assertion
# fails; otherwise an exception is thrown.
def asrt(expression, message = "Assertion failed", warn = False):
	if not expression:
		_failed(message, warn)
		return False

	return True

# Assert not-None
# If warn is true, an error message is printed to stderr when the assertion
# fails; otherwise an exception is thrown.
def asrt_nn(expression, message = "Assertion failed", warn = False):
	if expression == None:
		_failed(message, warn)
		return False

	return True
