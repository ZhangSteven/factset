# coding=utf-8
#
# For API design only
# 

"""
This part is for Yu Dan.
"""
def getFactsetPositions(date, portfolio):
	"""
	[String] date (yyyy-mm-dd),
	[String] portfolio id
		=> [Iterable] ([Dictionary] fact position)
	"""
	return []



def getFactsetTransactions(date, portfolio):
	"""
	[String] date (yyyy-mm-dd),
	[String] portfolio id
		=> [Iterable] ([Dictionary] fact transaction)
	"""
	return []



def getFactsetSecurityInfo(date, portfolio):
	"""
	[String] date (yyyy-mm-dd),
	[String] portfolio id
		=> [Iterable] ([String] security type, [Dictionary] security info)
	"""
	return []



"""
This part the API from the database module
"""
def getPortfolioDescription(portfolio):
	"""
	[String] portfolio id => [String] portfolio description
	"""
	return ''



def getSedolFromGenevaId(gid):
	"""
	[String] geneva investment id => [String] SEDOL code

	The database may not contain SEDOL code for investments other than the
	equity type. So make sure the investment is equity type before calling 
	this function.
	"""
	return ''



def getLocalCurrencyFromGenevaId(gid):
	"""
	[String] geneva investment id => [String] local currency of the investment
	"""
	return ''



def getFuturesInfoFromGenevaId(gid):
	"""
	[String] geneva investment id 
		=> ([String] underlying security id, [Float] contract size) 
	"""
	return ('', 0.0)



"""
This part the API from the Geneva data module
"""
def getGenevaPositions(date, portfolio):
	"""
	[String] date (yyyy-mm-dd),
	[String] portfolio id
		=> [List] ([Dictionary] fact position)

	This function will check the data before returning them. The list is 
	always non-empty.
	"""
	return []



def getGenevaDividendReceivable(date, portfolio):
	"""
	[String] date (yyyy-mm-dd),
	[String] portfolio id
		=> [List] ([Dictionary] dividend receivable position)
	"""
	return []



def getGenevaFX(date, portfolio, currency, targetCurrency):
	"""
	[String] date (yyyy-mm-dd),
	[String] portfolio id
	[String] currency,
	[String] target currency
		=> [Float] exchange rate

	The function returns the exchange rate of converting one unit of 'currency'
	to 'target currency'.

	For example, if currency == USD, target currency == HKD, then exchange rate
	is some number near 7.8.
	"""
	return 1.0