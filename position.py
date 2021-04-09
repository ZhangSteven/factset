# coding=utf-8
#
# Handles Geneva position data for FactSet upload.
# 
from geneva.report import groupMultipartReportLines, txtReportToLines \
						, readTxtReportFromLines, updatePositionWithFunctionMap
from steven_utils.utility import mergeDict, writeCsv, dictToValues
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



def updateNumber(s):
	"""
	[String] s => either a String or Float
	"""
	return 'NA' if s in ('', 'NA') else numberFromString(s)



def updateNumberForFields(fields, p):
	"""
	[List] ([String]) fields, [Dictionary] p => [Dictionary] p
	"""
	return \
	{key: updateNumber(p[key]) if key in fields else p[key] for key in p}



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
		return isCash(position['SortByDescription']) or \
				isDerivative(position['SortByDescription'])


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



def readTaxlotReportFromLines(lines):
	"""
	[Iterable] ([List]) lines => [Iterable] positions

	positions updated, meta data unchanged.
	"""
	def lognContinue(positions, metaData):
		logger.debug('readTaxlotReportFromLines(): Portfolio {0}'.format(
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



"""
	[String] encoding, [String] delimiter, [String] filename, 
		=> [Iterable] ([Dictionary] position)

	Read a multipart tax lot appraisal report (txt format), enrich it 
	with meta data, and return all positions.

	Some of the positions consolidated.
"""
readMultipartTaxlotReport = compose(
	chain.from_iterable
  , partial(map, readTaxlotReportFromLines)
  , groupMultipartReportLines
  , txtReportToLines
)



def getTaxlotCsvHeaders():
	return \
	( 'Portfolio', 'PeriodEndDate', 'KnowledgeDate', 'BookCurrency', 'InvestID'
	, 'SortByDescription', 'ThenByDescription', 'InvestmentDescription'
	, 'TaxLotDescription', 'TaxLotID', 'TaxLotDate', 'Quantity', 'OriginalFace'
	, 'UnitCost', 'MarketPrice', 'CostBook', 'MarketValueBook', 'UnrealizedPriceGainLossBook'
	, 'UnrealizedFXGainLossBook', 'AccruedAmortBook', 'AccruedInterestBook'
	# , 'ExtendedDescription', 'Description3'
	)



def processMultipartTaxlotReport(outputDir, file):
	"""
	[String] output directory,
	[String] multipart tax lot report (TXT) 
		=> [String] output csv

	Side effect: create a csv file in the output directory.
	"""
	def getDate(positions):
		"""
		[List] positions => [String] date
		"""
		if len(positions) == 0:
			logger.error('processMultipartTaxlotReport(): no positions')
			raise ValueError

		return positions[0]['PeriodEndDate']
	# End of getDate()


	def getOutputFilename(positions):
		"""
		[List] positions => [String] date
		"""
		return join(outputDir, 'taxlot_positions_' + getDate(positions) + \
					'_' + datetime.now().strftime('%Y%m%d%H%M%S') + '.csv')
	# End of getOutputFilename()


	logger.debug('processMultipartTaxlotReport(): {0}'.format(file))

	positions = list(readMultipartTaxlotReport('utf-16', '\t', file))
	
	return \
	compose(
		partial(writeCsv, getOutputFilename(positions))
	  , partial(chain, [getTaxlotCsvHeaders()])
	  , partial(map, partial(dictToValues, getTaxlotCsvHeaders()))
	)(positions)




if __name__ == "__main__":
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)
	
	import argparse
	parser = argparse.ArgumentParser(description='handle fact positions')
	parser.add_argument('file', metavar='file', type=str, help="input file")

	logger.debug('main(): start')
	print(processMultipartTaxlotReport('', parser.parse_args().file))