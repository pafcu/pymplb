import unittest
import time
import pymplb

class TestMPlayer(unittest.TestCase):
	def testProperty(self):
		player = pymplb.MPlayer()
		r = player.p_loop
		self.assertEqual(r,-1)
		player.p_loop = 5
		r = player.p_loop
		self.assertEqual(r,5)

	def testMethod(self):
		player = pymplb.MPlayer()
		player.set_property('loop','1')
		r  = player.get_property('loop')
		self.assertEqual(r,'1')

	def testNullProperty(self):
		player = pymplb.MPlayer()
		r = player.p_filename
		self.assertEqual(r,None)

	def testListProperty(self):
		player = pymplb.MPlayer()
		player.loadfile('test.ogv')
		time.sleep(0.1)
		r = player.p_metadata
		self.assertEqual(type(r),type([]))

	def testOtherPrefix(self):
		player = pymplb.makeMPlayerClass(property_prefix='prop_',method_prefix='m_')()
		r = player.prop_loop
		player.prop_loop = 5
		r = player.m_get_property('loop')
		self.assertRaises(AttributeError,lambda: player.p_loop)
		self.assertRaises(AttributeError,lambda: player.get_property('loop'))

if __name__ == '__main__':
	unittest.main()
