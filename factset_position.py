# coding=utf-8
#
# Handles Geneva position data for FactSet upload.
# 
from factset.data import getGenevaPositions, getSecurityIdAndType \
						, getPortfolioNames
from os.path import join
import logging, re
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



def _getGenevaAssetType(position):
	"""
	[Dictionary] geneva position => [String] Geneva Asset Type
	"""
	return getSecurityIdAndType()[_getInvestId(position)]['AssetType Description']



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



def _getExchangeLocation(position):
	"""
	[Dictionary] geneva position => [String] equity exchange location
	"""
	equitySuffix = investId.split()[-1]

	if equitySuffix in ('C1', 'C2', 'CH'):
		return 'CN'
	elif equitySuffix in ('HK', 'US'):
		return equitySuffix
	elif equitySuffix == 'SP':
		return 'SG'
	else:
		logger.error('_getExchangeLocation(): {0} not supported'.format(
					_getInvestId(position)))
		raise ValueError



def _getEquitySymbol(position):
	"""
	[Dictionary] geneva position => [String] symbol
	"""
	isin = getSecurityIdAndType()[_getInvestId(position)]['Isin']
	if isin == '':
		logger.error('_getEquitySymbol(): {0}: empty ISIN code'.format(
					_getInvestId(position)))
		raise ValueError

	return isin + '-' + _getExchangeLocation(position)



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
	return getSecurityIdAndType()[_getInvestId(position)]['Description']



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
	return ''



def _getLocalCurrency(position):
	"""
	[Dictionary] geneva position => [String] local currency
	"""
	return ''



def _getPerShareAccruedInterest(position):
	"""
	[Dictionary] geneva position => [Float] accrued interest per share
	"""
	return 0



def _getPerSharePrincipal(position):
	"""
	[Dictionary] geneva position => [Float] principal return per share
	"""
	return 0



def _getPerShareIncome(position):
	"""
	[Dictionary] geneva position => [Float] income per share
	"""
	return 0



def _getTotalCost(position):
	"""
	[Dictionary] geneva position => [Float] total cost
	"""
	return 0



def _getEndingMarketValue(position):
	"""
	[Dictionary] geneva position => [Float] ending market value
	"""
	return 0



def _getStrategy(position):
	"""
	[Dictionary] geneva position => [String] stragegy (HTM, AFS)
	"""
	return ''



def _getContractSize(position):
	"""
	[Dictionary] geneva position => [Float] futures contract size
	"""
	return 'NA'



def _getUnderlyingId(position):
	"""
	[Dictionary] geneva position
		=> [String] futures underlying security
	"""
	return ''



def _changeDateFormat(dt):
	"""
	[String] dt (yyyy-mm-dd) => [String] yyyymmdd
	"""
	return ''.join(dt.split('-'))



def _factsetPosition(position):
	"""
	[Dictionary] position => [Dictionary] factset position
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
	, 'Ending Market Value': _getEndingMarketValue(position)
	, 'Per Share Income': _getPerShareIncome(position)
	}



def getPositions(date, portfolio):
	"""
	[String] date (yyyy-mm-dd), [String] portfolio
		=> [Iterable] ([Dictionary]) factset positions
	"""
	logger.debug('getPositions(): date={0}, portfolio={1}'.format(date, portfolio))
	return map(_factsetPosition, getGenevaPositions(date, portfolio))




if __name__ == "__main__":
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	logger.debug('main(): start')
