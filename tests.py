import unittest
import pymplb
import time
pymplb.initialize()

class TestMPlayer(unittest.TestCase):
	def setUp(self):
		self.player = pymplb.MPlayer()
		self.player.loadfile('test.ogv')
		time.sleep(0.1)
	def testProperty(self):
		r = self.player.p_loop
		self.assertEqual(r,-1)
		self.player.p_loop = 5
		r = self.player.p_loop
		self.assertEqual(r,5)
	def testMethod(self):
		self.player.set_property('loop','1')
		r  = self.player.get_property('loop')
		self.assertEqual(r,'1')
	
if __name__ == '__main__':
	unittest.main()
