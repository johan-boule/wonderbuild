#! /usr/bin/env python
# This source is free software ; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation ; either version 2, or (at your option) any later version.
# copyright 2007-2009 members of the psycle project http://psycle.sourceforge.net ; johan boule <bohan@jabber.org>

from wonderbuild.logger import out, colored, is_debug, debug, silent
from wonderbuild.subprocess_wrapper import exec_subprocess, exec_subprocess_pipe
from wonderbuild.check_task import CheckTask
from wonderbuild.std_checks import BinaryFormatPeCheckTask, PicFlagDefinesPicCheckTask

class DetectImplCheckTask(CheckTask):
	@staticmethod
	def shared(user_build_cfg):
		try: return user_build_cfg.project.cxx_detect_impl
		except AttributeError:
			instance = user_build_cfg.project.cxx_detect_impl = DetectImplCheckTask(user_build_cfg)
			return instance
			
	def __init__(self, user_build_cfg):
		CheckTask.__init__(self, user_build_cfg.project)
		self.user_build_cfg = user_build_cfg

	@property
	def sig(self): return self.user_build_cfg.options_sig

	@property
	def uid(self): return str(self.__class__)

	@property
	def desc(self): return 'c++-compiler'
	
	@property
	def result_display(self):
		if not self.result: return 'not found', '31'
		else: return str(self.kind) + ' version ' + '.'.join(str(v) for v in self.version), '32'

	@property
	def result(self): return self.kind is not None
	
	@property
	def kind(self): return self.results[0]
	
	@property
	def version(self): return self.results[1]
	
	def __call__(self, sched_context):
		CheckTask.__call__(self, sched_context)
		cfg = self.user_build_cfg
		cfg.kind = self.kind
		cfg.version = self.version
		self.setup_build_cfg()
	
	def do_check_and_set_result(self, sched_context):
		sched_context.lock.release()
		try:
			cfg = self.user_build_cfg
			o = cfg.options
			
			# determine the kind of compiler
			if cfg.cxx_prog is not None: # check the compiler specified in cfg.cxx_prog
				if not silent:
					desc = 'checking for ' + self.desc + ' ... ' + cfg.cxx_prog
					self.print_check(desc)
				try: r, out, err = exec_subprocess_pipe([cfg.cxx_prog, '-dumpversion'], silent=True)
				except Exception, e:
					if __debug__ and is_debug: debug('cfg: ' + desc + ': ' + str(e))
					r = 1
				if r == 0: cfg.kind = 'gcc'
				else:
					try: r, out, err = exec_subprocess_pipe([cfg.cxx_prog, '/?'], input = '', silent=True)
					except Exception, e:
						if __debug__ and is_debug: debug('cfg: ' + desc + ': ' + str(e))
						r = 1
					if r == 0: cfg.kind = 'msvc'
					else: cfg.kind = None
			else: # try some compilers program names until we found one available
				if not silent:
					desc = 'checking for ' + self.desc + ' ...'
					self.print_check(desc + ' g++')
				try: r, out, err = exec_subprocess_pipe(['g++', '-dumpversion'], silent=True)
				except Exception, e:
					if __debug__ and is_debug: debug('cfg: ' + desc + ': ' + str(e))
					r = 1
				if r == 0:
					cfg.kind = 'gcc'
					cfg.cxx_prog = 'g++' ###
				else:
					if not silent: self.print_check(desc + ' msvc')
					try: r, out, err = exec_subprocess_pipe(['cl'], silent=True)
					except Exception, e:
						if __debug__ and is_debug: debug('cfg: ' + desc + ': ' + str(e))
						r = 1
					if r == 0:
						cfg.kind = 'msvc'
						cfg.cxx_prog = 'cl' ###
					elif False: # pure posix support not tested
						if not silent: self.print_check(desc + ' c++')
						try: r, out, err = exec_subprocess_pipe(['c++'], silent=True)
						except Exception, e:
							if __debug__ and is_debug: debug('cfg: ' + desc + ': ' + str(e))
							r = 1
						if r == 0:
							cfg.kind = 'posix'
							cfg.cxx_prog = 'c++' ###
					else: cfg.kind = None
			# set the impl corresponding to the kind
			self.select_impl()
			# read the version
			if cfg.impl is not None: cfg.version = cfg.impl.parse_version(out, err)
		finally: sched_context.lock.acquire()
		self.results = cfg.kind, cfg.version

	def select_impl(self):
		cfg = self.user_build_cfg
		# set the impl corresponding to the kind
		if cfg.kind == 'gcc':
			from gcc_impl import Impl
			cfg.impl = Impl()
		elif kind == 'msvc':
			from msvc_impl import Impl
			cfg.impl = Impl(self.project.persistent)
		elif cfg.kind == 'posix':
			from posix_impl import Impl
			cfg.impl = Impl(self.project.persistent)
		else: cfg.impl = cfg.version = None

	def setup_build_cfg(self):
		cfg = self.user_build_cfg
		if cfg.impl is None: self.select_impl()
		if cfg.impl is not None:
			o = cfg.options
			# set the programs
			cxx_prog, ld_prog, ar_prog, ranlib_prog = cfg.impl.progs(cfg)
			if 'cxx' not in o: cfg.cxx_prog = cxx_prog
			if 'ld' not in o: cfg.ld_prog = ld_prog
			if 'ar' not in o: cfg.ar_prog = ar_prog
			if 'ranlib' not in o: cfg.ranlib_prog = ranlib_prog
			
			pe = BinaryFormatPeCheckTask.shared(cfg)
			pic = PicFlagDefinesPicCheckTask.shared(cfg)

			cfg.pic_flag_defines_pic = True # allows it to be reentrant during the check itself

			self.project.sched_context.parallel_wait(pe, pic)
			cfg.target_platform_binary_format_is_pe = pe.result
			cfg.pic_flag_defines_pic = pic.result
