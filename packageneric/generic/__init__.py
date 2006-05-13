#! /usr/bin/env python

# This source is free software ; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation ; either version 2, or (at your option) any later version.
# copyright 2006 johan boule <bohan@jabber.org>
# copyright 2006 psycledelics http://psycle.pastnotecut.org

import os, fnmatch
#from SCons.Script.SConscript import SConsEnvironment
#from SCons.Script import *

def _PkgConfig(context, packageneric, name, what):
	command = 'pkg-config --%s \'%s\'' % (what, name)
	context.Message('checking for ' + command + ' ... ')
	result = context.TryAction(command)
	#print result
	result = result[0]
	context.Result(result)
	return result

class Packageneric:
	
	def	 environment(self):
		return self._environment
	
	def configure(self):
		return self._configure
	
	def finish_configure(self):
		self._environment = self.configure().Finish()

	def options(self):
		return self._options
	
	def __init__(self, environment_ctor, configure_ctor, options_ctor, *etc):
		self._environment_ctor = environment_ctor
		self._configure_ctor = configure_ctor
		self._options_ctor = options_ctor
		
		self._environment = self._environment_ctor()
		self._environment.BuildDir(os.path.join('++packageneric', 'build', 'scons'), 'src', duplicate=0)
		self._configure = self._configure_ctor(
			self.environment(),
			{
				'PkgConfig' : lambda context, packageneric, name, what: _PkgConfig(context, packageneric, name, what)
			}
		)
		self._options = self._options_ctor('packageneric.configuration')
	
	class Person:
		def __init__(self, name, email = None):
			self.name = name
			self.email = email

	class InstallPrefix:
		def __init__(self, packageneric):
			# Get our configuration options:
			packageneric.options().Add(PathOption('PREFIX', 'Directory to install under', '/usr/local'))
			packageneric.options().Update(packageneric.environment())
			# Save, so user doesn't have to specify PREFIX every time
			packageneric.options().Save('packageneric.configuration', packageneric.environment())
			Help(packageneric.options().GenerateHelpText(packageneric.environment()))
			# Here are our installation paths:
			self.prefix  = '$PREFIX'
			self.lib     = '$PREFIX/lib'
			self.bin     = '$PREFIX/bin'
			self.include = '$PREFIX/include'
			self.data    = '$PREFIX/share'
			packageneric.environment().Export('env self.prefix self.lib self.bin self.include self.data')
	
	class EnvList:
		def __init__(self, env, all = False):
			if all:
				dictionary = env.Dictionary()
				keys = dictionary.keys()
				keys.sort()
				for key in keys:
					print '%s = %s' % (key, dictionary[key])
			else:
				def show(key):
					try:
						env[key]
						if len(env[key]):
							print key, '->', env[key], '->', env.subst('$' + key)
						else:
							print key, '<- empty'
					except:
						pass
				show('CPPPATH')
				show('CXXFLAGS')
				show('LIBPATH')
				show('LIBS')
				show('LINKFLAGS')
		
	class Find:
		'''a forward iterator that traverses a directory tree'''
		
		def __init__(self, strip_path, path, pattern = '*'):
			self.strip_path = strip_path
			self.stack = [path]
			self.pattern = pattern
			self.files = []
			self.index = 0
			
		def __getitem__(self, index):
			while 1:
				try:
					file = self.files[self.index]
					self.index = self.index + 1
				except IndexError:
					# pop next directory from stack
					self.directory = self.stack.pop()
					self.files = os.listdir(os.path.join(self.strip_path, self.directory))
					self.index = 0
				else:
					# got a filename
					path = os.path.join(self.directory, file)
					if os.path.isdir(os.path.join(self.strip_path, path)):
						self.stack.append(path)
					if fnmatch.fnmatchcase(file, self.pattern):
						return path
	
	def print_all_nodes(dirnode, level = 0):
		'''Print all the scons nodes that are children of this node, recursively.'''
		if type(dirnode)==type(''):
			dirnode=Dir(dirnode)
		dt = type(Dir('.'))
		for f in dirnode.all_children():
			if type(f) == dt:
				print "%s%s: .............." % (level * ' ', str(f))
				print_dir(f, level+2)
			print "%s%s" % (level * ' ', str(f))

	def Glob(includes = ['*'], excludes = None, dir = '.'):
		'''Similar to glob.glob, except globs SCons nodes, and thus sees generated files and files from build directories.
		Basically, it sees anything SCons knows about.
		A key subtlety is that since this function operates on generated nodes as well as source nodes on the filesystem,
		it needs to be called after builders that generate files you want to include.
		
		It will return both Dir entries and File entries
		'''
		
		def fn_filter(node):
			fn = os.path.basename(str(node))
			match = False
			for include in includes:
				if fnmatch.fnmatchcase(fn, include):
					match = True
					break
			if match and not excludes is None:
				for exclude in excludes:
					if fnmatch.fnmatchcase(fn, exclude):
						match = False
						break
			return match

		def filter_nodes(where):
			children = filter(fn_filter, where.all_children(scan = False))
			nodes = []
			for f in children:
				nodes.append(gen_node(f))
			return nodes

		def gen_node(n):
			'''Checks first to see if the node is a file or a dir, then creates the appropriate node.
			(code seems redundant, if the node is a node, then shouldn't it just be left as is?)
			'''
			if type(n) in (type(''), type(u'')):
				path = n
			else:
				path = n.abspath
			if os.path.isdir(path):
				return Dir(n)
			else:
				return File(n)
		
		here = Dir(dir)
		nodes = filter_nodes(here)
		node_srcs = [n.srcnode() for n in nodes]
		src = here.srcnode()
		if src is not here:
			for s in filter_nodes(src):
				if s not in node_srcs:
					# Probably need to check if this node is a directory
					nodes.append(gen_node(os.path.join(dir, os.path.basename(str(s)))))
		return nodes

	class SourcePackage:
		def __init__(self, name = None, version = None, description = '', long_description = '', path = '.'):
			self.name = name
			if version is None:
				self.version = []
			else:
				self.version = version
			self.description= description
			self.long_description = long_description
			self.path = path
		
	class File:
		def __init__(self):
			self.strip_path = None
			self.path = None
			self.install_path = None
		
	class SourceFile:
		def __init__(self, path):
			self.path = path
			self.defines = []
			self.include_path = []
		
	class ObjectFile:
		def __init__(self, source):
			self.source = source
			self.defines = source.defines
			self.include_path = source.include_path
			self.compiler_flags = None
		
	class CompilerFlags:
		class Define:
			def __init(name, value = ''):
				self.name = name
				self.value = value
		def __init__(self):
			self.defines = []
			self.include_path = []
			self.optimizations = []
			self.debugging_info = []
		
	class LinkerFlags:
		def __init_(self):
			self.library_path = []
			self.libraries = []
			self.optimizations = []
		
	def pkg_config(self, name, what):
		return self.configure().PkgConfig(self, name, what)
	
	class ExternalPackage:
		def __init__(
			self,
			packageneric,
			debian,
			debian_version_compare,
			pkg_config = None,
			pkg_config_version_compare = None
		):
			self.packageneric = packageneric
			self.pkg_config = pkg_config
			self.pkg_config_version_compare = pkg_config_version_compare
			self.debian = debian
			self.debian_version_compare = debian_version_compare
			self.parsed = False
			
		def get_env(self):
			if not self.parsed:
				self.parsed = True
				env = self.packageneric.environment().Copy()
				if not self.pkg_config is None:
					self.packageneric.pkg_config(self.pkg_config, 'exists')
					string = self.pkg_config
					if not self.pkg_config_version_compare is None:
						string += ' ' + self.pkg_config_version_compare
					self.packageneric.pkg_config(string, 'exists')
					includes = self.packageneric.pkg_config(string, 'cflags-only-I')
					cflags = self.packageneric.pkg_config(string, 'cflags-only-other')
					libpath = self.packageneric.pkg_config(string, 'libs-only-L')
					libs = self.packageneric.pkg_config(string, 'libs-only-other')
			return env

		def __str__(self):
			string = ''
			if not self.pkg_config is None:
				string += self.pkg_config
				if not self.pkg_config_version_compare is None:
					string += ' ' + self.pkg_config_version_compare
				elif not self.debian_version_compare is None:
					string += ' ' + self.debian_version_compare
			else:
				string += self.debian
				if not self.debian_version_compare is None:
					string += ' ' + self.debian_version_compare
			return string
		
		def show(self):
			strings = ['======== module package external: ']
			strings.append(str(self))
			strings.append(' ========')
			string = ''
			for x in strings:
				string += x
			print string
			Packageneric.EnvList(self.get_env())
		
	class Module:
		class Types:
			files = 'files'
			shared_lib = 'shared_lib'
			static_lib = 'static_lib'
			bin = 'bin'
			python = 'python'
			
		def __init__(self, packageneric, name = None, version = None, description = '', public_requires = None):
			self.packageneric = packageneric
			self.name = name
			if version is None:
				self.version = []
			else:
				self.version = version
			self.description = description
			if public_requires is None:
				self.public_requires = []
			else:
				self.public_requires = public_requires
			self.parsed = False
			self.sources = []
			self.headers = []
			
		def get_name(self):
			return self.name
		
		def get_version(self):
			return self.version
		
		def get_sources(self):
			return self.sources
		def add_source(self, source):
			self.sources.append(source)
		def add_sources(self, sources):
			for x in sources: self.add_source(x)
			
		def get_headers(self):
			return self.headers
		def add_header(self, header):
			self.headers.append(header)
		def add_headers(self, headers):
			for x in headers: self.add_header(x)
			
		def get_public_requires(self):
			return self.public_requires
		def add_public_requires(self, requires):
			self.public_requires.append(requires)
			
		def get_env(self):
			if not self.parsed:
				self.parsed = True
				public_requires = ''
				for x in self.public_requires:
					public_requires += ' ' + str(x)
				debian = ''
				debian_version_compare = ''
				env = self.packageneric.environment().Copy()
			return env
		
		def show(self):
			print '======== module internal:', self.name, self.version, '========'
			public_requires = []
			for x in self.public_requires:
				public_requires.append(str(x))
			print 'requires', public_requires
			Packageneric.EnvList(self.get_env())
			
		def scons(self):
			return self.get_env().SharedLibrary(self.name, self.sources)

	class PkgConfigPackage:
		def __init__(self, name = None, version = None, description = '', modules = None):
			self.name = name
			if version is None:
				self.version = []
			else:
				self.version = version
			self.description = description
			if modules is None:
				self.modules = []
			else:
				self.modules = modules

	class DebianPackage:
		def __init__(
			self,
			source_package = None,
			name = None,
			section = None,
			architecture = 'any',
			description = '',
			long_description = ''
		):
			self.source_package = source_package
			self.name = name
			if section is None:
				self.section = self.source_package.section
			else:
				self.section = section
			self.architecture = architecture
			self.provides = []
			self.depends = []
			self.recommends = []
			self.suggests = []
			self.description = description
			self.long_description = long_description
			self.files = []

		def	get_build_depends(self):
			class Depend: pass
			result = []
			for x in self.depends:
				depend = Depend()
				depend.name = x.debian
				if not x.debian_version_compare is None:
					depend.version_compare = x.debian_version_compare
				result.append(depend)
			return result
		
	class Debian:
		def __init__(
			self,
			source_package = None,
			section = 'libs',
			priority = 'optional',
			maintainer = '',
			uploaders = None,
			description = None,
			long_description = None,
			binary_packages = None,
			build_depends = None
		):
			self.source_package = source_package
			self.section = section
			self.priority = priority
			self.maintainer = maintainer
			if uploaders is None:
				self.uploaders = []
			else:
				self.uploaders = uploaders
			if description is None and not source_package is None:
				self.description = source_package.description
			else:
				self.description = description
			if long_description is None and not source_package is None:
				self.long_description = source_package.long_description
			else:
				self.description = description
			if binary_packages is None:
				self.binary_packages = []
			else:
				self.binary_packages = binary_packages
			if build_depends is None:
				self.build_depends = []
			else:
				self.build_depends = build_depends

		def	get_build_depends(self):
			result = self.build_depends
			for x in self.binary_packages:
				for xx in x.get_build_depends():
					if not xx in self.build_depends:
						result.append(xx)
			return result
		
		def control(self):
			string = ''
			string += 'Source: ' + self.source_package.name + '\n'
			string += 'Section: ' + self.section + '\n'
			string += 'Priority: ' + self.priority + '\n'
			string += 'Build-Depends: scons'
			for x in self.get_build_depends():
				string += x.name + ' (' + x.version_compare + '), '
			string += '\n'
			if not self.maintainer is None:
				string += 'Maintainer: ' + self.maintainer.name + ' <' + self.maintainer.email + '>\n'
			if len(self.uploaders):
				string += 'Uploaders: '
				for x in self.uploaders:
					string += x.name + ' <' + x.email + '>, '
				string += '\n'
			string += 'Standards-Version: 3.6.2\n'
			for x in self.binary_packages:
				string += '\n'
				string += 'Package: ' + x.name + '\n'
				if len(x.provides):
					string += 'Provides: '
					for xx in x.provides:
						string += xx + ', '
					string += '\n'
				if len(x.recommends):
					string += 'Recommends: '
					for xx in x.recommends:
						string += xx.name + ' (' + xx.version_compare, '), '
					string += '\n'
				if len(x.suggests):
					string += 'Suggests: '
					for xx in x.suggests:
						string += xx.name + ' (' + xx.version_compare + '), '
					string += '\n'
				string += 'Depends: ${shlibs:Depends}, ${misc:Depends}'
				for xx in x.depends:
					if isinstance(x, Packageneric.ExternalPackage):
						string += xx.name + ' (' + xx.version_compare + '), '
				string += '\n'
				string += 'Section: '
				if x.section is None:
					string += self.section
				else:
					string += x.section
				string += '\n'
				string += 'Architecture: ' + x.architecture + '\n'
				string += 'Description: ' + x.description + '\n '
				description = self.long_description + '\n\n' + x.long_description
				was_new_line = False
				for xx in description:
					if xx == '\n':
						if was_new_line:
							string += '.'
						was_new_line = True
						string += '\n '
					else:
						was_new_line = False
						string += xx
				string += '\n'
			return string
			
	class DistributionArchive:
		def __init__(self):
			self.remote_path = None
			self.source_packages = []
			self.binary_packages = []
