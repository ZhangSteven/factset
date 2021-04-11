# coding=utf-8
#
# Handles Geneva position data for FactSet upload.
# 
from geneva.report import groupMultipartReportLines, txtReportToLines \
						, readTxtReportFromLines, updatePositionWithFunctionMap
from steven_utils.utility import mergeDict
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
		datetime.strptime(s, '%m/%d/%Y').strftime('%Y-%m-%d')
	except:
		logger.debug('_updateDate strange date:{0}#'.format(s))
		return ''



def updateDateForFields(fields, p):
	"""
	[List] ([String]) fields, [Dictionary] p => [Dictionary] p
	"""
	return {key: _updateDate(p[key]) if key in fields else p[key] for key in p}



def updateNumberForFields(fields, p):
	"""
	[List] ([String]) fields, [Dictionary] p => [Dictionary] p
	"""
	return {key: _updateNumber(p[key]) if key in fields else p[key] for key in p}



def isDerivative(assetType):
	"""
	[String] Geneva asset type => [Bool] is it a derivative position
	"""
	return assetType in ( 'Equity Option', 'FX Forward', 'FX Future'
						, 'Index Future', 'Repurchase Agreement', 'Right')



def isCash(assetType):
	return assetType == 'Cash and Equivalents'



def consolidateTaxlotPositions(positions):
	"""
	[Iterable] positions => [Iterable] positions

	For some of the tax lot positions, we need to consolidate them
	into one.
	"""
	def notForConsolidate(position):
		return isCash(position['ThenByDescription']) or \
				isDerivative(position['ThenByDescription'])


	def consolidate(group):
		"""
		[List] group (positions) => [Dictionary] position
		"""
		def addUpField(field, positions):
			return sum(map(lambda p: p[field], positions))


		def updateFields(fields, positions):
			return {key: addUpField(key, positions) for key in fields}


		def getUnitCost(positions):
			quantity = addUpField('Quantity', positions)
			return positions[0]['UnitCost'] if quantity == 0 else \
					sum(map(lambda p: p['Quantity']*p['UnitCost'], positions))/quantity
		# End of getUnitCost()

		return \
		compose(
			lambda position: mergeDict(
				position
			  , {'UnitCost': getUnitCost(group)}
			)

		  , lambda position: mergeDict(
		  		position	
		  	  , updateFields( ( 'Quantity', 'CostBook', 'MarketValueBook'
		  		   			  , 'UnrealizedPriceGainLossBook', 'UnrealizedFXGainLossBook'
		  		   			  , 'AccruedAmortBook', 'AccruedInterestBook'
		  		   			  )
		  		   			, group
		  		   			)
		  	)

		  , lambda group: group[0]
		)(group)
	# End of consolidate()

	positions = list(positions)

	consolidatedPositions = \
	compose(
		lambda d: d.values()
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
		consolidateTaxlotPositions
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



def readMultipartTaxlotReport(encoding, delimiter, file):
	"""
	[String] encoding, [String] delimiter, [String] filename, 
		=> [Iterable] ([Dictionary] position)

	Read a multipart tax lot appraisal report (txt format), enrich it 
	with meta data, and return all positions.

	Some of the positions consolidated.
	"""
	return compose(
		chain.from_iterable
	  , partial(map, _readTaxlotReportFromLines)
	  , groupMultipartReportLines
	  , txtReportToLines
	)(encoding, delimiter, file)



def readMultipartCashLedgerReport(encoding, delimiter, file):
	"""
	[String] encoding, [String] delimiter, [String] filename
		=> [Iterable] ([Dictionary]) positions
	"""
	return compose(
		chain.from_iterable
	  , partial(map, _readCashLedgerReportFromLines)
	  , groupMultipartReportLines
	  , txtReportToLines
	)(encoding, delimiter, file)
