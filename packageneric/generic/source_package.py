# This source is free software ; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation ; either version 2, or (at your option) any later version.
# copyright 2006 johan boule <bohan@jabber.org>
# copyright 2006 psycledelics http://psycle.pastnotecut.org

class source_package:
	def __init__(
		self,
		packageneric,
		name = None,
		version = None,
		description = '',
		long_description = '',
		path = ''
	):
		self._packageneric = packageneric
		self._name = name
		self._version = version
		self._description= description
		self._long_description = long_description
		self._path = path
		
		
		self._node = None
		
		import os.path
		self._header = os.path.join('packageneric', 'source-package', self.name() + '.private.hpp')
		self.packageneric().environment().SubstInFile(
			os.path.join(self.packageneric().build_directory(), self._header),
			'packageneric/generic/detail/src/packageneric/package/meta-information.private.hpp.in',
			SUBST_DICT = {
				'#undef PACKAGENERIC__PACKAGE__NAME': '#define PACKAGENERIC__PACKAGE__NAME "' + self.name() + '"',
				'#undef PACKAGENERIC__PACKAGE__VERSION': '#define PACKAGENERIC__PACKAGE__VERSION "' + str(self.version()) + '"',
				'#undef PACKAGENERIC__PACKAGE__VERSION__MAJOR': '#define PACKAGENERIC__PACKAGE__VERSION__MAJOR ' + str(self.version().major()),
				'#undef PACKAGENERIC__PACKAGE__VERSION__MINOR': '#define PACKAGENERIC__PACKAGE__VERSION__MINOR ' + str(self.version().minor()),
				'#undef PACKAGENERIC__PACKAGE__VERSION__PATCH': '#define PACKAGENERIC__PACKAGE__VERSION__PATCH ' + str(self.version().patch())
			}
		)
		self.packageneric().environment().Append(
			CPPDEFINES = {
				'PACKAGENERIC': '\\<' + self._header + '\\>'
			}
		)
		self.packageneric().environment().AppendUnique(
			CPPPATH = [self.packageneric().build_directory()]
		)
	
	def packageneric(self):
		return self._packageneric
	
	def node(self, env):
		if not self._node:
			import SCons.Node.Python
			self._node = SCons.Node.Python.Value(
				(
					self.name(),
					self.version()
				)
			)
			import os.path
			if False:
				env.Depends(os.path.join(self.packageneric().build_directory(), self._header), self._node)
				return self._node
			else:
				return os.path.join(self.packageneric().build_directory(), self._header)
			
	def name(self):
		return self._name
		
	def version(self):
		return self._version
		
	def description(self):
		return self._description
		
	def long_description(self):
		return self._long_description
		
	def path(self):
		return self._path
