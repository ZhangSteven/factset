# coding=utf-8
# 

import unittest2
from factset.geneva_position import readMultipartTaxlotReport \
								, readMultipartCashLedgerReport
from steven_utils.iter import firstOf
from toolz.functoolz import compose
from functools import partial
from itertools import filterfalse
from os.path import join, dirname, abspath



def currentDir():
	"""
	Get the absolute path to the directory where this module is in.

	This piece of code comes from:

	http://stackoverflow.com/questions/3430372/how-to-get-full-path-of-current-files-directory-in-python
	"""
	return dirname(abspath(__file__))



def isTaxlotCash(position):
	return position['ThenByDescription'] == 'Cash and Equivalents'


def isTaxlotFixedDeposit(position):
	return position['ThenByDescription'] == 'Fixed Deposit'


def isTaxlotFXForward(position):
	return position['ThenByDescription'] == 'FX Forward'



class TestGenevaPosition(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestGenevaPosition, self).__init__(*args, **kwargs)



	def testMultipartTaxlotReport(self):
		file = join(currentDir(), 'samples', 'all funds tax lot 2021-03-31.txt')
		positions = compose(
			list
		  , partial(filter, lambda p: p['Portfolio'] == '12307')
		  , readMultipartTaxlotReport
		)('utf-16', '\t', file)

		cashPositions = list(filter(isTaxlotCash, positions))
		self.assertEqual(7, len(cashPositions))

		p = sorted(cashPositions, key=lambda p: p['Quantity'])[0]
		self.assertAlmostEqual(-80050151.41, p['Quantity'])
		self.assertEqual('HKD', p['InvestID'])

		otherPositions = list(filterfalse(isTaxlotCash, positions))
		self.assertEqual(114, len(otherPositions))

		p = firstOf(lambda p: p['InvestID'] == '1088 HK', otherPositions)
		self.assertEqual(761500, p['Quantity'])
		self.assertAlmostEqual(14.687, p['UnitCost'], 3)
		self.assertEqual(16.02, p['MarketPrice'])
		self.assertEqual(1569143.80, p['MarketValueBook'])
		self.assertEqual(0, p['AccruedInterestBook'])
		self.assertEqual( 134206.70
						, p['UnrealizedPriceGainLossBook'] + p['UnrealizedFXGainLossBook']
						)



	def testMultipartTaxlotReport2(self):
		file = join(currentDir(), 'samples', 'all funds tax lot 2021-03-31.txt')
		positions = compose(
			list
		  , partial(filter, lambda p: p['Portfolio'] == '60001')
		  , readMultipartTaxlotReport
		)('utf-16', '\t', file)

		cashPositions = list(filter(isTaxlotCash, positions))
		self.assertEqual(10, len(cashPositions))

		fdPositions = list(filter(isTaxlotFixedDeposit, positions))
		self.assertEqual(13, len(fdPositions))

		p = firstOf( lambda p: p['InvestID'] == 'IB Fixed Deposit 0.651 07/08/2021'
				   , fdPositions)
		self.assertEqual(5000000, p['Quantity'])
		self.assertEqual(7504.58, p['AccruedInterestBook'])

		p = firstOf(lambda p: p['InvestID'] == 'US06120TAA60', positions)
		self.assertEqual(7273000, p['Quantity'])
		self.assertAlmostEqual(112.186, p['UnitCost'], 3)
		self.assertEqual(112.449, p['MarketPrice'])
		self.assertEqual(8178415.77, p['MarketValueBook'])
		self.assertAlmostEqual(139399.17, p['AccruedInterestBook'])
		self.assertEqual( 19121.06
						, p['UnrealizedPriceGainLossBook'] + p['UnrealizedFXGainLossBook']
						)



	def testMultipartTaxlotReport3(self):
		file = join(currentDir(), 'samples', 'all funds tax lot 2021-03-31.txt')
		positions = compose(
			list
		  , partial(filter, lambda p: p['Portfolio'] == '40017')
		  , readMultipartTaxlotReport
		)('utf-16', '\t', file)

		fxPositions = list(filter(isTaxlotFXForward, positions))
		self.assertEqual(14, len(fxPositions))

		p = firstOf( lambda p: p['TaxLotDescription'] == 'CNH per USD @ 7.16' \
						and p['TaxLotID'] == '1120963'
				   , positions
				   )
		self.assertEqual(-4861014.11, p['Quantity'])
		self.assertEqual(6.5485, p['MarketPrice'])
		