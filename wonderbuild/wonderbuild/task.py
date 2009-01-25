#! /usr/bin/env python
# This source is free software ; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation ; either version 2, or (at your option) any later version.
# copyright 2008-2009 members of the psycle project http://psycle.sourceforge.net ; johan boule <bohan@jabber.org>

import sys, os, subprocess

from logger import out, is_debug, debug, colored

class Task(object):
	def __init__(self, project, aliases = None):
		self.project = project
		project.add_task(self, aliases)
		self.in_task_todo_count = 0
		self.out_tasks = []
		self.processed = False

	def __call__(self, sched_context):
		yield []
		raise StopIteration

	def print_desc(self, desc, color = '7;1'):
		out.write(colored(color, 'wonderbuild: task: ' + desc) + '\n')
		out.flush()

def exec_subprocess(args, env = None, cwd = None):
	if __debug__ and is_debug: debug('exec: ' + str(cwd) + ' ' + str(env) + ' ' + str(args))
	return subprocess.call(
		args = args,
		bufsize = -1,
		env = env,
		cwd = cwd
	)

def exec_subprocess_pipe(args, input = None, env = None, cwd = None, silent = False):
	if __debug__ and is_debug: debug('exec: pipe: ' + str(cwd) + ' ' + str(env) + ' ' + str(args))
	if input is not None: # workaround for bug still present in python 2.5.2
		_lock.acquire()
		try: p = subprocess.Popen(
				args = args,
				bufsize = -1,
				stdin = subprocess.PIPE,
				stdout = subprocess.PIPE,
				stderr = subprocess.PIPE,
				env = env,
				cwd = cwd
			)
		finally: _lock.release()
	else: p = subprocess.Popen(
			args = args,
			bufsize = -1,
			stdin = None,
			stdout = subprocess.PIPE,
			stderr = subprocess.PIPE,
			env = env,
			cwd = cwd
		)
	if input is not None:
		if __debug__ and is_debug:
			for line in input.split('\n')[:-1]: debug('exec: pipe: ' + colored('7;36', 'in') + ': ' + line)
		elif not silent:
			sys.stdout.write('\n')
			sys.stdout.write(input)
	out, err = p.communicate(input)
	if __debug__ and is_debug:
		if len(out):
			for line in out.split('\n')[:-1]: debug('exec: pipe: ' + colored('7;32', 'out') + ': ' + line)
		if len(err):
			s = ''
			for line in err.split('\n')[:-1]: debug('exec: pipe: ' + colored('7;1;31', 'err') + ': ' + line)
			debug(s)
		if p.returncode == 0: debug('exec: pipe: ' + colored('7;32', 'ret') + ': ' + str(p.returncode) + ' ok')
		else: debug('exec: pipe: ' + colored('7;1;31', 'ret') + ': ' + str(p.returncode) + ' failed')
	elif not silent:
		if len(out): sys.stdout.write(out)
		if len(err):
			s = ''
			for line in err.split('\n')[:-1]: s += colored('7;1;31', 'error:') + ' ' + line + '\n'
			sys.stderr.write(s)
		if p.returncode == 0: sys.stdout.write('exec: pipe: ' + colored('7;32', 'ret') + ': ' + str(p.returncode) + ' ok\n')
		else: sys.stderr.write('exec: pipe: ' + colored('7;1;31', 'ret') + ': ' + str(p.returncode) + ' failed\n')
	return p.returncode, out, err
# workaround for bug still present in python 2.5.2
import threading
_lock = threading.Lock() # used in exec_subprocess_pipe
