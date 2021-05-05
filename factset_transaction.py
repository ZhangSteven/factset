# coding=utf-8
#
# Handles FactSet transaction data upload.
# 
from geneva_data.data import get_geneva_cash_ledger \
							, get_geneva_purchase_sales
from geneva_data.security_data import get_geneva_id_from_description \
							, get_geneva_security_type, get_sedol_code
from geneva_data.utility import first_of, merge_dict
from factset.factset_position import changeDateFormat
from toolz.functoolz import compose
from functools import partial, reduce
from itertools import chain, filterfalse
import logging
logger = logging.getLogger(__name__)



def _factset_dividend_transaction(position):
	"""
	[Dictionary] cash ledger dividend position
		=> [Dictionary] factset dividend transaction
	"""
	invest_id = get_geneva_id_from_description(position['Investment'])
	asset_class, asset_type = _get_asset_class_type(invest_id)

	return \
	{ 'Portfolio Code': position['Portfolio']
	, 'Date': changeDateFormat(position['CashDate'])
	, 'Symbol': _get_security_symbol(invest_id)
	, 'Asset Class': asset_class
	, 'Asset Type': asset_type
	, 'Transaction ID': position['Portfolio'] + '_' + position['TransID']
	, 'Transaction Status': 'ACCT'
	, 'Trade Type': 'IN'
	, 'Price ISO': _get_currency_from_description(position['Currency_ClosingBalDesc'])
	, 'Quantity': ''
	, 'Price': ''
	, 'Gross Transaction Amount': position['LocalAmount']
	, 'Net Transaction Amount': position['LocalAmount']
	, 'Commissions and Fees': 0.0
	, 'Settle Date': changeDateFormat(position['CashDate'])
	, 'Broker': ''
	}



def _factset_return_of_cap_transaction(position):
	"""
	[Dictionary] cash ledger return of cap position
		=> [Dictionary] factset transaction
	"""
	return _factset_dividend_transaction(position)



def _factset_buysell_transaction(position):
	"""
	[Dictionary] purchase sales buy or sell position
		=> [Dictionary] factset buy or sell transaction
	"""
	asset_class, asset_type = _get_asset_class_type(position['InvestID'])

	result = \
	{ 'Portfolio Code': position['Portfolio']
	, 'Date': changeDateFormat(position['TradeDate'])
	, 'Symbol': _get_security_symbol(position['InvestID'])
	, 'Asset Class': asset_class
	, 'Asset Type': asset_type
	, 'Transaction ID': position['Portfolio'] + '_' + position['TranID']
	, 'Transaction Status': 'ACCT'
	, 'Price ISO': position['LocalCurrency']
	, 'Quantity': position['Quantity']
	, 'Price': position['Price']
	, 'Commissions and Fees': position['Commission'] + position['Expenses']
	, 'Settle Date': changeDateFormat(position['SettleDate'])
	, 'Broker': position['Broker']
	}

	if position['TranType'] == 'Buy':
		temp = \
		{ 'Trade Type': 'BL'
		, 'Gross Transaction Amount': abs(position['LocalAmount'])
		, 'Net Transaction Amount': abs(position['LocalAmount']) \
								- position['Commission'] \
								- position['Expenses']
		}
	else:
		temp = \
		{ 'Trade Type': 'SL'
		, 'Gross Transaction Amount': abs(position['LocalAmount']) \
								- position['Commission'] \
								- position['Expenses']
		, 'Net Transaction Amount': abs(position['LocalAmount'])
		}

	return merge_dict(result, temp)



def _factset_spot_fx_transaction(position):
	"""
	[Dictionary] purchase sales spot fx position
		=> [Dictionary] factset spot fx transaction
	"""
	asset_class, asset_type = _get_asset_class_type(position['InvestID'])

	return \
	{ 'Portfolio Code': position['Portfolio']
	, 'Date': changeDateFormat(position['TradeDate'])
	, 'Symbol': 'CASH_ZERO_' + position['InvestID']
	, 'Asset Class': asset_class
	, 'Asset Type': asset_type
	, 'Transaction ID': position['Portfolio'] + '_' + position['TranID']
	, 'Transaction Status': 'ACCT'
	, 'Trade Type': 'BL'
	, 'Price ISO': position['LocalCurrency']
	, 'Quantity': position['Quantity']
	, 'Price': 1.0/position['Price']
	, 'Gross Transaction Amount': position['LocalAmount']
	, 'Net Transaction Amount': position['LocalAmount'] \
								- position['Commission'] \
								- position['Expenses']
	, 'Commissions and Fees': position['Commission'] + position['Expenses']
	, 'Settle Date': changeDateFormat(position['SettleDate'])
	, 'Broker': position['Broker']
	}



def _get_transactions_from_purchase_sales(date, portfolio):
	"""
	[String] date (yyyy-mm-dd), [String] portfolio
		=> [Iterable] ([Dictionary]) factset transactions
	"""
	return compose(
		partial(map, lambda t: t[0](t[1]))
	  , partial( map
	  		   , lambda p: ( _get_purchase_sales_transaction_handler_map()[p['TranType']]
	  		   			   , p
	  		   			   )
	  		   )
	  , get_geneva_purchase_sales
	)(date, portfolio)



def _get_purchase_sales_transaction_handler_map():
	return \
	{ 'SpotFX': _factset_spot_fx_transaction
	, 'Buy': _factset_buysell_transaction
	, 'Sell': _factset_buysell_transaction
	}



def _get_transactions_from_cash_ledger(date, portfolio):
	"""
	[String] date (yyyy-mm-dd), [String] portfolio
		=> [Iterable] ([Dictionary]) factset transactions
	"""
	funcMap = \
		{ 'Dividend': _factset_dividend_transaction
		, 'GrossAmountDividend': _factset_dividend_transaction
		, 'ReturnOfCap': _factset_return_of_cap_transaction
		}

	ignored_types = ('AccountingRelated', )

	return compose(
		partial(map, lambda t: t[0](t[1]))
	  , partial(map, lambda p: (funcMap[p['TranDescription']], p))
	  , partial(filterfalse, lambda p: p['TranDescription'] in ignored_types)
	  , partial( filterfalse
	  		   , lambda p: p['TranDescription'] in \
	  		   				_get_purchase_sales_transaction_handler_map()
	  		   )
	  , get_geneva_cash_ledger
	)(date, portfolio)



def _get_security_symbol(investId):
	"""
	[String] geneva investment id => [String] Factset security symbol
	"""
	asset_type, _ = _get_asset_class_type(investId)
	if asset_type == 'Equity':
		return get_sedol_code(investId)
	else:
		raise ValueError('_get_security_symbol(): not implemented {0}'.format(
						investId))



def _get_asset_class_type(gid):
	"""
	[Dictionary] investment id
		=> ([String] asset class, [String] asset type)
	"""
	_, gType = get_geneva_security_type(gid)
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
		logger.error('_get_asset_class_type(): {0} not supported'.format(
					gType))
		raise ValueError



def _get_currency_from_description(description):
	"""
	[String] currency description => [String] currency code
	"""
	c_map = \
	{ 'chinese renminbi yuan': 'CNY'
	, 'hong kong dollar': 'HKD'
	, 'united states dollar': 'USD'
	}

	key = first_of(lambda k: description.lower().startswith(k), c_map)
	if key != None:
		return c_map[key]
	else:
		raise ValueError('_get_currency_from_description(): not supported {0}'.format(
						description))



def get_transactions(date, portfolio):
	"""
	[String] date (yyyy-mm-dd), [String] portfolio
		=> [List] ([Dictionary]) factset transactions

	Note: portfolio cannot be 'all', must be a portfolio code.
	"""
	logger.debug('get_transactions(): date={0}, portfolio={1}'.format(
				date, portfolio))

	return list(chain( _get_transactions_from_cash_ledger(date, portfolio)
					 , _get_transactions_from_purchase_sales(date, portfolio)))
