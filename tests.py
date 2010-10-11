import unittest
import pymplb

class TestMPlayer(unittest.TestCase):
	def testReadProperty(self):
		player = pymplb.MPlayer()
		r = player.p_loop
		self.assertEqual(r,-1)

	def testWriteProperty(self):
		player = pymplb.MPlayer()
		player.p_loop = 5
		r = player.p_loop
		self.assertEqual(r,5)

	def testMethod(self):
		player = pymplb.MPlayer()
		player.set_property('loop','1')
		r  = player.get_property('loop')
		self.assertEqual(r,'1')

	def testListProperty(self):
		player = pymplb.MPlayer()
		player.loadfile('test.ogv')
		r = player.p_metadata
		self.assertEqual(type(r),type([]))

	def testNullProperty(self):
		player = pymplb.MPlayer()
		r = player.p_filename
		self.assertEqual(r,None)

	def testLoadedFileProperties(self):
		player = pymplb.MPlayer(fs=True)
		player.loadfile('test.ogv')
		r = player.p_filename
		self.assertNotEqual(r,None)

	def testOtherPrefix(self):
		player = pymplb.make_mplayer_class(property_prefix='prop_',method_prefix='m_')()
		r = player.prop_loop
		player.prop_loop = 5
		r = player.m_get_property('loop')
		self.assertRaises(AttributeError,lambda: player.p_loop)
		self.assertRaises(AttributeError,lambda: player.get_property('loop'))

	def testMethodTooManyArgs(self):
		player = pymplb.MPlayer()
		self.assertRaises(TypeError,lambda: player.get_property('loop','foo'))

	def testMethodTooFewArgs(self):
		player = pymplb.MPlayer()
		self.assertRaises(TypeError,lambda: player.get_property())

	def testMethodType(self):
		player = pymplb.MPlayer()
		self.assertRaises(TypeError,lambda:player.get_property(0))

	def testSetPropertyType(self):
		player = pymplb.MPlayer()
		def f():
			player.p_loop = '0'
		self.assertRaises(TypeError,f)

	def testGetpropertyType(self):
		player = pymplb.MPlayer()
		r = player.p_loop
		self.assertEqual(type(r),type(0))

	def testInitArgumentsDict(self):
		player = pymplb.MPlayer({'fs':True,'speed':2.0})
		player.loadfile('test.ogv')

	def testInitArgumentsKw(self):
		player = pymplb.MPlayer(fs=True,speed=2.0)
		player.loadfile('test.ogv')

	def testPausing(self):
		player = pymplb.MPlayer()
		player.get_property('loop',pausing='pausing')

if __name__ == '__main__':
	unittest.main()
