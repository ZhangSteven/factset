# coding=utf-8
#
# For scheduled jobs
# 
from factset.data import getGenevaPositions, getGenevaDividendReceivable \
						, getGenevaCashLedger, getSecurityIdAndType \
						, getPortfolioNames
from steven_utils.utility import writeCsv, dictToValues
from toolz.functoolz import compose
from functools import partial
from itertools import chain
from os.path import join
import logging
logger = logging.getLogger(__name__)



def processMultipartTaxlotReport(outputDir, date, portfolio):
	"""
	[String] output directory,
	[String] date (yyyy-mm-dd)
	[String] portfolio
		=> [String] output csv

	Side effect: create a csv file in the output directory.
	"""
	logger.debug('processMultipartTaxlotReport(): {0}, {1}'.format(
				date, portfolio))

	return \
	compose(
		partial( writeCsv
			   , _getOutputFilename( outputDir, 'taxlot_positions'
			   					   , date, portfolio)
			   )
	  , partial(chain, [_getTaxlotCsvHeaders()])
	  , partial(map, partial(dictToValues, _getTaxlotCsvHeaders()))
	  , getGenevaPositions
	)(date, portfolio)



def processMultipartCashLedgerReport(outputDir, date, portfolio):
	"""
	[String] output directory,
	[String] date (yyyy-mm-dd)
	[String] portfolio
		=> [String] output csv

	Side effect: create a csv file in the output directory.
	"""
	logger.debug('processMultipartCashLedgerReport(): {0}, {1}'.format(
				date, portfolio))

	return \
	compose(
		partial( writeCsv
			   , _getOutputFilename( outputDir, 'cash_ledger'
			   					   , date, portfolio)
			   )
	  , partial(chain, [_getCashLedgerCsvHeaders()])
	  , partial(map, partial(dictToValues, _getCashLedgerCsvHeaders()))
	  , getGenevaCashLedger
	)(date, portfolio)



def processMultipartDividendReceivableReport(outputDir, date, portfolio):
	"""
	[String] output directory,
	[String] date (yyyy-mm-dd)
	[String] portfolio
		=> [String] output csv

	Side effect: create a csv file in the output directory.
	"""
	logger.debug('processMultipartDividendReceivableReport(): {0}, {1}'.format(
				date, portfolio))

	return \
	compose(
		partial( writeCsv
			   , _getOutputFilename( outputDir, 'dividend_receivable'
			   					   , date, portfolio)
			   )
	  , partial(chain, [_getDividendReceivableCsvHeaders()])
	  , partial(map, partial(dictToValues, _getDividendReceivableCsvHeaders()))
	  , getGenevaDividendReceivable
	)(date, portfolio)



def _changeDateFormat(s):
	"""
	[String] s (yyyy-mm-dd) => [String] s (yyyymmdd)
	"""
	return '' if s == '' else ''.join(s.split('-'))



def _changeDateHourFormat(s):
	"""
	[String] s (yyyy-mm-dd hh:mm) => [String] s (yyyymmddhhmm)
	"""
	return '' if s == '' else \
	compose(
		lambda t: _changeDateFormat(t[0]) + ''.join(t[1].split(':'))
	  , lambda s: s.split(' ')
	)(s)



def _getOutputFilename(outputDir, prefix, date, portfolio):
	"""
	[String] output directory,
	[String] prefix, 
	[String] date (yyyy-mm-dd)
	[String] portfolio
		=> [String] output csv file name
	"""
	return join( outputDir
			   , prefix + '_' + _changeDateFormat(date) + '_' \
			   		+ portfolio + '.csv'
			   )



def _getTaxlotCsvHeaders():
	return \
	( 'Portfolio', 'PeriodEndDate', 'KnowledgeDate', 'BookCurrency', 'InvestID'
	, 'SortByDescription', 'ThenByDescription', 'InvestmentDescription'
	, 'TaxLotDescription', 'TaxLotID', 'TaxLotDate', 'Quantity', 'OriginalFace'
	, 'UnitCost', 'MarketPrice', 'CostBook', 'MarketValueBook', 'UnrealizedPriceGainLossBook'
	, 'UnrealizedFXGainLossBook', 'AccruedAmortBook', 'AccruedInterestBook'
	# , 'ExtendedDescription', 'Description3'
	)



def _getCashLedgerCsvHeaders():
	return \
	( 'Portfolio', 'PeriodStartDate', 'PeriodEndDate', 'KnowledgeDate', 'BookCurrency'
	, 'Currency_OpeningBalDesc', 'CurrBegBalLocal', 'CurrBegBalBook', 'GroupWithinCurrency_OpeningBalDesc'
	, 'GroupWithinCurrencyBegBalLoc', 'GroupWithinCurrencyBegBalBook', 'CashDate', 'TradeDate'
	, 'SettleDate', 'TransID', 'TranDescription', 'Investment', 'Quantity', 'Price', 'LocalAmount'
	, 'LocalBalance', 'BookAmount', 'BookBalance', 'GroupWithinCurrency_ClosingBalDesc'
	, 'GroupWithinCurrencyClosingBalLoc', 'GroupWithinCurrencyClosingBalBook', 'Currency_ClosingBalDesc'
	, 'CurrClosingBalLocal', 'CurrClosingBalBook'
	)



def _getDividendReceivableCsvHeaders():
	return \
	( 'Portfolio', 'PeriodEndDate', 'KnowledgeDate', 'BookCurrency'
	, 'SortByDescription', 'LocalAccountingName', 'Currency', 'Textbox96'
	, 'Investment', 'TransID', 'EXDate', 'ExDateQuantity', 'LocalCurrency'
	, 'LocalGrossDividendRecPay', 'WHTaxRate', 'LocalWHTaxPayable'
	, 'LocalNetDividendRecPay', 'BookGrossDividendRecPay', 'BookWHTaxPayable'
	, 'BookNetDividendRecPay', 'UnrealizedFXGainLoss', 'PayDate', 'LocalPerShareAmount'
	, 'LocalReclaimReceivable', 'BookReclaimReceivable', 'LocalReliefReceivable'
	, 'BookReliefReceivable'
	)




if __name__ == "__main__":
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	logger.debug('main(): start')

	import argparse
	parser = argparse.ArgumentParser(description='handle fact positions')
	parser.add_argument('date', metavar='date', type=str, help="position date (yyyy-mm-dd)")
	parser.add_argument('portfolio', metavar='portfolio', type=str, help="portfolio id")

	print(processMultipartTaxlotReport('', parser.parse_args().date, parser.parse_args().portfolio))
	print(processMultipartCashLedgerReport('', parser.parse_args().date, parser.parse_args().portfolio))
	print(processMultipartDividendReceivableReport('', parser.parse_args().date, parser.parse_args().portfolio))
	print(getSecurityIdAndType())
	print(getPortfolioNames())