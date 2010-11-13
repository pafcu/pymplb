# -*- coding: utf-8 -*-

# Copyright (c) 2010, Stefan Parviainen <pafcu@iki.fi>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
pymplb (PYthonMPLayerBingings) is a library that can be used to play media using an external MPlayer process.
The library runs the MPlayer binary in slave mode as a subprocess and then sends slave-mode commands to the process.
Commands are mapped to class methods and properties to class properties (by default prefixed with 'p_').
Commands are discovered at runtime and thus these bindings should automatically also support any new commands added to MPlayer in the future.
An example:
>>> import pymplb
>>> player = pymplb.MPlayer()
>>> player.loadfile('test.ogv')
>>> player.p_filename
'test.ogv'
"""

from functools import partial
import subprocess
import atexit

class PlayerNotFoundException(Exception):
	"""Exception which is raised when the external mplayer binary is not found."""
	def __init__(self, player_path):
		Exception.__init__(self, 'Player not found at %s'%player_path)

def make_mplayer_class(mplayer_bin='mplayer', method_prefix='', property_prefix='p_'):
	"""
	Construct a MPlayer class which user mplayer_bin as the platyer binary and prepends the given prefixes to property and method names.
	Prefixes are needed because some properties and methods have the same name.
	You only need to construct a new class if the default values are not suitable (i.e. mplayer is not in your path, or some new commands have been introduced that conflict with the default prefixes.
	"""

	# Yes, I'm aware it's a bit messy to have a function in a function in a class in a function
	# Decrease your indentation and bear with me here
	class _MPlayer(object): #pylint: disable-msg=R0903
		"""
		This is the main class used to play audio and video files by launching mplayer as a subprocess in slave mode.
		Slave mode methods can be called directly (e.g. x.loadfile("somefile)") while properties are prefixed to avoid
		name conflicts between methods and properties (e.g. x.p_looping = False).
		Available methods and properties are determined at runtime when the class is instantiated. All methods and properties are
		type-safe and properties respect minimum and maximum values given by mplayer.
		"""
		_arg_types = {'Flag':type(False), 'String':type(''), 'Integer':type(0), 'Float':type(0.0), 'Position':type(0.0), 'Time':type(0.0)} # Mapping from mplayer -> Python types
		_player_methods = {} # Need to keep track of methods because they must be modified after they have been added

		def __init__(self, mplayer_args_d=None, **mplayer_args):
			if mplayer_args_d: # Make pylint happy by not passing {} as an argument
				mplayer_args.update(mplayer_args_d)
			cmd_args = [mplayer_bin, '-slave', '-quiet', '-idle', '-msglevel', 'all=-1:global=4']
			for (name, value) in mplayer_args.items():
				cmd_args.append('-'+name)
				if value != None and value != True:
					cmd_args.append(str(value))

			self.__player = _MPlayer._run_player(cmd_args)

			# Partially apply methods to use the newly created player
			for (name, func) in self._player_methods.items():
				setattr(self, name, partial(func, self.__player))

			atexit.register(self.__cleanup) # Make sure subprocess is killed

		def __cleanup(self):
			"""Method that kills the MPlayer subprocess when the application using the library exits"""
			self.__player.terminate()

		@staticmethod
		def _run_player(args):
			"""Helper function that runs MPlayer with the given arguments"""
			try:
				player = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			except OSError, err:
				if err.errno == 2:
					raise PlayerNotFoundException(args[0])
				else:
					raise err
			return player

		@classmethod
		def _add_methods(cls, mplayer_bin):
			"""Discover which commands MPlayer understands and add them as class methods"""
			def cmd(name, argtypes, obligatory, player, *args, **kwargs):
				"""Function which sends the given command to the MPlayer process"""
				if len(args) < obligatory:
					raise TypeError('TypeError: %s() takes at least %d arguments (%d given)'%(name, obligatory, len(args)))
				if len(args) > len(argtypes):
					raise TypeError('TypeError: %s() takes at most %d arguments (%d given)'%(name, len(argtypes), len(args)))
				for i in range(len(args)):
					if type(args[i]) != argtypes[i]:
						raise TypeError('Argument %d of %s() has type %s, should be %s'%(i, name, type(args[i]).__name__, argtypes[i].__name__))
				pausing = kwargs.get('pausing','pausing_keep')
				if pausing != '':
					pausing = pausing + ' '

				mplayer_command = '%s%s %s\n' % (pausing, name, ' '.join((str(x) for x in args)))
				player.stdin.write(mplayer_command.encode('utf-8'))
				player.stdin.flush()

				# Read return value of commands that give one
				# Hopefully this is smart enough ...
				if name.startswith('get_'):
					retval = str(player.stdout.readline().decode('utf-8')).split('=', 2)[1].rstrip()
					if retval == 'PROPERTY_UNAVAILABLE':
						return None
					else:
						return retval

			player = cls._run_player([mplayer_bin, '-input', 'cmdlist'])

			# Add each command found
			for line in player.stdout:
				line = str(line.decode('utf-8'))
				parts = line.strip().split()
				name = parts[0]
				args = parts[1:]
				if len(parts) > 1:
					obligatory = len([x for x in args if x[0] != '[']) # Number of obligatory args
					argtypes = [cls._arg_types[y] for y in [x.strip('[]') for x in args]]

				method = partial(cmd, name, argtypes, obligatory)
				if len(args) == 0:
					method.__doc__ = 'Method taking no arguments'
				elif len(args) == 1:
					method.__doc__ = 'Method taking argument of type %s' % args[0]
				else:
					method.__doc__ = 'Method taking arguments of types %s' % ' '.join(args)

				cls._player_methods[cls._method_prefix+name] = method
				setattr(cls, cls._method_prefix+name, method)

		@classmethod
		def _add_properties(cls, mplayer_bin):
			"""Discover which properties MPlayer understands and add them as class properties"""
			def get_prop(name, prop_type, islist, self):
				"""Function which calls the get_property method to get the property value and does some type checking"""
				# self argument is needed to be property at the end because of partial
				retval = getattr(self, cls._method_prefix+'get_property')(name)
				if islist and retval == '(null)':
					return []
				if retval != None:
					if prop_type != type(False):
						if islist:
							retval = [prop_type(x) for x in retval.split(',')]
						else:
							retval = prop_type(retval)
					else:
						if islist:
							retval = [x == 'yes' for x in retval.split(',')]
						else:
							retval = (retval == 'yes')
				return retval

			# Function for getting and setting properties
			def set_prop(name, prop_type, islist, prop_min, prop_max, self, value):
				"""Function which calls the set_property method to set the property value and does some type checking"""
				if islist:
					for elem in value:
						if type(elem) != prop_type:
							raise TypeError('TypeError: Element %s has wrong type %s, not %s'%(elem, type(elem).__name__, prop_type))
						if prop_min != None and elem < prop_min:
							raise ValueError('ValueError: Element %s must be at least %s'%(elem, prop_min))
						if prop_max != None and elem > prop_max:
							raise ValueError('ValueError: Element %s must be at most %s'%(elem, prop_max))
					value = ','.join([str(elem) for elem in value])
				else:
					if type(value) != prop_type:
						raise TypeError('TypeError: %s has type %s, not %s'%(name, prop_type.__name__, type(value).__name__))
					if prop_min != None and value < prop_min:
						raise ValueError('ValueError: %s must be at least %s (>%s)'%(name, prop_min, value))
					if prop_max != None and value > prop_max:
						raise ValueError('ValueError: %s must be at most %s (<%s)'%(name, prop_max, value))

				getattr(self, cls._method_prefix+'set_property')(name, str(value))
					
			player = cls._run_player([mplayer_bin, '-list-properties'])
			# Add each property found
			for line in player.stdout:
				line = str(line.decode('utf-8'))
				parts = line.strip().split()
				if not (len(parts) == 4 or (len(parts) == 5 and parts[2] == 'list')):
					continue
				name = parts[0]
				try:
					prop_type = cls._arg_types[parts[1]]
				except KeyError:
					continue
					
				if parts[2] == 'list': # Actually a list
					prop_min = parts[3]
					prop_max = parts[4]
					islist = True
				else:
					prop_min = parts[2]
					prop_max = parts[3]
					islist = False

				if prop_min == 'No':
					prop_min = None
				else:
					prop_min = prop_type(prop_min)

				if prop_max == 'No':
					prop_max = None
				else:
					prop_max = prop_type(prop_max)

				getter = partial(get_prop, name, prop_type, islist)
				setter = partial(set_prop, name, prop_type, islist, prop_min, prop_max)
				setattr(cls, cls._property_prefix+name, property(getter, setter, doc='Property of type %s in range [%s, %s].'%(prop_type.__name__, prop_min, prop_max)))
	# end of _MPlayer

	_MPlayer._method_prefix = method_prefix
	_MPlayer._property_prefix = property_prefix

	_MPlayer._add_methods(mplayer_bin)
	_MPlayer._add_properties(mplayer_bin)
	return _MPlayer

MPlayer = make_mplayer_class() # pylint: disable-msg=C0103

if __name__ == "__main__":
	import doctest
	doctest.testmod(optionflags=doctest.ELLIPSIS)
