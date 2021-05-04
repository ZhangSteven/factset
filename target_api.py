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
Database API
"""
def get_security_basic_info(gid):
	"""
	[String] gid => [Dictonary] basic information, including Geneva
	investment Id, Ticker, Geneva asset type and investment type, etc.

	If not found, raise Error: security info not found
	"""
	return {}



def add_security_basic_info(info):
	"""
	[Dictonary] basic information, including Geneva	investment Id, 
	Ticker, Geneva asset type and investment type, etc.

	If security info already there, raise Error: 
	security info exists

	Otherwise, add the security basic info.
	"""
	pass



def update_security_basic_info(info):
	"""
	[Dictonary] basic information, including Geneva	investment Id, 
	Ticker, Geneva asset type and investment type, etc.

	If not found, raise Error: security info not found
	Otherwise, update the security basic info.
	"""
	pass



def get_fixed_deposit_info(gid):
	"""
	[String] gid => [Dictonary] factset security id, starting date,
	maturity date, etc.

	If not found, raise Error: security info not found
	"""
	return {}



def add_fixed_deposit_info(info):
	"""
	[Dictionary] fixed deposit information

	If security info already there, raise Error: security info exists

	Otherwise, add the fixed deposit info.
	"""
	pass



def update_fixed_deposit_info(info):
	"""
	[Dictionary] fixed deposit information

	If not found, raise Error: security info not found
	Otherwise, update the fixed deposit info.
	"""
	pass



def get_fx_forward_info(fx_name):
	"""
	[String] Geneva FX Forward name 
		=> [Dictonary] factset security id, starting date, 
						maturity date, base/term currency, etc.

	If not found, raise Error: security info not found
	"""
	return {}



def add_fx_forward_info(info):
	"""
	[Dictionary] FX Forward information

	If security info already there, raise Error: security info exists

	Otherwise, add the fixed deposit info.
	"""
	pass



def update_fx_forward_info(info):
	"""
	[Dictionary] FX Forward information

	If not found, raise Error: security info not found
	Otherwise, update the fixed deposit info.
	"""
	pass



def get_security_attributes(gid):
	"""
	[String] gid => [Dictonary] security attributes

	If not found, raise Error: security info not found
	"""
	return {}


"""
Geneva Data API
"""
def getGenevaCashLedger(date, portfolio):
	"""
	[String] date (yyyy-mm-dd),
	[String] portfolio id
		=> [List] ([Dictionary] dividend receivable position)
	"""
	return []



def getGenevaPurchaseSales(date, portfolio):
	"""
	[String] date (yyyy-mm-dd),
	[String] portfolio id
		=> [List] ([Dictionary] dividend receivable position)
	"""
	return []

