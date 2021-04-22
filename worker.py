# coding=utf-8
#
# For scheduled jobs
# 
from factset.data import getGenevaPositions, getGenevaDividendReceivable \
						, getGenevaCashLedger, getSecurityIdAndType \
						, getPortfolioNames, getFxTable, getGenevaNav \
						, getGenevaPurchaseSales
from factset.factset_position import getPositions
from factset.utility import getOutputDirectory
from steven_utils.utility import writeCsv, dictToValues
from toolz.functoolz import compose
from functools import partial
from itertools import chain
from os.path import join
from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__)



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



def writeFxTableCsv(outputDir, date):
	"""
	[String] output directory,
	[String] date (yyyy-mm-dd)
		=> [String] output csv

	Side effect: create a csv file in the output directory.
	"""
	return compose(
		partial( writeCsv
			   , _getOutputFilename(outputDir, 'fx_table', date, '')
			   )
	  , partial(chain, [_getFxTableCsvHeaders()])
	  , partial(map, partial(dictToValues, _getFxTableCsvHeaders()))
	  , getFxTable
	)(date)



def _doCsvOutput( positionGetterFunc, csvHeaders, filePrefix
				, outputDir, date, portfolio):
	"""
	[Function] (([String] date, [String] portfolio) -> [Iterable] positions),
	[Tuple] csv headers,
	[String] csv file prefix
	[String] output directory,
	[String] date (yyyy-mm-dd),
	[String] portfolio
		=> [String] output csv

	Side effect: create a csv file in the output directory.
	"""
	logger.debug('_doCsvOutput(): {0}, {1}, {2}'.format(filePrefix, date, portfolio))

	return compose(
		partial( writeCsv
			   , _getOutputFilename(outputDir, filePrefix, date, portfolio)
			   )
	  , partial(chain, [csvHeaders])
	  , partial(map, partial(dictToValues, csvHeaders))
	  , positionGetterFunc
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



def _getPurchaseSalesCsvHeaders():
	return \
	( 'Portfolio', 'PeriodStartDate', 'PeriodEndDate', 'KnowledgeDate', 'BookCurrency'
	, 'TradeDate', 'SettleDate', 'TranType', 'InvestID', 'Investment', 'CustodianAccount'
	, 'Quantity', 'Price', 'SEC', 'LocalAmount', 'BookAmount', 'ContractDate', 'TranID'
	, 'GenericInvestment', 'Broker', 'Trader', 'Commission', 'Expenses', 'LocalCurrency'
	, 'TotalBookAmount'
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



def _getFactsetPositionCsvHeaders():
	return \
	( 'Portfolio Name', 'Portfolio Description', 'Date', 'Symbol', 'Security Name'
	, 'Asset Class', 'Asset Type', 'Shares', 'Price', 'Price ISO', 'Per Share Accrued Interest'
	, 'Per Share Principal', 'Per Share Income', 'Underlying ID', 'Total Cost', 'Contract Size'
	, 'Ending Market Value', 'Strategy', 'Average Cumulative Cost'
	)



def _getFxTableCsvHeaders():
	return ('Date', 'Portfolio', 'Currency', 'TargetCurrency', 'ExchangeRate')



"""
	[String] output directory, [String] date (yyyy-mm-dd), [String] portfolio
		=> [String] output csv

	Side effect: create a csv file in the output directory.
"""
_writeFactPositionToCsv = partial(
	_doCsvOutput
  , getPositions
  , _getFactsetPositionCsvHeaders()
  , 'factset_position'
)



"""
	[String] output directory, [String] date (yyyy-mm-dd), [String] portfolio
		=> [String] output csv

	Side effect: create position csv file in the output directory.
"""
_writeGenevaPositionCsv = partial(
	_doCsvOutput
  , getGenevaPositions
  , _getTaxlotCsvHeaders()
  , 'positions'
)



"""
	[String] output directory, [String] date (yyyy-mm-dd), [String] portfolio
		=> [String] output csv

	Side effect: create position csv file in the output directory.
"""
_writeGenevaCashLedgerCsv = partial(
	_doCsvOutput
  , getGenevaCashLedger
  , _getCashLedgerCsvHeaders()
  , 'cash_ledger'
)



"""
	[String] output directory, [String] date (yyyy-mm-dd), [String] portfolio
		=> [String] output csv

	Side effect: create position csv file in the output directory.
"""
_writeGenevaPurchaseSalesCsv = partial(
	_doCsvOutput
  , getGenevaPurchaseSales
  , _getPurchaseSalesCsvHeaders()
  , 'purchase_sales'
)



"""
	[String] output directory, [String] date (yyyy-mm-dd), [String] portfolio
		=> [String] output csv

	Side effect: create position csv file in the output directory.
"""
_writeDividendReceivableCsv = partial(
	_doCsvOutput
  , getGenevaDividendReceivable
  , _getDividendReceivableCsvHeaders()
  , 'dividend_receivable'
)




if __name__ == "__main__":
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	logger.debug('main(): start')

	import argparse
	parser = argparse.ArgumentParser(description='handle fact positions')
	parser.add_argument('date', metavar='date', type=str, help="position date (yyyy-mm-dd)")
	parser.add_argument('portfolio', metavar='portfolio', type=str, help="portfolio id")

	# print(_writeGenevaPositionCsv(getOutputDirectory(), parser.parse_args().date, parser.parse_args().portfolio))
	# print(_writeDividendReceivableCsv(getOutputDirectory(), parser.parse_args().date, parser.parse_args().portfolio))
	# print(_writeGenevaCashLedgerCsv(getOutputDirectory(), parser.parse_args().date, parser.parse_args().portfolio))
	# print(_writeGenevaPurchaseSalesCsv(getOutputDirectory(), parser.parse_args().date, parser.parse_args().portfolio))
	# print(getGenevaNav(parser.parse_args().date, parser.parse_args().portfolio))
	# print(getSecurityIdAndType())
	# print(getPortfolioNames())

	# print(
	# 	_writeFactPositionToCsv(
	# 		getOutputDirectory()
	# 	  , parser.parse_args().date
	# 	  , parser.parse_args().portfolio
	# 	)
	# )

	startingDay = datetime(2021,3,1)
	# for d in range(31):
	# 	print((startingDay + timedelta(days=d)).strftime('%Y-%m-%d'))
	# 	print(
	# 		_writeFactPositionToCsv(
	# 			getOutputDirectory()
	# 		  , (startingDay + timedelta(days=d)).strftime('%Y-%m-%d')
	# 		  , '12307'
	# 		)
	# 	)


	positions = []
	for d in range(31):
		date = (startingDay + timedelta(days=d)).strftime('%Y-%m-%d')
		_, nav = getGenevaNav(date, '12307')
		positions = positions + [(date, nav)]

	writeCsv('12307_nav_2021Mar.csv', chain([('date', 'nav')], positions))
	# print(writeFxTableCsv(getOutputDirectory(), parser.parse_args().date))