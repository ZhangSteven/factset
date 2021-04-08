# coding=utf-8
# 

import unittest2
from factset.position import readMultipartTaxlotReport
from os.path import join



class TestPosition(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestPosition, self).__init__(*args, **kwargs)


	def testMultipartTaxlotReport(self):
		self.assertEqual(1, 1)