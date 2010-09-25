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

# BUG: Lists are not supported
class MPlayer(object):
	"""This is the main class used to play audio and video files by launching mplayer as a subprocess in slave mode. Slave mode methods can be called directly (e.g. x.loadfile("somefile)") while properties are prefixed to avoid name conflicts between methods and properties (e.g. x.p_looping = False). Available methods and properties are determined at runtime when the class is instantiated. All methods and properties are type-safe and properties respect minimum and maximum values given by mplayer."""
	arg_types = {'Flag':type(False), 'String':type(''), 'Integer':type(0), 'Float':type(0.0), 'Position':type(0.0), 'Time':type(0.0)} # Mapping from mplayer -> Python types
	def __run_player(self,args):
		try:
			player = subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		except OSError, e:
			if e.errno == 2:
				raise PlayerNotFoundException(args[0])
			else:
				raise e
		return player

	def __add_methods(self, mplayer_bin):
		# Function which is run for each mplayer command
		def cmd(name, argtypes, obligatory, *args, **kwargs):
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
			print >>self.__player.stdin, pausing+name,' '.join((str(x) for x in args))

			# Read return value of commands that give one
			# Hopefully this is smart enough ...
			if name.startswith('get_'):
				r = self.__player.stdout.readline().split('=',2)[1].rstrip()
				if r=='PROPERTY_UNAVAILABLE':
					return None
				else:
					return r


		player = self.__run_player([mplayer_bin,'-input','cmdlist'])
			

		# Add each command found
		for line in player.stdout:
			parts = line.strip().split()
			name = parts[0]
			args = []
			if len(parts) > 1:
				obligatory = len([x for x in parts[1:] if x[0] != '[']) # Number of obligatory args
				argtypes = [MPlayer.arg_types[y] for y in [x.strip('[]') for x in parts[1:]]]

			self.__dict__[name] = partial(cmd, name, argtypes, obligatory)
			

	def __add_properties(self, mplayer_bin):
		def get_prop(name,p_type,self):
			# self argument is needed to be property, at the end because of partial
			r = self.get_property(name)
			if r != None:
				if p_type != type(False):
					r = p_type(r)
				else:
					r = r == 'yes'
			return r

		# Function for getting and setting properties
		def set_prop(name, p_type, min, max, self, value):
			if type(value) != p_type:
				raise TypeError('TypeError: %s has type %s, not %s'%(name,p_type,type(value).__name__))
			if min != None and value < min:
				raise TypeError('TypeError: %s must be at least %s (>%s)'%(name,min,value))
			if max != None and value > max:
				raise TypeError('TypeError: %s must be at most %s (<%s)'%(name,max,value))

			self.set_property(name,str(value))
				
		player = self.__run_player([mplayer_bin,'-list-properties'])
		# Add each property found
		for line in player.stdout:
			parts = line.strip().split()
			if len(parts) != 4:
				continue
			name = parts[0]
			try:
				p_type = MPlayer.arg_types[parts[1]]
			except KeyError, e:
				continue
				
			min = parts[2]
			max = parts[3]
			if min == 'No':
				min = None
			else:
				min = p_type(min)

			if max == 'No':
				max = None
			else:
				max = p_type(max)

			getter = partial(get_prop, name, p_type)
			setter = partial(set_prop, name, p_type, min, max)
			setattr(self.__class__,self.__property_prefix+name,property(getter,setter))

	def __init__(self, mplayer_bin='mplayer', property_prefix='p_', mplayer_args_d={}, **mplayer_args):
		self.__property_prefix = property_prefix
		self.__add_methods(mplayer_bin)
		self.__add_properties(mplayer_bin)
		mplayer_args.update(mplayer_args_d)
		cmd_args = [mplayer_bin,'-slave','-quiet','-idle','-msglevel','all=-1:global=4']
		for (k,v) in mplayer_args.items():
			cmd_args.append('-'+k)
			cmd_args.append(v)

		self.__player = self.__run_player(cmd_args)

		atexit.register(self.__cleanup) # Make sure subprocess is killed

	def __cleanup(self):
		self.__player.terminate()

if __name__ == '__main__':
	p = MPlayer()
	p.loadfile('test')
	p.af_add('scaletempo')
	p.speed_set(2.0)
	sys.stdin.readline()
	print p.p_time_pos
	sys.stdin.readline()
	p.p_time_pos = 10.0
	sys.stdin.readline()
	print p.p_time_pos
	sys.stdin.readline()
