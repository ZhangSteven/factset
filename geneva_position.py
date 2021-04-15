# coding=utf-8
#
# Provide methods to read Geneva data.
# 
from geneva.report import groupMultipartReportLines, txtReportToLines \
						, readTxtReportFromLines, updatePositionWithFunctionMap
from steven_utils.utility import mergeDict, allEquals
from toolz.functoolz import compose
from toolz.itertoolz import groupby as groupbyToolz
from toolz.dicttoolz import valmap
from functools import partial
from itertools import chain, filterfalse
from datetime import datetime
from os.path import join
import logging, re
logger = logging.getLogger(__name__)



def numberFromString(s):
	"""
	[String] s => [Float] x
	
	The number string can be like: 2.85
	Or, it can be like: "-14,854,500.47", with double quotes and comma
	"""
	return float(s[1:-1].replace(',', '')) \
	if len(s) > 2 and s[0] == '"' and s[-1] == '"' else float(s)



def _updateNumber(s):
	"""
	[String] s => either a String or Float
	"""
	return 'NA' if s in ('', 'NA') else numberFromString(s)



def _updateDate(s):
	"""
	[String] s (date, mm/dd/yyyy) => [String] s (yyyy-mm-dd)
	"""
	try:
		return datetime.strptime(s, '%m/%d/%Y').strftime('%Y-%m-%d')
	except:
		logger.debug('_updateDate strange date:{0}#'.format(s))
		return ''



def _updatePercentage(s):
	"""
	[String] s (that ends with %) => [Float] or [String] s
	"""
	return float(s[:-1]) if s[-1] == '%' else s



def _updateFieldsWithFunction(func, fields, p):
	"""
	[Func] function, [List] ([String]) fields, [Dictionary] p 
		=> [Dictionary] p
	"""
	return {key: func(p[key]) if key in fields else p[key] for key in p}



updateDateForFields = partial(
	_updateFieldsWithFunction
  , _updateDate
)


updateNumberForFields = partial(
	_updateFieldsWithFunction
  , _updateNumber
)


updatePercentageForFields = partial(
	_updateFieldsWithFunction
  , _updatePercentage
)



def _isOTCType(assetType):
	"""
	[String] Geneva asset type => [Bool] is it a derivative position
	"""
	return assetType in ( 'Equity Option', 'FX Forward', 'FX Future'
						, 'Index Future', 'Repurchase Agreement', 'Right')



def _isCash(assetType):
	return assetType == 'Cash and Equivalents'



def _addUpField(field, positions):
	return sum(map(lambda p: p[field], positions))



def _updateFields(fields, positions):
	return {key: _addUpField(key, positions) for key in fields}



def _consolidateTaxlotPositions(positions):
	"""
	[Iterable] positions => [Iterable] positions

	For some of the tax lot positions, we need to consolidate them
	into one.
	"""
	def notForConsolidate(position):
		return _isOTCType(position['ThenByDescription'])


	def getUnitCost(positions):
		quantity = _addUpField('Quantity', positions)
		return positions[0]['UnitCost'] if quantity == 0 else \
				sum(map(lambda p: p['Quantity']*p['UnitCost'], positions))/quantity


	def consolidate(group):
		"""
		[List] group (positions) => [Dictionary] position
		"""
		return \
		compose(
			lambda position: mergeDict(
		  		position
		  	  , _updateFields( ( 'Quantity', 'CostBook', 'MarketValueBook'
		  		   			   , 'UnrealizedPriceGainLossBook', 'UnrealizedFXGainLossBook'
		  		   			   , 'AccruedAmortBook', 'AccruedInterestBook'
		  		   			   )
		  		   			 , group
		  		   			 )
		  	)

		  , lambda group: mergeDict(
		  		group[0]
		  	  , {'UnitCost': getUnitCost(group)}
		  	)
		)(group)
	# End of consolidate()


	def updateCashDescription(p):
		return mergeDict(p, {'TaxLotDescription': p['InvestID'] + ' ' + p['Portfolio']}) \
				if _isCash(p['ThenByDescription']) else p
	# End of updateCashDescription()

	positions = list(positions)

	consolidatedPositions = \
	compose(
		partial(map, updateCashDescription) 
	  , lambda d: d.values()
	  , partial(valmap, consolidate)
	  , partial(groupbyToolz, lambda p: p['InvestID'])
	  , partial(filterfalse, notForConsolidate)
	)(positions)

	return chain( filter(notForConsolidate, positions)
				, consolidatedPositions)



def _readTaxlotReportFromLines(lines):
	"""
	[Iterable] ([List]) lines => [Iterable] positions

	positions updated, meta data unchanged.
	"""
	def lognContinue(positions, metaData):
		logger.debug('_readTaxlotReportFromLines(): Portfolio {0}'.format(
						metaData['Portfolio']))
		return positions, metaData


	def addMetaDataToPosition(positions, metaData):
		"""
		[Iterable] positions, [Dictionary] metaData
			=> [Iterable] positions
		"""
		data = { 'Portfolio': metaData['Portfolio']
			   , 'PeriodEndDate': metaData['PeriodEndDate']
			   , 'KnowledgeDate': metaData['KnowledgeDate']
			   , 'BookCurrency' : metaData['BookCurrency']
			   }

		return map(lambda p: mergeDict(p, data), positions)
	# End of addMetaDataToPosition()


	def addInvestId(position):
		"""
		[Dictionary] position => [Dictionary] position

		Add the field 'InvestID' to the position
		"""
		m = re.search('\((.*)\)', position['InvestmentDescription'])

		return \
		mergeDict( position
				 , {'InvestID': m.group(1) if m != None else position['InvestmentDescription']}
				 )
	# End of addInvestId()


	return \
	compose(
		_consolidateTaxlotPositions
	  , partial(map, addInvestId)
	  , partial( map
			   , partial( updateNumberForFields
			   			, ( 'Quantity', 'OriginalFace', 'UnitCost', 'MarketPrice'
			   			  , 'CostBook', 'MarketValueBook', 'UnrealizedPriceGainLossBook'
			   			  , 'UnrealizedFXGainLossBook', 'AccruedAmortBook', 'AccruedInterestBook'
			   			  )
						)
			   )
	  , lambda t: addMetaDataToPosition(t[0], t[1])
	  , lambda t: lognContinue(t[0], t[1])
	  , readTxtReportFromLines
	)(lines)



def _readCashLedgerReportFromLines(lines):
	"""
	[Iterable] ([List]) lines => [Iterable] ([Dictionary]) positions
	"""
	def lognContinue(positions, metaData):
		logger.debug('_readCashLedgerReportFromLines(): Portfolio {0}'.format(
						metaData.get('Portfolio', '')))
		return positions, metaData


	def addMetaDataToPosition(positions, metaData):
		"""
		[Iterable] positions, [Dictionary] metaData
			=> [Iterable] positions
		"""
		data = { 'Portfolio': metaData.get('Portfolio', '')
			   , 'PeriodStartDate': metaData.get('PeriodStartDate', '')
			   , 'PeriodEndDate': metaData.get('PeriodEndDate', '')
			   , 'KnowledgeDate': metaData.get('KnowledgeDate', '')
			   , 'BookCurrency' : metaData.get('BookCurrency', '')
			   }

		return map(lambda p: mergeDict(p, data), positions)
	# End of addMetaDataToPosition()


	return \
	compose(
		partial( map
			   , partial(updateDateForFields, ('CashDate', 'TradeDate', 'SettleDate'))
			   )
	  , partial( map
			   , partial( updateNumberForFields
			   			, ( 'CurrBegBalLocal', 'CurrBegBalBook', 'GroupWithinCurrencyBegBalLoc'
			   			  , 'GroupWithinCurrencyBegBalBook', 'Quantity', 'Price', 'LocalAmount'
			   			  , 'LocalBalance', 'BookAmount', 'BookBalance', 'GroupWithinCurrencyClosingBalLoc'
			   			  , 'GroupWithinCurrencyClosingBalBook', 'CurrClosingBalLocal', 'CurrClosingBalBook'
			   			  )
						)
			   )
	  , lambda t: addMetaDataToPosition(t[0], t[1])
	  , lambda t: lognContinue(t[0], t[1])
	  , readTxtReportFromLines
	)(lines)



# def _consolidateDividendReceivable(positions):
# 	"""
# 	[Iterable] ([Dictionary]) positions => [Iterable] positions

# 	Consolidate positions of the same security into one.
# 	"""
# 	def checkConsistency(group):
# 		logger.debug('_consolidateDividendReceivable(): {0}'.format(group[0]['Investment']))
# 		if allEquals(map(lambda p: (p['LocalCurrency'], p['LocalPerShareAmount']), group)):
# 			return group
# 		else:
# 			logger.error('_consolidateDividendReceivable(): inconsistency: {0}'.format(group))
# 			raise ValueError


# 	def consolidate(group):
# 		return mergeDict(
# 			group[0]
# 		  , _updateFields( ( 'ExDateQuantity', 'LocalGrossDividendRecPay'
# 		  				   , 'LocalWHTaxPayable', 'LocalNetDividendRecPay'
# 		  				   , 'BookGrossDividendRecPay', 'BookWHTaxPayable'
# 		  				   , 'BookNetDividendRecPay', 'UnrealizedFXGainLoss'
# 		  				   , 'LocalReclaimReceivable', 'BookReclaimReceivable'
# 		  				   , 'LocalReliefReceivable', 'BookReliefReceivable'
# 		  				   )
# 		  				 , group
# 		  				 )
# 		)
# 	# End of consolidate()

# 	return compose(
# 		lambda d: d.values()
# 	  , partial(valmap, consolidate)
# 	  , partial(valmap, checkConsistency)
# 	  , partial(groupbyToolz, lambda p: p['Investment'])
# 	)(positions)



def _readDividendReceivableReportFromLines(lines):
	"""
	[Iterable] ([List]) lines => [Iterable] ([Dictionary]) positions
	"""
	def lognContinue(positions, metaData):
		logger.debug('_readDividendReceivableReportFromLines(): Portfolio {0}'.format(
						metaData.get('Portfolio', '')))
		return positions, metaData


	def addMetaDataToPosition(positions, metaData):
		"""
		[Iterable] positions, [Dictionary] metaData
			=> [Iterable] positions
		"""
		data = { 'Portfolio': metaData.get('Portfolio', '')
			   , 'PeriodEndDate': metaData.get('PeriodEndDate', '')
			   , 'KnowledgeDate': metaData.get('KnowledgeDate', '')
			   , 'BookCurrency' : metaData.get('BookCurrency', '')
			   }

		return map(lambda p: mergeDict(p, data), positions)
	# End of addMetaDataToPosition()

	def checkGroupConsistency(group):
		if not allEquals(map(lambda p: (p['LocalCurrency'], p['LocalPerShareAmount']), group)):
			logger.error('_readDividendReceivableReportFromLines(): inconsistency: {0}'.format(
						group))
			raise ValueError

		return group
	# End of checkGroupConsistency()

	def checkConsistency(positions):
		compose(
			partial(valmap, checkGroupConsistency)
		  , partial( groupbyToolz
		  		   , lambda p: (p['Portfolio'], p['PeriodEndDate'], p['Investment'])
		  		   )
		)(positions)

		return positions
	# End of checkConsistency()


	return \
	compose(
		checkConsistency
	  , list
	  , partial(map, partial(updateDateForFields, ('EXDate', 'PayDate')))
	  , partial(map, partial(updatePercentageForFields, ('WHTaxRate', )))
	  , partial( map
			   , partial( updateNumberForFields
			   			, ( 'ExDateQuantity', 'LocalGrossDividendRecPay', 'LocalWHTaxPayable'
			   			  , 'LocalNetDividendRecPay', 'BookGrossDividendRecPay', 'BookWHTaxPayable'
			   			  , 'BookNetDividendRecPay', 'UnrealizedFXGainLoss', 'LocalPerShareAmount'
			   			  , 'LocalReclaimReceivable', 'BookReclaimReceivable', 'LocalReliefReceivable'
			   			  , 'BookReliefReceivable'
						  )
						)
			   )
	  , lambda t: addMetaDataToPosition(t[0], t[1])
	  , lambda t: lognContinue(t[0], t[1])
	  , readTxtReportFromLines
	)(lines)



def _readMultipartReport(mappingFunc, encoding, delimiter, file):
	"""
	[Func] ([Iterable] ([List]) lines => [Iterable] ([Dictionary] positions)),
	[String] encoding, 
	[String] delimiter, 
	[String] filename 
		=> [Iterable] ([Dictionary] position)

	Read a multipart report (txt format), enrich it with meta data, 
	and return all positions.
	"""
	return compose(
		chain.from_iterable
	  , partial(map, mappingFunc)
	  , groupMultipartReportLines
	  , txtReportToLines
	)(encoding, delimiter, file)



"""
	[String] encoding, [String] delimiter, [String] filename, 
		=> [Iterable] ([Dictionary] position)

	Read a multipart tax lot appraisal report (txt format), enrich it 
	with meta data, and return all positions.

	Some of the positions consolidated.
"""
readMultipartTaxlotReport = partial(
	_readMultipartReport
  , _readTaxlotReportFromLines
)



"""
	[String] encoding, [String] delimiter, [String] filename, 
		=> [Iterable] ([Dictionary] position)

	Read a multipart cash ledger report (txt format), enrich it 
	with meta data, and return all positions.
"""
readMultipartCashLedgerReport = partial(
	_readMultipartReport
  , _readCashLedgerReportFromLines
)



"""
	[String] encoding, [String] delimiter, [String] filename, 
		=> [Iterable] ([Dictionary] position)

	Read a multipart dividend receivable report (txt format), enrich it 
	with meta data, and return all positions.
"""
readMultipartDividendReceivableReport = partial(
	_readMultipartReport
  , _readDividendReceivableReportFromLines
)
