# coding=utf-8
#
# Handles Geneva position data for FactSet upload.
# 
from os.path import join
import logging, re
logger = logging.getLogger(__name__)



def getFactsetPosition(date, portfolio):
	"""
	[String] date (yyyy-mm-dd), [String] portfolio
		=> [Iterable] ([Dictionary]) factset positions
	"""
	positions = getGenevaPosition(date, portfolio)
	securityIdType = getSecurityIdType()
	portfolioName = getPortfolioName()
	

	return []



if __name__ == "__main__":
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	logger.debug('main(): start')
