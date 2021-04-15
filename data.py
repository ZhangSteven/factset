# coding=utf-8
#
# Handle data store operations.
# 
from factset.geneva_position import readMultipartTaxlotReport \
								, readMultipartDividendReceivableReport \
								, readMultipartCashLedgerReport
from factset.utility import getDataDirectory
from steven_utils.file import getFiles
from steven_utils.utility import mergeDict, allEquals
from steven_utils.excel import getRawPositionsFromFile
from toolz.functoolz import compose
from toolz.itertoolz import groupby as groupbyToolz
from toolz.dicttoolz import valmap
from functools import lru_cache, partial
from itertools import filterfalse
from os.path import join
import logging, re
logger = logging.getLogger(__name__)



def _getGenevaPortfolioData(dataGetterFunc, date, portfolio):
	"""
	[Function] ([String] date -> [Iterable] ([Dictionary]) positions),
	[String] date (yyyy-mm-dd), 
	[String] portfolio
		=> [List] ([Dictionary]) Positions from a Geneva report
	"""
	logger.debug('_getGenevaPortfolioData(): {0}, {1}'.format(date, portfolio))

	if portfolio == 'all':
		return list(dataGetterFunc(date))
	else:
		return compose(
			list
		  , partial(filter, lambda p: p['Portfolio'] == portfolio)
		  , dataGetterFunc
		)(date)



@lru_cache(maxsize=3)
def getFxTable(date):
	"""
	[String] date (yyyy-mm-dd)
		=> [List] ([Dictionary]) FX Entries

	Retrieve FX rate from tax lot report. Usually FX rates across
	different portfolios are the same, but there are occassions that
	they are different. So there is a checker for such inconsistency
	and give warnings in the log.
	"""
	def checkGroupConsistency(group):
		if not allEquals(map(lambda p: p['ExchangeRate'], group)):
			logger.warning('getFxTable(): inconsistency: {0}'.format(group))

		return group
	# End of checkGroupConsistency

	def checkInconsistency(positions):
		compose(
			partial(valmap, checkGroupConsistency)
		  , partial( groupbyToolz
		  		   , lambda p: (p['Date'], p['Currency'], p['TargetCurrency'])
		  		   )
		)(positions)
		return positions


	return compose(
		checkInconsistency
	  , list
	  , partial( map
			   , lambda p: { 'Date': p['PeriodEndDate']
			   			   , 'Portfolio': p['Portfolio']
			   			   , 'Currency': p['InvestID']
			   			   , 'TargetCurrency': p['BookCurrency']
			   			   , 'ExchangeRate': p['MarketPrice']
			   			   }
			   )
	  , partial(filterfalse, lambda p: p['MarketPrice'] == 'NA')
	  , partial(filterfalse, lambda p: p['BookCurrency'] == p['InvestID'])
	  , partial( filter
	  		   , lambda p: p['ThenByDescription'] == 'Cash and Equivalents'
	  		   )
	  , lambda date: getGenevaPositions(date, 'all')
	)(date)



def getSecurityIdAndType():
	"""
	[Dictionary] ([String] invest id -> [Dictionary] security properties)
	"""
	file = compose(
		lambda L: join(getDataDirectory(), L[0])
	  , _checkOnlyOne
	  , list
	  , partial( filter
	  		   , lambda fn: fn.lower().startswith('steven zhang security id and type report')
	  		   )
	  , getFiles
	  , getDataDirectory
	)()

	return compose(
		dict
	  , partial(map, lambda p: (p['Code'], p))
	  , _getGenevaSecurityIdAndTypeFromFile
	)(file)



def getPortfolioNames():
	"""
	[Dictionary] ([String] portfolio code => [String] portfolio name)
	"""
	file = compose(
		lambda L: join(getDataDirectory(), L[0])
	  , _checkOnlyOne
	  , list
	  , partial( filter
	  		   , lambda fn: fn.lower().startswith('steven zhang portfolio names')
	  		   )
	  , getFiles
	  , getDataDirectory
	)()

	return compose(
		dict
	  , partial(map, lambda p: (p['NameSort'], p['NameLine1']))
	  , _getGenevaPortfolioNamesFromFile
	)(file)



def _getEndDateFromFilename(fn):
	"""
	[String] file name (without path) => [String] date

	date is in the file name, with the form of yyyy-mm-dd

	If there are more than 1 dates, return the last date in the
	file name.
	"""
	m = re.findall('\d{4}-\d{2}-\d{2}', fn)
	if m:
		return m[-1]
	else:
		logger.error('_getEndDateFromFilename(): could not find date: {0}'.format(fn))
		raise ValueError



def _checkOnlyOne(L):
	""" [List] L => [List] L """
	if len(L) == 1:
		return L
	else:
		logger.error('_checkOnlyOne(): {0}'.format(len(L)))
		raise ValueError



def _getGenevaFileWithDate(func, date):
	"""
	[Function] ([String] -> [Bool]) file name pattern function,
	[String] date (yyyy-mm-dd)
		=> [String] file

	Using the file name pattern function to filter files from the
	data directory, then get the file with the correct end date.
	"""
	return compose(
		lambda L: join(getDataDirectory(), L[0])
	  , _checkOnlyOne
	  , list
	  , partial(filter, lambda fn: _getEndDateFromFilename(fn) == date)
	  , partial(filter, func)
	  , getFiles
	  , getDataDirectory
	)()



""" 
	[String] date => [String] tax lot file 
"""
_getGenevaTaxlotFile = partial(
	_getGenevaFileWithDate
  , lambda fn: fn.lower().startswith('all funds tax lot')
)



""" 
	[String] date => [String] dividend receivable payable file 
"""
_getGenevaDividendReceivableFile = partial(
	_getGenevaFileWithDate
  , lambda fn: fn.lower().startswith('all funds dividend receivable')
)



""" 
	[String] date => [String] cash ledger file 
"""
_getGenevaCashLedgerFile = partial(
	_getGenevaFileWithDate
  , lambda fn: fn.lower().startswith('all funds cash ledger')
)



@lru_cache(maxsize=3)
def _getGenevaPortfolioNamesFromFile(file):
	"""
	[String] file => [List] ([Dictionary]) positions
	"""
	def toString(x):
		return str(int(x)) if isinstance(x, float) else x


	def updatePortfolioName(p):
		return mergeDict(p, {'NameSort': toString(p['NameSort'])})


	logger.debug('_getGenevaPortfolioNamesFromFile(): {0}'.format(file))
	return compose(
		list
	  , partial(map, updatePortfolioName)
	  , getRawPositionsFromFile
	)(file)



@lru_cache(maxsize=3)
def _getGenevaSecurityIdAndTypeFromFile(file):
	"""
	[String] file => [List] ([Dictionary]) positions
	"""
	logger.debug('_getGenevaSecurityIdAndTypeFromFile(): {0}'.format(file))
	return list(getRawPositionsFromFile(file))



@lru_cache(maxsize=3)
def _getGenevaPositionsFromFile(date):
	"""
	[String] date (yyyy-mm-dd) => [List] ([Dictionary]) positions
	"""
	logger.debug('_getGenevaPositionsFromFile(): {0}'.format(date))
	return compose(
		list
	  , partial(readMultipartTaxlotReport, 'utf-16', '\t')
	  , _getGenevaTaxlotFile
	)(date)



@lru_cache(maxsize=3)
def _getGenevaDividendReceivableFromFile(date):
	"""
	[String] date (yyyy-mm-dd) => [List] ([Dictionary]) positions
	"""
	logger.debug('_getGenevaDividendReceivableFromFile(): {0}'.format(date))
	return compose(
		list
	  , partial(readMultipartDividendReceivableReport, 'utf-16', '\t')
	  , _getGenevaDividendReceivableFile
	)(date)



@lru_cache(maxsize=3)
def _getGenevaCashLedgerFromFile(date):
	"""
	[String] date (yyyy-mm-dd) => [List] ([Dictionary]) positions
	"""
	logger.debug('_getGenevaCashLedgerFromFile(): {0}'.format(date))
	return compose(
		list
	  , partial(readMultipartCashLedgerReport, 'utf-16', '\t')
	  , _getGenevaCashLedgerFile
	)(date)



"""
	[String] date (yyyy-mm-dd), [String] portfolio
		=> [List] ([Dictionary]) Geneva Positions (from tax lot)
"""
getGenevaPositions = partial(
	_getGenevaPortfolioData
  , _getGenevaPositionsFromFile
)



"""
	[String] date (yyyy-mm-dd), [String] portfolio
		=> [List] ([Dictionary]) Geneva Cash Ledger Positions
"""
getGenevaCashLedger = partial(
	_getGenevaPortfolioData
  , _getGenevaCashLedgerFromFile
)



"""
	[String] date (yyyy-mm-dd), [String] portfolio
		=> [List] ([Dictionary]) Geneva dividend receivable

	consolidate based on "investment description".
"""
getGenevaDividendReceivable = partial(
	_getGenevaPortfolioData
  , _getGenevaDividendReceivableFromFile
)