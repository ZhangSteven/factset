# coding=utf-8
#
# For scheduled jobs
# 
from factset.geneva_position import readMultipartCashLedgerReport \
								, readMultipartTaxlotReport \
								, readMultipartDividendReceivableReport
from factset.data import getGenevaPositions, getGenevaDividendReceivable
from steven_utils.utility import writeCsv, dictToValues
from toolz.functoolz import compose
from functools import partial
from itertools import chain
from os.path import join
import logging
logger = logging.getLogger(__name__)



def processMultipartTaxlotReport(outputDir, file):
	"""
	[String] output directory,
	[String] multipart tax lot report (TXT) 
		=> [String] output csv

	Side effect: create a csv file in the output directory.
	"""
	logger.debug('processMultipartTaxlotReport(): {0}'.format(file))

	positions = list(readMultipartTaxlotReport('utf-16', '\t', file))
	
	return \
	compose(
		partial(writeCsv, _getOutputFilename(outputDir, 'tax_positions', positions))
	  , partial(chain, [_getTaxlotCsvHeaders()])
	  , partial(map, partial(dictToValues, _getTaxlotCsvHeaders()))
	)(positions)



def processMultipartCashLedgerReport(outputDir, file):
	"""
	[String] output directory,
	[String] multipart tax lot report (TXT) 
		=> [String] output csv

	Side effect: create a csv file in the output directory.
	"""
	logger.debug('processMultipartCashLedgerReport(): {0}'.format(file))

	positions = list(readMultipartCashLedgerReport('utf-16', '\t', file))
	
	return \
	compose(
		partial(writeCsv, _getOutputFilename(outputDir, 'cash_ledger', positions))
	  , partial(chain, [_getCashLedgerCsvHeaders()])
	  , partial(map, partial(dictToValues, _getCashLedgerCsvHeaders()))
	)(positions)



def processMultipartDividendReceivableReport(outputDir, file):
	"""
	[String] output directory,
	[String] multipart tax lot report (TXT) 
		=> [String] output csv

	Side effect: create a csv file in the output directory.
	"""
	logger.debug('processMultipartDividendReceivableReport(): {0}'.format(file))

	positions = list(readMultipartDividendReceivableReport('utf-16', '\t', file))
	
	return \
	compose(
		partial(writeCsv, _getOutputFilename(outputDir, 'dividend_receivable', positions))
	  , partial(chain, [_getDividendReceivableCsvHeaders()])
	  , partial(map, partial(dictToValues, _getDividendReceivableCsvHeaders()))
	)(positions)



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



def _getOutputFilename(outputDir, prefix, positions):
	"""
	[String] prefix, [List] positions => [String] output csv file name
	"""
	if len(positions) == 0:
		logger.error('_getOutputFilename(): no positions')
		raise ValueError

	return join( outputDir
			   , prefix + '_' + _changeDateFormat(positions[0]['PeriodEndDate']) + '_' \
			   		+ _changeDateHourFormat(positions[0]['KnowledgeDate']) + '.csv'
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
	# parser.add_argument('file', metavar='file', type=str, help="input file")
	# print(processMultipartTaxlotReport('', parser.parse_args().file))
	# print(processMultipartCashLedgerReport('', parser.parse_args().file))
	# print(processMultipartDividendReceivableReport('', parser.parse_args().file))

	parser.add_argument('date', metavar='date', type=str, help="position date (yyyy-mm-dd)")
	parser.add_argument('portfolio', metavar='portfolio', type=str, help="portfolio id")
	print(getGenevaPositions( parser.parse_args().date
							, parser.parse_args().portfolio
							))
	# print(getGenevaDividendReceivable( parser.parse_args().date
	# 								 , parser.parse_args().portfolio))
	# print(getGenevaDividendReceivable( parser.parse_args().date
	# 								 , '11490-B'))