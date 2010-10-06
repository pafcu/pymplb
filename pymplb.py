# -*- coding: utf-8 -*-

#Copyright (c) 2010, Stefan Parviainen <pafcu@iki.fi>
#
#Permission to use, copy, modify, and/or distribute this software for any
#purpose with or without fee is hereby granted, provided that the above
#copyright notice and this permission notice appear in all copies.
#
#THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
#WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
#MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
#ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
#WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
#ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
#OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

#See bottom of file for an example usage
import sys
from functools import partial
import subprocess
import atexit

class PlayerNotFoundException(Exception):
	"""Exception which is raised when the external mplayer binary is not found."""
	def __init__(self,player_path):
		Exception.__init__(self,'Player not found at %s'%player_path)

class MPlayer(object):
	"""
	This is the main class used to play audio and video files by launching mplayer as a subprocess in slave mode.
	Slave mode methods can be called directly (e.g. x.loadfile("somefile)") while properties are prefixed to avoid
	name conflicts between methods and properties (e.g. x.p_looping = False).
	Available methods and properties are determined at runtime when the class is instantiated. All methods and properties are
	type-safe and properties respect minimum and maximum values given by mplayer.
	"""
	_arg_types = {'Flag':type(False), 'String':type(''), 'Integer':type(0), 'Float':type(0.0), 'Position':type(0.0), 'Time':type(0.0)} # Mapping from mplayer -> Python types
	_player_methods = {}
	_method_prefix = ''
	_property_prefix = ''

	def __init__(self, mplayer_bin='mplayer', mplayer_args_d={}, **mplayer_args):
		if MPlayer._player_methods == {}:
			initialize() # Initialize class if it hasn't been done explicitly

		mplayer_args.update(mplayer_args_d)
		cmd_args = [mplayer_bin,'-slave','-quiet','-idle','-msglevel','all=-1:global=4']
		for (k,v) in mplayer_args.items():
			cmd_args.append('-'+k)
			cmd_args.append(v)

		self.__player = _run_player(cmd_args)

		# Partially apply methods to use the newly created player
		for (name,f) in MPlayer._player_methods.items():
			setattr(self,name,partial(f,self.__player))

		atexit.register(self.__cleanup) # Make sure subprocess is killed

	def __cleanup(self):
		self.__player.terminate()


def initialize(mplayer_bin='mplayer',method_prefix='',property_prefix='p_'):
	MPlayer._method_prefix = method_prefix
	MPlayer._property_prefix = property_prefix
	_add_methods(mplayer_bin)
	_add_properties(mplayer_bin)

def _add_methods(mplayer_bin):
	# Function which is run for each mplayer command
	def cmd(name, argtypes, obligatory, player, *args, **kwargs):
		if len(args) < obligatory:
			raise TypeError('TypeError: %s() takes at least %d arguments (%d given)'%(name,obligatory,len(args)))
		if len(args) > len(argtypes):
			raise TypeError('TypeError: %s() takes at most %d arguments (%d given)'%(name,len(argtypes),len(args)))
		for i in range(len(args)):
			if type(args[i]) != argtypes[i]:
				raise TypeError('Argument %d of %s() has type %s, should be %s'%(i,name,type(args[i]).__name__,argtypes[i].__name__))
		pausing = kwargs.get('pausing','pausing_keep')
		if pausing != '':
			pausing = pausing + ' '

		s = '%s%s %s\n'%(pausing,name,' '.join((str(x) for x in args)))
		player.stdin.write(s.encode('utf-8'))
		player.stdin.flush()

		# Read return value of commands that give one
		# Hopefully this is smart enough ...
		if name.startswith('get_'):
			r = str(player.stdout.readline().decode('utf-8')).split('=',2)[1].rstrip()
			if r=='PROPERTY_UNAVAILABLE':
				return None
			else:
				return r

	player = _run_player([mplayer_bin,'-input','cmdlist'])

	# Add each command found
	for line in player.stdout:
		line = str(line.decode('utf-8'))
		parts = line.strip().split()
		name = parts[0]
		args = parts[1:]
		if len(parts) > 1:
			obligatory = len([x for x in args if x[0] != '[']) # Number of obligatory args
			argtypes = [MPlayer._arg_types[y] for y in [x.strip('[]') for x in args]]

		f = partial(cmd,name,argtypes,obligatory)
		if len(args) == 0:
			f.__doc__ = 'Method taking no arguments'
		elif len(args) == 1:
			f.__doc__ = 'Method taking argument of type %s'%args[0]
		else:
			f.__doc__ = 'Method taking arguments of types %s'%' '.join(args)

		MPlayer._player_methods[MPlayer._method_prefix+name] = f
		setattr(MPlayer, MPlayer._method_prefix+name, f)

def _add_properties(mplayer_bin):
	def get_prop(name,p_type,islist,self):
		# self argument is needed to be property, at the end because of partial
		r = self.get_property(name)
		if islist and r == '(null)':
			return None
		if r != None:
			if p_type != type(False):
				if islist:
					r = [p_type(x) for x in r.split(',')]
				else:
					r = p_type(r)
			else:
				if islist:
					r = [x == 'yes' for x in r.split(',')]
				else:
					r = (r == 'yes')
		return r

	# Function for getting and setting properties
	def set_prop(name, p_type, islist, min, max, self, value):
		if islist:
			for x in value:
				if type(x) != p_type:
					raise TypeError('TypeError: Element %s has wrong type %s, not %s'%(x,type(x).__name__,p_type))
				if min != None and x < min:
					raise ValueError('ValueError: Element %s must be at least %s'%(x,min))
				if max != None and x > max:
					raise ValueError('ValueError: Element %s must be at most %s'%(x,max))
			value = ','.join([str(x) for x in value])
		else:
			if type(value) != p_type:
				raise TypeError('TypeError: %s has type %s, not %s'%(name,p_type.__name__,type(value).__name__))
			if min != None and value < min:
				raise ValueError('ValueError: %s must be at least %s (>%s)'%(name,min,value))
			if max != None and value > max:
				raise ValueError('ValueError: %s must be at most %s (<%s)'%(name,max,value))

		self.set_property(name,str(value))
			
	player = _run_player([mplayer_bin,'-list-properties'])
	# Add each property found
	for line in player.stdout:
		line = str(line.decode('utf-8'))
		parts = line.strip().split()
		if not (len(parts) == 4 or (len(parts) == 5 and parts[2] == 'list')):
			continue
		name = parts[0]
		try:
			p_type = MPlayer._arg_types[parts[1]]
		except KeyError as e:
			continue
			
		if parts[2] == 'list': # Actually a list
			min = parts[3]
			max = parts[4]
			islist = True
		else:
			min = parts[2]
			max = parts[3]
			islist = False

		if min == 'No':
			min = None
		else:
			min = p_type(min)

		if max == 'No':
			max = None
		else:
			max = p_type(max)

		getter = partial(get_prop, name, p_type, islist)
		setter = partial(set_prop, name, p_type, islist, min, max)
		setattr(MPlayer, MPlayer._property_prefix+name, property(getter,setter, doc='Property of type %s in range [%s, %s].'%(p_type.__name__,min,max)))

def _run_player(args):
	try:
		player = subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	except OSError as e:
		if e.errno == 2:
			raise PlayerNotFoundException(args[0])
		else:
			raise e
	return player

if __name__ == '__main__':
	p = MPlayer()
	p.loadfile('test')
	p.af_add('scaletempo')
	p.speed_set(2.0)
	sys.stdin.readline()
	print(p.p_metadata)
	print(p.p_time_pos)
	sys.stdin.readline()
	print(p.p_time_pos)
	sys.stdin.readline()
	p.p_time_pos = 10.0
	sys.stdin.readline()
	print(p.p_time_pos)
	sys.stdin.readline()
