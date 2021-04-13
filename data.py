# coding=utf-8
#
# Handle data store operations.
# 
from factset.geneva_position import readMultipartTaxlotReport
from factset.utility import getDataDirectory
from steven_utils.file import getFiles
from toolz.functoolz import compose
from functools import lru_cache, partial
from os.path import join
import logging, re
logger = logging.getLogger(__name__)



def getGenevaPositions(date, portfolio):
	"""
	[String] date (yyyy-mm-dd), [String] portfolio
		=> [List] ([Dictionary]) Geneva Positions
	"""
	logger.debug('getGenevaPositions(): {0}, {1}'.format(date, portfolio))
	return compose(
		list
	  , partial(filter, lambda p: p['Portfolio'] == portfolio)
	  , _getGenevaPositionsFromFile
	)(date)



def getGenevaDividendReceivable(date, portfolio):
	"""
	[String] date (yyyy-mm-dd), [String] portfolio
		=> [Dictionary] ( [String] investment description
						  -> [Dictionary] receivable info
						)

	consolidate based on "investment description".
	"""
	return {}



def getSecurityIdAndType():
	"""
	[Dictionary] ([String] InvestID -> [Dictionary] properties) 
					Geneva security id and type mapping
	"""
	return {}



def getPortfolioName():
	"""
	[Dictionary] ([String] portfolio code => [String] portfolio name)
	"""
	return {}



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
