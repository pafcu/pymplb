import unittest
import pymplb

class TestMPlayer(unittest.TestCase):
	def testReadProperty(self):
		player = pymplb.MPlayer()
		r = player.p_loop
		self.assertEqual(r,-1)
		player.close()

	def testWriteProperty(self):
		player = pymplb.MPlayer()
		player.p_loop = 5
		r = player.p_loop
		self.assertEqual(r,5)
		player.close()

	def testMethod(self):
		player = pymplb.MPlayer()
		player.set_property('loop','1')
		r  = player.get_property('loop')
		self.assertEqual(r,'1')
		player.close()

	def testListProperty(self):
		player = pymplb.MPlayer()
		player.loadfile('test.ogv')
		r = player.p_metadata
		self.assertEqual(type(r),type([]))
		player.close()

	def testNullProperty(self):
		player = pymplb.MPlayer()
		r = player.p_filename
		self.assertEqual(r,None)
		player.close()

	def testLoadedFileProperties(self):
		player = pymplb.MPlayer(fs=True)
		player.loadfile('test.ogv')
		r = player.p_filename
		self.assertNotEqual(r,None)
		player.close()

	def testOtherPrefix(self):
		player = pymplb.make_mplayer_class(property_prefix='prop_',method_prefix='m_')()
		r = player.prop_loop
		player.prop_loop = 5
		r = player.m_get_property('loop')
		self.assertRaises(AttributeError,lambda: player.p_loop)
		self.assertRaises(AttributeError,lambda: player.get_property('loop'))
		player.close()

	def testMethodTooManyArgs(self):
		player = pymplb.MPlayer()
		self.assertRaises(TypeError,lambda: player.get_property('loop','foo'))
		player.close()

	def testMethodTooFewArgs(self):
		player = pymplb.MPlayer()
		self.assertRaises(TypeError,lambda: player.get_property())
		player.close()

	def testMethodType(self):
		player = pymplb.MPlayer()
		self.assertRaises(TypeError,lambda:player.get_property(0))
		player.close()

	def testSetPropertyType(self):
		player = pymplb.MPlayer()
		def f():
			player.p_loop = '0'
		self.assertRaises(TypeError,f)
		player.close()

	def testGetpropertyType(self):
		player = pymplb.MPlayer()
		r = player.p_loop
		self.assertEqual(type(r),type(0))
		player.close()

	def testInitArgumentsDict(self):
		player = pymplb.MPlayer(mplayer_args_d={'fs':True,'speed':2.0})
		player.loadfile('test.ogv')
		player.close()

	def testInitArgumentsKw(self):
		player = pymplb.MPlayer(fs=True,speed=2.0)
		player.loadfile('test.ogv')
		player.close()

	def testPausing(self):
		player = pymplb.MPlayer()
		player.get_property('loop',pausing='pausing')
		player.close()

if __name__ == '__main__':
	unittest.main()
