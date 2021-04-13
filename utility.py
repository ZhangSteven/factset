# coding=utf-8
#
# Load configurations
# 

import configparser


def _loadConfig():
	config = configparser.ConfigParser()
	config.read('factset.config')
	return config



# initialized only once when this module is first imported by others
if not 'config' in globals():
	config = _loadConfig()



def getDataDirectory():
	global config
	return config['Input']['dataDirectory']