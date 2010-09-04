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

# BUG: Lists are not supported
class MPlayer():
	arg_types = {'Flag':type(False), 'String':type(''), 'Integer':type(0), 'Float':type(0.0), 'Position':type(0.0), 'Time':type(0.0)} # Mapping from mplayer -> Python types

	def add_methods(self, mplayer_bin):
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
			print >>self.player.stdin, pausing+name,' '.join((str(x) for x in args))

			# Read return value of commands that give one
			# Hopefully this is smart enough ...
			if name.startswith('get_'):
				r = self.player.stdout.readline().split('=',2)[1].rstrip()
				if r=='PROPERTY_UNAVAILABLE':
					return None
				else:
					return r


		self.methods = {}
		player = subprocess.Popen([mplayer_bin,'-input','cmdlist'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)

		# Add each command found
		for line in player.stdout:
			parts = line.strip().split()
			name = parts[0]
			args = []
			if len(parts) > 1:
				obligatory = len([x for x in parts[1:] if x[0] != '[']) # Number of obligatory args
				argtypes = [MPlayer.arg_types[y] for y in [x.strip('[]') for x in parts[1:]]]

			self.methods[name] = partial(cmd, name, argtypes, obligatory)

	def add_properties(self, mplayer_bin):
		# Function for getting and setting properties
		def prop(name, p_type, min, max, value=None, **kwargs):
			if value == None:
				r = self.get_property(name,**kwargs)
				if r != None:
					r = p_type(r)
				return r

			if type(value) != p_type:
				raise TypeError('TypeError: %s has type %s, not %s'%(name,p_type,type(value).__name__))
			if min != None and value < min:
				raise TypeError('TypeError: %s must be at least %s (>%s)'%(name,min,value))
			if max != None and value > max:
				raise TypeError('TypeError: %s must be at most %s (<%s)'%(name,max,value))

			self.set_property(name,str(value),**kwargs)
				
		self.properties = {}
		player = subprocess.Popen([mplayer_bin,'-list-properties'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		# Add each property found
		for line in player.stdout:
			parts = line.strip().split()
			if len(parts) != 4:
				continue
			name = parts[0]
			try:
				p_type = MPlayer.arg_types[parts[1]]
			except KeyError, e:
				print e
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

			self.methods['p_'+name] = partial(prop, name, p_type, min, max)

	def __init__(self,mplayer_bin='mplayer', mplayer_args_d={}, **mplayer_args):
		self.add_methods(mplayer_bin)
		self.add_properties(mplayer_bin)
		mplayer_args.update(mplayer_args_d)
		cmd_args = [mplayer_bin,'-slave','-quiet','-idle','-msglevel','all=-1:global=4']
		for (k,v) in mplayer_args.items():
			cmd_args.append('-'+k)
			cmd_args.append(v)

		self.player = subprocess.Popen(cmd_args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

		atexit.register(self.cleanup) # Make sure subprocess is killed

	def cleanup(self):
		self.player.terminate()

	def __getattr__(self, m):
		try:
			return self.methods[m]
		except KeyError:
			raise AttributeError("'%s' object has no attribute '%s'"%(type(self).__name__,m))

if __name__ == '__main__':
	p = MPlayer()
	p.loadfile('test')
	p.af_add('scaletempo')
	p.speed_set(2.0)
	sys.stdin.readline()
	print p.p_time_pos()
	sys.stdin.readline()
	p.p_time_pos(10.0)
	sys.stdin.readline()
	print p.p_time_pos()
	sys.stdin.readline()
