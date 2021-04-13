# coding=utf-8
#
# Handle data store operations.
# 
from os.path import join
import logging
logger = logging.getLogger(__name__)



def getGenevaPositions(date, portfolio):
	"""
	[String] date (yyyy-mm-dd), [String] portfolio
		=> [List] ([Dictionary]) Geneva Positions
	"""
	return []



def getSecurityIdAndType():
	"""
	[Dictionary] Geneva security id and type mapping
	"""
	return {}



def getPortfolioName():
	"""
	[Dictionary] ([String] portfolio code => [String] portfolio name)
	"""
	return {}




if __name__ == "__main__":
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)
	
	import argparse
	parser = argparse.ArgumentParser(description='handle fact positions')
	parser.add_argument('file', metavar='file', type=str, help="input file")

	logger.debug('main(): start')
	print(processMultipartTaxlotReport('', parser.parse_args().file))
	# print(processMultipartCashLedgerReport('', parser.parse_args().file))