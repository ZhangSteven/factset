# coding=utf-8
#
# Handles Geneva position data for FactSet upload.
# 
from factset.data import getGenevaPositions, getSecurityIdAndType \
						, getPortfolioNames, getGenevaDividendReceivable \
						, getFxTable
from steven_utils.utility import mergeDict
from steven_utils.iter import firstOf
from toolz.functoolz import compose
from functools import partial
from itertools import filterfalse
from os.path import join
import logging
logger = logging.getLogger(__name__)



def _getInvestId(position):
	"""
	[Dictionary] geneva position => [String] portfolio code
	"""
	return position['InvestID']



def _getPortfolioCode(position):
	"""
	[Dictionary] geneva position => [String] portfolio code
	"""
	return position['Portfolio']



def _getPortfolioDescription(position):
	"""
	[Dictionary] geneva position => [String] portfolio name
	"""
	return getPortfolioNames()[_getPortfolioCode(position)]



def _getPositionDate(position):
	"""
	[Dictionary] geneva position => [String] date (yyyy-mm-dd)
	"""
	return position['PeriodEndDate']



def _getQuantity(position):
	"""
	[Dictionary] geneva position => [Float] quantity
	"""
	return position['Quantity']



def _getUnitCost(position):
	"""
	[Dictionary] geneva position => [Float] quantity
	"""
	return position['UnitCost']



def _getGenevaInvestmentType(position):
	"""
	[Dictionary] geneva position => [String] Geneva Investment Type
	"""
	return getSecurityIdAndType()[_getInvestId(position)]['InvestmentType Description']



def _getCashSymbol(position):
	"""
	[Dictionary] geneva position => [String] symbol
	"""
	_, assetClass = _getAssetClassAndType(position)
	if assetClass == 'Zero Interest Cash':
		return 'CASH_ZERO_' + _getInvestId(position)
	else:
		logger.error('_getCashSymbol(): {0} not supported'.format(assetType))
		raise ValueError



def _getEquitySymbol(position):
	"""
	[Dictionary] geneva position => [String] symbol
	"""
	return getSecurityIdAndType()[_getInvestId(position)]['SEDOL']



def _getSecuritySymbol(position):
	"""
	[Dictionary] geneva position => [String] factset security symbol
	"""
	assetClass, assetType = _getAssetClassAndType(position)
	if assetClass == 'Cash':
		return _getCashSymbol(position)
	elif assetClass == 'Equity':
		return _getEquitySymbol(position)
	else:
		logger.error('_getSecuritySymbol(): {0}, {1} not supported'.format(
					assetClass, assetType))
		raise ValueError



def _getSecurityName(position):
	"""
	[Dictionary] geneva position => [String] security name
	"""
	return position['TaxLotDescription']



def _getAssetClassAndType(position):
	"""
	[Dictionary] geneva position
		=> ([String] asset class, [String] asset type)
	"""
	gType = _getGenevaInvestmentType(position)
	if gType == 'Cash and Equivalents':
		return ('Cash', 'Zero Interest Cash')
	elif gType == 'American Depository Receipt':
		return ('Equity', 'ADR')
	elif gType in ('Common Stock', 'Stapled Security'):
		return ('Equity', 'Equity Common')
	elif gType == 'Preferred Stock':
		return ('Equity', 'Preferred')
	elif gType == 'Closed End Fund':
		return ('Funds', 'Close Ended Fund')
	elif gType == 'Open-End Fund':
		return ('Funds', 'Mutual Fund')
	elif gType == 'Exchange Trade Fund':
		return ('Funds', 'Exchange Traded Fund')
	elif gType == 'Real Estate Investment Trust':
		return ('Funds', 'REIT')
	else:
		logger.error('_getAssetClassAndType(): {0} not supported'.format(
					gType))
		raise ValueError



def _getMarketPrice(position):
	"""
	[Dictionary] geneva position 
		=> [Float] price, or [String] 'NA'
	"""
	assetClass, assetType = _getAssetClassAndType(position)
	if assetClass == 'Cash':
		return 1.0

	return position['MarketPrice']



def _getLocalCurrency(position):
	"""
	[Dictionary] geneva position => [String] local currency
	"""
	return getSecurityIdAndType()[_getInvestId(position)]['BifurcationCurrency Code']



def _getPerShareAccruedInterest(position):
	"""
	[Dictionary] geneva position => [Float] accrued interest per share
	"""
	if position['AccruedInterestBook'] == 0:
		return 0
	else:
		logger.error('_getPerShareAccruedInterest(): not supported')
		raise ValueError



def _getPerSharePrincipal(position):
	"""
	[Dictionary] geneva position => [Float] principal return per share
	"""
	assetClass, assetType = _getAssetClassAndType(position)
	if assetClass in ('Cash', 'Equity', 'Fund'):
		return 0
	else:
		logger.error('_getPerSharePrincipal(): not supported')
		raise ValueError



def _amountInLocalCurrency(amoutWithCurrency, position):
	"""
	([String] currency, [Float] amount), [Dictionary] position
		=> [Float] amount
	"""
	currency, amount = amoutWithCurrency
	return amount * _getFxRate( _getPositionDate(position), _getPortfolioCode(position)
							  , currency, _getLocalCurrency(position))



def _getPerShareDividend(dividendReceivable, position):
	"""
	[Dictionary] ([String] portfolio, [String] investment) -> [Dictionary] dividend entry
	[Dictionary] geneva position
		=> [Float] dividend receivable for the position
	"""
	try:
		dvdReceivable = dividendReceivable[(_getPortfolioCode(position), _getSecurityName(position))]
	except KeyError:
		return 0

	fx = _getFxRate( _getPositionDate(position), _getPortfolioCode(position)
				   , dvdReceivable['LocalCurrency'], _getLocalCurrency(position))
	perShareDvd = dvdReceivable['LocalPerShareAmount'] \
					if isinstance(dvdReceivable['LocalPerShareAmount'], float) \
					else dvdReceivable['LocalGrossDividendRecPay']/_getQuantity(position)

	return perShareDvd * fx



def _getPerShareIncome(dividendReceivable, position):
	"""
	[Dictionary] geneva position => [Float] income per share
	"""
	return _getPerShareDividend(dividendReceivable, position)



def _getTotalCost(position):
	"""
	[Dictionary] geneva position => [Float] total cost
	"""
	assetClass, assetType = _getAssetClassAndType(position)
	if assetClass == 'Equity':
		return _getQuantity(position) * _getUnitCost(position)
	elif (assetClass, assetType) == ('Cash', 'Zero Interest Cash'):
		return _getQuantity(position)
	else:
		logger.error('_getEndingMarketValue(): not implemented')
		raise ValueError



def _getEndingMarketValue(position):
	"""
	[Dictionary] geneva position => [Float] ending market value
	"""
	assetClass, assetType = _getAssetClassAndType(position)
	if assetClass == 'Cash':
		return _getQuantity(position)
	
	if _getMarketPrice(position) == 'NA':
		return 'NA'

	if assetClass in ('Equity', 'Fund'):
		return _getQuantity(position) * _getMarketPrice(position)
	else:
		logger.error('_getEndingMarketValue(): not supported')
		raise ValueError



def _getStrategy(position):
	"""
	[Dictionary] geneva position => [String] stragegy (HTM, AFS)
	"""
	assetClass, assetType = _getAssetClassAndType(position)
	if assetClass == 'Cash':
		return ''

	if assetClass in ('Equity', 'Fund'):
		return 'AFS'
	else:
		logger.error('_getStrategy(): not supported')
		raise ValueError



def _getContractSize(position):
	"""
	[Dictionary] geneva position => [Float] futures contract size
	"""
	assetClass, assetType = _getAssetClassAndType(position)

	if assetClass in ('Cash', 'Equity', 'Fund'):
		return 'NA'
	else:
		logger.error('_getContractSize(): not supported')
		raise ValueError



def _getUnderlyingId(position):
	"""
	[Dictionary] geneva position
		=> [String] futures underlying security
	"""
	assetClass, assetType = _getAssetClassAndType(position)

	if assetClass in ('Cash', 'Equity', 'Fund'):
		return ''
	else:
		logger.error('_getUnderlyingId(): not supported')
		raise ValueError



def _getAverageCumulativeCost(position):
	assetClass, assetType = _getAssetClassAndType(position)

	if assetClass == 'Cash':
		return 1.0
	elif assetClass == 'Equity':
		return _getUnitCost(position)
	else:
		logger.error('_getUnderlyingId(): not supported')
		raise ValueError



def _changeDateFormat(dt):
	"""
	[String] dt (yyyy-mm-dd) => [String] yyyymmdd
	"""
	return ''.join(dt.split('-'))



def _getFxRate(date, portfolio, currency, targetCurrency):
	"""
	[String] date (yyyy-mm-dd),
	[String] portfolio,
	[String] currency,
	[String] target currency
		=> [Float] FX rate

	returns how many units of target currency is equal to one unit
	of currency. For example:

	_getFxRate('2021-03-31', '12307', 'USD', 'HKD') -> 7.7741
	"""
	if currency == targetCurrency:
		return 1.0

	fxPositions = getFxTable(date)
	p = firstOf( lambda p: all(( date == p['Date']
							   , portfolio == p['Portfolio']
							   , currency == p['Currency']
							   , targetCurrency == p['TargetCurrency']
							   ))
			   , fxPositions
			   )

	if p != None:
		return p['ExchangeRate']

	p = firstOf( lambda p: all(( date == p['Date']
							   , portfolio == p['Portfolio']
							   , targetCurrency == p['Currency']
							   , currency == p['TargetCurrency']
							   ))
			   , fxPositions
			   )

	if p != None:
		return 1.0/p['ExchangeRate']

	logger.debug('FX not found for portfolio {0}, {1}->{2}, try other portfolio'.format(
				portfolio, currency, targetCurrency))

	p = firstOf( lambda p: all(( date == p['Date']
							   , currency == p['Currency']
							   , targetCurrency == p['TargetCurrency']
							   ))
			   , fxPositions
			   )

	if p != None:
		return p['ExchangeRate']

	p = firstOf( lambda p: all(( date == p['Date']
							   , targetCurrency == p['Currency']
							   , currency == p['TargetCurrency']
							   ))
			   , fxPositions
			   )

	if p != None:
		return 1.0/p['ExchangeRate']

	logger.error('FX not found for {1}->{2}'.format(currency, targetCurrency))
	raise ValueError



def _factsetPosition(dividendReceivable, position):
	"""
	[Dictionary] dividend receivable,
	[Dictionary] position 
		=> [Dictionary] factset position
	"""
	logger.debug('_factsetPosition(): {0}, {1}'.format(
				_getPortfolioCode(position), _getInvestId(position)))

	assetClass, assetType = _getAssetClassAndType(position)

	return \
	{ 'Portfolio Name': _getPortfolioCode(position)
	, 'Portfolio Description': _getPortfolioDescription(position)
	, 'Date': _changeDateFormat(_getPositionDate(position))
	, 'Symbol': _getSecuritySymbol(position)
	, 'Security Name': _getSecurityName(position)
	, 'Asset Class': assetClass
	, 'Asset Type': assetType
	, 'Shares': _getQuantity(position)
	, 'Price': _getMarketPrice(position)
	, 'Price ISO': _getLocalCurrency(position)
	, 'Per Share Accrued Interest': _getPerShareAccruedInterest(position)
	, 'Per Share Principal': _getPerSharePrincipal(position)
	, 'Per Share Income': _getPerShareIncome(dividendReceivable, position)
	, 'Total Cost': _getTotalCost(position)
	, 'Contract Size': _getContractSize(position)
	, 'Underlying ID': _getUnderlyingId(position)
	, 'Ending Market Value': _getEndingMarketValue(position)
	, 'Strategy': _getStrategy(position)
	, 'Average Cumulative Cost': _getAverageCumulativeCost(position)
	}



def getPositions(date, portfolio):
	"""
	[String] date (yyyy-mm-dd), [String] portfolio
		=> [Iterable] ([Dictionary]) factset positions

	Note: portfolio cannot be 'all', must be a portfolio code.
	"""
	logger.debug('getPositions(): date={0}, portfolio={1}'.format(date, portfolio))
	
	dividendReceivable = compose(
		dict
	  , partial(map, lambda p: ((p['Portfolio'], p['Investment']), p))
	  , partial(filter, lambda p: date == p['EXDate'])
	  , getGenevaDividendReceivable
	)(date, portfolio)

	return compose(
		partial(map, partial(_factsetPosition, dividendReceivable))
	  , getGenevaPositions
	)(date, portfolio)
