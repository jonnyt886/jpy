# command.py - contains methods for running commands

from datetime import timedelta, datetime
import os, sys
from optparse import (OptionParser, OptionGroup)
import shlex, subprocess

# Contains the result of a command run using run_command().
class CommandResult:
    """
    init parameters:
        process: process object
        stdout: string representing stdout
        stderr: string representing stderr
        start_time: start time (as a datetime)
        finish_time: start time (as a datetime)
        exit_code: process exit code

    this object will also calculate:
        running_time (as a timedelta)
        success
    """
    def __init__(self, process, stdout, stderr, start_time, finish_time, exit_code):
        self.process = process
        self.stdout = stdout
        self.stderr = stderr
        self.start_time = start_time
        self.finish_time = finish_time
        self.running_time = start_time - finish_time
        self.exit_code = exit_code
        self.success = exit_code == 0

def execute(command_line, directory = None, \
        print_timing_info = False, shell='/bin/bash', \
        grab_output = True, ignore_exit_code = False, \
        input_string = None):
    """Run an operating system command. This is an updated
    version of run_command() which returns a CommandResult
    object instead of a tuple.
    
    command_line: the command line to run. As the command
        is run inside a shell, this can be a shell command
    directory: if not None, change the working directory 
        to the one specified when making the call
    grab_output: if True, wait until the command is finished
        and return output as a tuple (stdout, stderr). If 
        False, the process can interact with the terminal 
        and no stdout/stderr is collected. If you want to 
        pass input to the process, this must be True.
    ignore_exist_code: if False, an exception is thrown if 
        the process exits with a non-zero exit code. If this 
        is true then the exit code is returned regardless of 
        value
    input_string: a String representing input to pass into 
        the process - grab_output must be True for this to work
    """
    # For stuff we run through the shell shlex splitting doesn't work,
    # so we just pass command_line straight through to bash.
    #args = shlex.split(command_line)

    stdout = None
    stderr = None
    p = None
    
    before = datetime.now()

    if grab_output:
            stdout, stderr, p = _run_grab_output(command_line,
                    shell, directory, input_string)
    else:
            p = _run_no_output(command_line, shell, directory)
    
    after = datetime.now()

    if not ignore_exit_code and p.returncode != 0:
            raise OSError('Command "' + str(command_line) + \
                    '" failed with exit code: ' + str(p.returncode))

    # don't split on \n, leave it as a string
#    if grab_output:
#            stdout = stdout.split('\n')
#            stderr = stderr.split('\n')

    return CommandResult(
            process=p,
            stdout=stdout,
            stderr=stderr,
            start_time=before,
            finish_time=after,
            exit_code = p.returncode)

def _run_grab_output(command_line, shell, directory, input_string = None):
        #print '_run_grab_output', command_line, shell, directory
	if input_string == None:
		stdin = None
	else:
		stdin=subprocess.PIPE

	do_shell = (shell != None)
	if do_shell: executable = shell
	else: executable = None

	p = subprocess.Popen(command_line, executable=executable, shell=do_shell, \
            env=os.environ, cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=stdin)
	stdout, stderr = p.communicate(input_string)
	p.wait()

	return stdout, stderr, p
	
def _run_no_output(command_line, shell, directory):
	#print(('_run_no_output[command_line=', command_line, 'shell=', shell, 'dir=', directory))
	do_shell = (shell != None)
	if do_shell: executable = shell
	else: executable = None

	p = subprocess.Popen(command_line, executable=executable, shell=do_shell, \
            env=os.environ, cwd=directory)
	p.wait()

	return p
