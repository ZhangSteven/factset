# coding=utf-8
# 

import unittest2
from factset.geneva_position import readMultipartTaxlotReport
from os.path import join



class TestGenevaPosition(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestGenevaPosition, self).__init__(*args, **kwargs)


	def testMultipartTaxlotReport(self):
		self.assertEqual(1, 1)