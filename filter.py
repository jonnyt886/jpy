# Provides classes useful for doing stdin -> stdout filtering

import sys, re, os
from os.path import join
#from builder import settings
from jpy import (colours, util)
from jpy.colours import expand_colours

class InputFilter:
	filter_colours = False

	def __init__(self):
		self.logfile = None

	def set_log_file(self, logfile):
		self.logfile = logfile

	def do_filter(self):
		log = None
		if self.logfile != None:
			log = open(self.logfile, 'w')

		for line in sys.stdin:
			line = util.strip_trailing_newline(line)

			if log != None:
				log.write(line + '\r\n')

			newline = self.filter_line(line)
			#print >>sys.stderr, '"' + line + '" -> "' + newline + '"'

			if newline != None:
				t = type(newline)
				if t is str:
					pass
				elif t is list:
					newline = '\n'.join(newline)
				else:
					raise TypeError('Unknown type: ' + str(t))

				if newline.strip():
					if self.filter_colours:
						newline = colours.remove_colours(newline)

					print(newline, file=sys.stdout)
					sys.stdout.flush()

		if log != None:
			log.close()

	def filter_line(line):
		return colours.GRAY + 'filter_line: ' + colours.NONE + line

# Filter that prefixes every line with a string (in gray)
class SimpleFilter(InputFilter):
	def __init__(self, prefix):
		InputFilter.__init__(self)
		self.prefix = prefix

	def filter_line(self, line):
		return colours.GRAY + self.prefix + ': ' + colours.NONE + line

# Filter that performs either simple string-based replacements or regex-based replacements
class ReplaceFilter(InputFilter):
	# Contains instances either of Regex or Replacement
	# if a normal replacement matches, then after it has been run the line will continue to be processed by other normal
	# replacements.
	replacements = []
	

	# Contains instances either of Regex or Replacement
	# if a line replacement matches, then after it has been run no more processing on that line will take place.
	line_replacements = []

	# Represents a regular expression and the function to call if it matches a line of input
	# The function will be called with the entire line and the specific regex match (it should be declared my_function(line, match) )
	class Regex:
		def __init__(self, regex_str, func_name):
			if (regex_str == None):
				self.regex = re.compile('^.*$')
			else:
				self.regex = re.compile(regex_str)

			if func_name == None:
				raise ValueError('Cannot specify None for func_name')

			self.__name__ = func_name

		def matches(self, line):
			self.line = line
			self.match = self.regex.match(line)
			if self.match == None:
				return False
			else:
				return True

		# Run the 'handling' function and get the returned string
		# (note that the returned value may either be a single string
		# or a list of strings that should be printed)
		def run(self):
			return self.__name__(self.line, self.match)
	
	# Represents a regular expression and a string that it should be replaced with
	class RegexReplacement:
		def __init__(self, regex_str, replacement):
			if (regex_str == None):
				self.regex = re.compile('^.*$')
			else:
				self.regex = re.compile(regex_str)

			if replacement == None:
				self.replacement = ''
			else:
				self.replacement = replacement

		def matches(self, line):
			self.line = line
			self.match = self.regex.match(line)
			if self.match == None:
				return False
			else:
				return True
		
	class Replacement:
		def __init__(self, string, replacement):
			self.string = string

			if replacement == None:
				self.replacement = ''
			else:
				self.replacement = replacement

	def __init__(self):
		InputFilter.__init__(self)

	# Given that 'item' is a type of replacement, run 'item' against 'line' as input.
	# Returns a tuple, (ran_something, newline) where run_something is a bool indicating
	# whether item was run (depending on whether it matched), and newline is the resulting
	# line, which will be the same as 'line' if 'ran_something' is False.
	def _attempt_replacement(self, item, line):
		t = item.__class__.__name__
		ran_something = False
		newline = line

		#print '     -- Running filters for "' + line + '"'

		if t == 'Regex':
			# do something
			if newline != None and item.matches(newline):
				newline = item.run()
				#print '     -- ' + t + ' ran, result: "' + str(newline) + '"'
				ran_something = True

		elif t == 'RegexReplacement':
			if newline != None and item.matches(newline):
				newline = re.sub(item.regex, item.replacement, newline)
				#print '     -- ' + t + ' ran, result: "' + str(newline) + '"'
				ran_something = True

		elif t == 'Replacement':
			if newline != None and item.string in newline:
				newline = newline.replace(item.string, item.replacement)
				#print '     -- ' + t + ' ran, result: "' + str(newline) + '"'
				ran_something = True
			
		else:
			raise TypeError('replacements contains an unknown type: ' + str(t))
		
		return (ran_something, newline)

	def filter_line(self, line):
		newline = line
		line_replacement_run = False

		# First run the 'line replacements' - if a line replacement matches, then
		# after it has been run no more processing on that line will take place.
		for item in self.line_replacements:
			if newline == None:
				newline = ''

			ran_something, newline = self._attempt_replacement(item, newline)

			if ran_something:
				line_replacement_run = True
				break
			
		# First run the 'normal replacements' - if a normal replacement matches, then
		# after it has been run the line will continue to be processed by other normal
		# replacements.
		if not line_replacement_run:
			for item in self.replacements:
				if newline == None:
					newline = ''

				ran_something, newline = self._attempt_replacement(item, newline)
			
		return newline

	# Add a 'regex' filter.
	#
	# This will cause the filter to call func_name with the line and a Match object 
	# for any lines matching regex_str.
	def add_regex(self, regex_str, func_name):
		self.replacements.append(ReplaceFilter.Regex(regex_str, func_name))

	# Add a 'regex replacement' filter.
	#
	# This will cause any matches of regex_str to be replaced with replacement.
	def add_regex_replacement(self, regex_str, replacement):
		self.replacements.append(ReplaceFilter.RegexReplacement(regex_str, replacement))

	# Add a 'replacement' filter.
	#
	# This will cause any occurences of 'string' to be replaced with 'replacement'.
	def add_replacement(self, string, replacement):
		self.replacements.append(ReplaceFilter.Replacement(string, replacement))
	
	# Add a 'regex' line filter.
	#
	# This will cause the filter to call func_name with the line and a Match object 
	# for any lines matching regex_str.
	#
	# If this regex matches, no other replacements for the line will be processed
	def add_line_regex(self, regex_str, func_name):
		self.line_replacements.append(ReplaceFilter.Regex(regex_str, func_name))

	# Add a 'regex replacement' line filter.
	#
	# This will cause any matches of regex_str to be replaced with replacement.
	#
	# If this regex matches, no other replacements for the line will be processed
	def add_line_regex_replacement(self, regex_str, replacement):
		self.line_replacements.append(ReplaceFilter.RegexReplacement(regex_str, replacement))

	# Add a 'replacement' line filter.
	#
	# This will cause any occurences of 'string' to be replaced with 'replacement'.
	#
	# If this regex matches, no other replacements for the line will be processed
	def add_line_replacement(self, string, replacement):
		self.line_replacements.append(ReplaceFilter.Replacement(string, replacement))

	# Function that prints nothing
	def print_nothing(self, line, match):
		# Do nothing (print nothing)
		pass


class SvnUpdateFilter(ReplaceFilter):
	def __init__(self):
		ReplaceFilter.__init__(self)

		self.add_line_regex(r"^Updating (.*)$", self.print_updating)
		self.add_line_regex(r"^At revision (.*)\.$", self.print_nothing)
		self.add_line_regex(r"^Skipped '\.'$", self.print_nothing)
		self.add_line_regex(r"^U    (.*)$", self.print_update)
		self.add_line_regex(r"^A    (.*)$", self.print_add)
		self.add_line_regex(r"^D    (.*)$", self.print_delete)
		self.add_line_regex(r"^Fetching external item into '(.*)'$", self.print_nothing)
		self.add_line_regex(r"^External at revision (.*)\.$", self.print_nothing)
		self.add_line_regex(r"^Updated to revision (.*)\.$", self.print_updated_to_revision)
		self.add_line_regex(r"^Updated external to revision (.*)\.$", self.print_updated_external_to_revision)
		self.add_line_regex(r"^.*Please login using your SciSys windows username and password\.$", self.auth_request)
		self.add_line_regex(r"^\s*$", self.print_nothing)
		self.add_line_regex(None, self.print_simple)

	def print_simple(self, line, match):
		return '(unmatched, ' + str(os.getpid()) + str(sys.argv) + ') "' + line + '"'
	
	def print_updated_external_to_revision(self, line, match):
		return 'External at r'+ colours.GREEN + match.groups()[0] + colours.NONE + '.'
	
	def print_updated_to_revision(self, line, match):
		return 'At r'+ colours.GREEN + match.groups()[0] + colours.NONE + '.'

	def print_updating(self, line, match):
		return 'Updating... '+ colours.GREEN + match.groups()[0] + colours.NONE

	def print_update(self, line, match):
		return 'U ' + colours.CYAN + match.groups()[0] + colours.NONE

	def print_add(self, line, match):
		return 'A ' + colours.PURPLE + match.groups()[0] + colours.NONE

	def print_delete(self, line, match):
		return 'D ' + colours.BROWN + match.groups()[0] + colours.NONE
	
	def auth_request(self, line, match):
		raise ValueError('Came across an auth failure... bombing out')

# Filters standard-format java logs (eg log4j)
class JavaLoggingFilter(ReplaceFilter):
	class LevelRegex:
		def __init__(self, level, clazz, line, messageregex, func_name):
			self.level = level
			self.clazz = clazz
			self.line = line
			
			if (messageregex == None):
				self.messageregex = re.compile('^.*$')
			else:
				self.messageregex = re.compile(messageregex)

			self.__name__ = func_name

		def matches(self, level, clazz, line, message):
			matched = True

			if self.level != None and self.level != level:
				matched = False

			if self.clazz != None and self.clazz != clazz:
				matched = False
			
			if self.line != None and self.line != line:
				matched = False

			match = self.messageregex.match(line)

			if match == None:
				matched = False

			if matched:
				self.match = match
				self.matchedLevel = level
				self.matchedClazz = clazz
				self.matchedLine = line
				self.matchedMessage = message

			return matched

		# Run the 'handling' function and get the returned string
		# (note that the returned value may either be a single string
		# or a list of strings that should be printed)
		def run(self):
			return self.__name__(self.matchedLevel, self.matchedClazz, self.matchedLine, self.matchedMessage, self.match)

	def __init__(self):
		ReplaceFilter.__init__(self)
		self.levelregexes = []

		self.add_regex(r"^(\d+\-\d+\-\d+\s+\d+:\d+:\d+,\d+)\s+(\w+)\s+(\w+):(\d+)\s\-\s(.*)$", self.print_log_entry)
	
	def add_level_regex(self, loglevel, clazz, line, messageregex, func_name):
		self.levelregexes.append(JavaLoggingFilter.LevelRegex(loglevel, clazz, line, messageregex, func_name))

	def print_log_entry(self, line, match):
		timestamp = match.groups()[0]
		loglevel = match.groups()[1]
		clazz = match.groups()[2] # Class name
		line = match.groups()[3]  # Line number (in clazz)
		message = match.groups()[4]

		#print loglevel, message, line
		return self.handle_line(timestamp, loglevel, clazz, line, message)
	
	def handle_line(self, timestamp, loglevel, clazz, line, message):
		for r in self.levelregexes:
			if r.matches(loglevel, clazz, line, message):
				return r.run()

		return self.handle_line_default(timestamp, loglevel, clazz, line, message)
		
	def handle_line_default(self, timestamp, loglevel, clazz, line, message):	
		if loglevel == 'INFO':
			return self.print_info(timestamp, clazz, line, message)
		elif loglevel == 'WARN':
			return self.print_warn(timestamp, clazz, line, message)
		elif loglevel == 'ERROR':
			return self.print_error(timestamp, clazz, line, message)
		elif loglevel == 'FATAL':
			return self.print_fatal(timestamp, clazz, line, message)
		else:
			return self.print_unknown(timestamp, clazz, line, message)

	# version of print_nothing for loglevel messages (i.e. takes more args that standard print_nothing)
	def print_lnothing(self, timestamp, loglevel, clazz, line, message):
		return None

	def print_info(self, timestamp, clazz, line, message):
		return 'I ' + colours.BROWN + clazz + ':' + line + ' ' + colours.GRAY + message + colours.NONE
	
	def print_warn(self, timestamp, clazz, line, message):
		return 'W ' + colours.BROWN + clazz + ':' + line + ' ' + colours.WHITE + message + colours.NONE
	
	def print_error(self, timestamp, clazz, line, message):
		return 'E ' + colours.BROWN + clazz + ':' + line + ' ' + colours.PURPLE + message + colours.NONE

	def print_fatal(self, timestamp, clazz, line, message):
		return 'F ' + colours.BROWN + clazz + ':' + line + ' ' + colours.RED + message + colours.NONE
	
	def print_unknown(self, timestamp, clazz, line, message):
		return 'u ' + clazz + ':' + line + ' ' + message + colours.NONE


# Filters
class HibernateSpringLoggingFilter(JavaLoggingFilter):
	def __init__(self):
		JavaLoggingFilter.__init__(self)
	
		# Filter out hibernate debug stuff	
		self.add_regex(r"^Hibernate: (.*)$", self.print_nothing)

		# Hibernate messages
		self.add_level_regex('INFO', 'XmlBeanDefinitionReader', '323', None, self.print_lnothing)
		self.add_level_regex('INFO', 'SettingsFactory', None, None, self.print_lnothing)
		self.add_level_regex('INFO', 'ASTQueryTranslatorFactory', '24', None, self.print_lnothing)
		self.add_level_regex('INFO', 'MappingFilePersistenceUnitPostProcessor', '121', None, self.print_lnothing)
		self.add_level_regex('INFO', 'MappingFilePersistenceUnitPostProcessor', '150', None, self.print_lnothing)
		self.add_level_regex('INFO', 'MappingFilePersistenceUnitPostProcessor', '208', None, self.print_lnothing)
		self.add_level_regex('INFO', 'Dialect', '152', None, self.print_lnothing)
		self.add_level_regex('INFO', 'MergablePersistenceUnitManager', '91', None, self.print_lnothing)
		self.add_level_regex('INFO', 'MergablePersistenceUnitManager', '104', None, self.print_lnothing)
		self.add_level_regex('INFO', 'Configuration', '559', None, self.print_lnothing)
		self.add_level_regex('INFO', 'AnnotationBinder', '418', None, self.print_lnothing)
		self.add_level_regex('INFO', 'AnnotationBinder', '969', None, self.print_lnothing)
		self.add_level_regex('INFO', 'EntityBinder', '424', None, self.print_lnothing)
		self.add_level_regex('INFO', 'QueryBinder', '64', None, self.print_lnothing)
		self.add_level_regex('INFO', 'CollectionBinder', '651', None, self.print_lnothing)

		#self.add_level_regex(None, None, None, None, self.print_lnothing)

		# Spring messages
		self.add_level_regex('INFO', 'DefaultListableBeanFactory', '467', None, self.print_lnothing)
		self.add_level_regex('INFO', 'DefaultListableBeanFactory', '414', None, self.print_lnothing)
		self.add_level_regex('INFO', 'DefaultListableBeanFactory', '421', None, self.print_lnothing)
		self.add_level_regex('INFO', 'GenericApplicationContext', '1196', None, self.print_lnothing)

class MavenFilter(ReplaceFilter):
	def __init__(self):
		ReplaceFilter.__init__(self)

		self.current_plugin = None
		self.project_count = 0
		self.current_project = 0
		self.current_test = None
		self.failed_tests = []

		self.add_line_regex("^\[INFO\] (>>>|<<<|---) ([\w\-\.\d:]+) \((.+)\) @ ([\w\-\.\d:]+) (>>>|<<<|---)$", self.update_current_plugin)
		self.add_line_regex_replacement("^\[INFO\] ([\w\.\-]+)$", None)
		self.add_line_replacement("[INFO] Scanning for projects...", None)
		self.add_line_replacement("[INFO] Reactor Build Order:", None)
		self.add_line_regex_replacement("^\[INFO\] (.+) already added, skipping$", None)
		self.add_line_regex_replacement("^\[INFO\] Using 'UTF\-8' encoding to copy filtered resources\.$", None)
		self.add_line_regex_replacement("^\[INFO\] Copying (\d+) resource(?:s)?$", None)
		self.add_line_regex_replacement("^Downloading: (.+)$", None)
		self.add_line_regex_replacement("^Downloaded: (.+) \(([\d\.]+ \w+) at ([\d\.]+ [\w\/]+)\)$", None)

		self.add_line_regex_replacement("^\[INFO\] Building ([\w\.\-]+) (.+)$", expand_colours("${GRAY}Building${GREEN} \\1${BROWN} \\2${NONE}"))
		self.add_line_regex_replacement("^\[INFO\] Building (jar|war): (.+)$", None)
		self.add_line_regex_replacement("^\[INFO\] Deleting (.+)$", None)
		
		self.add_line_regex_replacement("^\[INFO\] BUILD SUCCESS$", expand_colours("${GREEN}*** BUILD SUCCESS ***"))
		self.add_line_regex_replacement("^\[INFO\] BUILD FAILURE$", expand_colours("${RED} *** BUILD FAILURE ***"))

		self.add_line_replacement("[WARNING] *****************************************************************", None)
		self.add_line_replacement("[WARNING] * Your build is requesting parallel execution, but project      *", None)
		self.add_line_replacement("[WARNING] * contains the following plugin(s) that are not marked as       *", None)
		self.add_line_replacement("[WARNING] * @threadSafe to support parallel building.                     *", None)
		self.add_line_replacement("[WARNING] * While this /may/ work fine, please look for plugin updates    *", None)
		self.add_line_replacement("[WARNING] * and/or request plugins be made thread-safe.                   *", None)
		self.add_line_replacement("[WARNING] * If reporting an issue, report it against the plugin in        *", None)
		self.add_line_replacement("[WARNING] * question, not against maven-core                              *", None)
		self.add_line_replacement("[WARNING] *****************************************************************", None)
		self.add_line_regex_replacement("\[WARNING\] The following plugins are not marked @threadSafe in (.+):", None)
		self.add_line_regex_replacement("\[WARNING\] (.+)", None)
		self.add_line_replacement("[WARNING] *****************************************************************", None)

		self.add_line_regex_replacement("\[WARNING\] Cannot include project artifact: (.+); it doesn't have an associated file or directory.", None)
		self.add_line_regex_replacement("\[WARNING\] Assembly file: (.+) is not a regular file (it may be a directory). It cannot be attached to the project build for installation or deployment.", None)


		self.add_line_replacement("[INFO] No tests to run.", None)
		self.add_line_replacement("[INFO] Not compiling test sources", None)
		self.add_line_replacement("[INFO] Tests are skipped.", None)
		self.add_line_replacement("[INFO] No sources to compile.", None)
		self.add_line_regex_replacement("^\[INFO\] Compiling (\d+) source file(?:s)? to (.+).$", expand_colours("${GRAY}Compiling: ${GREEN}Compiling${BROWN} \\1${GREEN} source files"))
		self.add_line_regex_replacement("^\[INFO\] skip non existing resourceDirectory .*$", None)
		self.add_line_regex_replacement("^\[INFO\] Reading assembly descriptor: .*$", None)
		self.add_line_replacement("[INFO] Nothing to compile - all classes are up to date", None)
		self.add_line_replacement("[INFO] No sources to compile", None)
		
		self.add_line_regex("^\[INFO\] (.+) \.+ (SUCCESS|SKIPPED|FAILURE)( \[\d+\.\d+s\])?$", self.process_summary_line)

		self.add_line_regex_replacement("^\[INFO\] Installing (.+) to (.+)$", None)

		self.add_line_replacement("[INFO] Packaging war-overlay", None)
		self.add_line_regex_replacement("^\[INFO\] Processing overlay \[ id (.+)\]$", None)
		self.add_line_replacement("[INFO] Packaging classes", None)
		self.add_line_replacement("[INFO] Processing war project", None)
		self.add_line_replacement("[INFO] No sources in project. Archive not created.", None)
		self.add_line_regex_replacement("^\[INFO\] Copying webapp webResources \[(.+)\] to \[(.+)\]$", None)
		self.add_line_regex_replacement("^\[INFO\] Copying (\d+) resource$", None)
		self.add_line_regex_replacement("^\[INFO\] Copy ear sources (.+)$", None)
		self.add_line_regex_replacement("^\[INFO\] Could not find manifest file: (.+) \- Generating one$", None)
		self.add_line_replacement("[WARNING] Warning: selected war files include a WEB-INF/web.xml which will be ignored", None)
		self.add_line_regex_replacement("Building jar: (.+)", None)
		self.add_line_replacement("[WARNING] JAR will be empty - no content was marked for inclusion!", None)
		self.add_line_replacement("(webxml attribute is missing from war task, or ignoreWebxml attribute is specified as 'true')", None)
		self.add_line_replacement("[INFO] Generating application.xml", None)

		self.add_line_replacement("[INFO] Packaging webapp", None)
		self.add_line_regex_replacement("^\[INFO\] Assembling webapp \[(.+)\] in \[(.+)\]$", None)
		self.add_line_regex_replacement("^\[INFO\] Copying webapp resources \[(.+)\]$", None)
		self.add_line_regex_replacement("^\[INFO\] Copying artifact\[(.+)\] to\[(.+)\]$", None)
		self.add_line_regex_replacement("^\[INFO\] Copying files to (.+)$", None)
		self.add_line_regex_replacement("^\[INFO\] Webapp assembled in \[(.+)\]$", None)
		self.add_line_regex_replacement("^\[INFO\] Reading assembly descriptor: .*$", None)

		self.add_line_replacement("-------------------------------------------------------", None)
		self.add_line_replacement(" T E S T S", None)
		self.add_line_replacement("Results :", None)
		self.add_line_replacement("There are no tests to run.", None)
		self.add_line_regex_replacement("\[INFO\] Surefire report directory: (.+)$", None)

		self.add_line_regex_replacement("Running (?:.+\.)?(.*Test.*)", None)
		self.add_line_regex_replacement("Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+), Time elapsed: ([\d\.]+ sec)", None)
		self.add_line_regex_replacement("Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)", None)

		self.add_line_regex("^\[INFO\] \-{72}$", self.reset_status)
		self.add_line_regex("^mvnw: OSError: [.\s]* failed with exit code: (\d+)$", self.fast_quit)
		self.add_line_replacement("[INFO] Reactor Summary:", None)
		self.add_line_regex_replacement("^Destroying (\d+) processes$", None)
		self.add_line_replacement("Destroying process...", None)
		self.add_line_regex_replacement("^Destroyed (\d+) processes$", None)
		
		self.add_line_regex_replacement("^\[INFO\] Total time: (.+) \(Wall Clock\)$", None)
		self.add_line_regex_replacement("^\[INFO\] Finished at: ([\s.]+)$", None)
		self.add_line_regex_replacement("^\[INFO\] Final Memory: (\d+M)\/(\d+M)$", None)
		
		self.add_line_regex_replacement("^\[WARNING\] (.*)$", expand_colours("${BROWN}WARNING \\1"))
		self.add_line_regex_replacement("^\[ERROR\] (.*)$", expand_colours("${RED}ERROR \\1"))

		self.add_line_regex_replacement(r"^\[\w+\]\s*$", None)
		self.add_line_regex_replacement(r"^\s*$", None)
		self.add_line_regex(None, self.print_simple)

	def print_simple(self, line, match):
		return expand_colours('${GRAY}(unmatched) ${NONE}"' + line + '"')
	
	def fast_quit(self, line, match):
		raise ValueError("Build failed, quitting")
	
	def reset_status(self, line, match):
		self.last_status = None

	def store_test(self, line, match):
		self.current_test = match.groups()[0]

	def update_current_plugin(self, line, match):
		groups = match.groups()
		new_plugin = groups[1]

		#if new_plugin != self.current_plugin:
		#	result = colours.GREEN + 'Current plugin: ' + colours.YELLOW + new_plugin + colours.NONE
	
		self.current_plugin = new_plugin

	def process_summary_line(self, line, match):
		groups = match.groups()
		mod_name = groups[1]
		mod_status = groups[2]
		mod_time = None

		if len(groups) > 3:
			mod_time = groups[3]

		if mod_status == "FAILURE":
			return expand_colours("${RED}Failed module: ${YELLOW}" + mod_name)
